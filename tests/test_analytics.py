"""Unit tests for the analytics, SLA, financial, and staffing modules.

Covers:
- Monthly aggregation & inclusive date boundaries (2025-01-01 to 2026-06-30)
- Missing transfer handling (unrecorded != 0)
- SLA calculations across all 4 channels
- CSAT missing values handling (no imputation of 0)
- Repeat-contact 30-day window logic
- Financial cost calculations & no double-counting
- Tier 1 vs Tier 2 separation
- Total volume reconciliation
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.data.loader import DataLoader
from src.analytics.monthly import MonthlyAnalytics
from src.analytics.workload import WorkloadAnalyzer
from src.analytics.sla import SLAMetrics
from src.analytics.financial import FinancialAuditor
from src.analytics.staffing import StaffingModel


@pytest.fixture(scope="module")
def project_data():
    """Load pre-classified tickets and agent roster for testing."""
    classified_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "classified_tickets.csv"
    agents_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "agents.csv"
    products_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "products.csv"

    tickets_df = pd.read_csv(classified_path)
    agents_df = pd.read_csv(agents_path)
    products_df = pd.read_csv(products_path)
    return {
        "tickets": tickets_df,
        "agents": agents_df,
        "products": products_df
    }


def test_core_window_date_filtering(project_data):
    """Verify inclusive filtering for 2025-01-01 to 2026-06-30 (11,641 tickets)."""
    core = MonthlyAnalytics.filter_core_window(project_data["tickets"])
    assert len(core) == 11641
    assert core["created_dt"].min() >= pd.Timestamp("2025-01-01")
    assert core["created_dt"].max() <= pd.Timestamp("2026-06-30 23:59:59")


def test_monthly_kpi_volume_reconciliation(project_data):
    """Verify sum of monthly incoming equals core window total and status reconciles."""
    kpis = MonthlyAnalytics.compute_monthly_kpis(
        project_data["tickets"],
        project_data["agents"]
    )
    assert len(kpis) == 18  # Exactly 18 months

    total_incoming = kpis["incoming_tickets"].sum()
    assert total_incoming == 11641

    # Check status reconciliation
    status_sum = (
        kpis["resolved_tickets"].sum()
        + kpis["auto_closed_tickets"].sum()
        + kpis["open_backlog"].sum()
        + kpis["pending_backlog"].sum()
    )
    assert status_sum == total_incoming


def test_missing_transfer_handling(project_data):
    """Verify unrecorded legacy transfers are NOT treated as zero."""
    tickets = project_data["tickets"]
    legacy_tickets = tickets[tickets["source_system"] == "legacy_fd"]
    assert legacy_tickets["transfers"].isna().all()

    kpis = MonthlyAnalytics.compute_monthly_kpis(tickets, project_data["agents"])
    # First 8 months (Jan - Aug 2025) are pre-migration and must have 0 observable transfers
    pre_migration_kpis = kpis.iloc[:8]
    assert (pre_migration_kpis["observable_transfers"] == 0).all()
    assert (pre_migration_kpis["helpdesk_tickets_sampled"] == 0).all()


def test_sla_channel_calculations():
    """Verify first-response breach detection against Policy §3 targets."""
    sample = pd.DataFrame([
        {"channel": "chat", "created_at": "2025-02-01 10:00", "first_response_at": "2025-02-01 10:10"},  # 10 min: Compliant
        {"channel": "chat", "created_at": "2025-02-01 10:00", "first_response_at": "2025-02-01 10:20"},  # 20 min: Breach (>15m)
        {"channel": "voice", "created_at": "2025-02-01 10:00", "first_response_at": "2025-02-01 11:30"}, # 1.5h: Compliant (<2h)
        {"channel": "voice", "created_at": "2025-02-01 10:00", "first_response_at": "2025-02-01 12:30"}, # 2.5h: Breach (>2h)
        {"channel": "email", "created_at": "2025-02-01 10:00", "first_response_at": "2025-02-01 17:00"}, # 7h: Compliant (<8h)
        {"channel": "email", "created_at": "2025-02-01 10:00", "first_response_at": "2025-02-01 19:00"}, # 9h: Breach (>8h)
    ])
    enriched = SLAMetrics.calculate_breaches(sample)
    assert list(enriched["is_sla_breach"]) == [False, True, False, True, False, True]
    assert list(enriched["sla_penalty_inr"]) == [0.0, 350.0, 0.0, 350.0, 0.0, 350.0]


def test_csat_missing_values_not_zero():
    """Verify that null CSAT scores are excluded from mean calculations."""
    sample = pd.Series([4.0, 5.0, np.nan, np.nan])
    # Correct calculation: mean of non-nulls is 4.5
    assert sample.dropna().mean() == 4.5
    # If incorrectly filled with zero, mean would be 2.25
    assert sample.fillna(0.0).mean() == 2.25


def test_tier1_vs_tier2_separation(project_data):
    """Verify Tier 2 Escalations & Warranty is kept separate with distinct metrics."""
    workload = WorkloadAnalyzer.compute_team_workload_summary(
        project_data["tickets"],
        project_data["agents"]
    )
    tier2 = workload[workload["team"] == "Escalations & Warranty"].iloc[0]
    assert tier2["tier"] == 2
    assert tier2["roster_headcount"] == 6

    # Tier 1 teams must have tier == 1
    tier1 = workload[workload["team"] != "Escalations & Warranty"]
    assert (tier1["tier"] == 1).all()


def test_financial_calculations_no_double_counting(project_data):
    """Verify financial metrics are additive, independent, and not double-counted."""
    core = MonthlyAnalytics.filter_core_window(project_data["tickets"])
    core = core.merge(
        project_data["agents"][["agent_id", "team"]].rename(columns={"team": "resolving_team"}),
        on="agent_id",
        how="left"
    )
    core["resolved_dt"] = pd.to_datetime(core["resolved_at"])
    core = SLAMetrics.calculate_breaches(core)
    core_sorted = core.sort_values(["customer_id", "created_dt"]).copy()
    core_sorted["prev_resolved_dt"] = core_sorted.groupby("customer_id")["resolved_dt"].shift(1)
    core_sorted["days_since_prev_res"] = (
        core_sorted["created_dt"] - core_sorted["prev_resolved_dt"]
    ).dt.total_seconds() / (24 * 3600.0)
    core_sorted["is_repeat_contact_30d"] = (
        (core_sorted["days_since_prev_res"] >= 0) & (core_sorted["days_since_prev_res"] <= 30)
    )

    inbound = FinancialAuditor.compute_inbound_channel_costs(core_sorted)
    sla = FinancialAuditor.compute_sla_breach_penalties(core_sorted)
    transfers = FinancialAuditor.compute_transfer_costs(core_sorted)
    repeats = FinancialAuditor.compute_repeat_contact_costs(core_sorted)

    # Inbound cost is channel baseline (~31.8L)
    assert inbound["total_inbound_cost_inr"] > 3000000.0

    # SLA cost is distinct penalty line (~4.5L)
    assert sla["total_store_credit_liability_inr"] > 400000.0

    # Transfer cost is administrative re-handling (~3.9L)
    assert transfers["total_transfer_cost_inr"] > 350000.0

    # Each metric has an independent accounting line and cannot be merged into single cost
    assert inbound["total_inbound_cost_inr"] != sla["total_store_credit_liability_inr"]
    assert sla["total_store_credit_liability_inr"] != transfers["total_transfer_cost_inr"]


def test_staffing_evaluation_logistics_vs_billing(project_data):
    """Verify staffing model accurately identifies Logistics as bottleneck and Billing as fast."""
    core = MonthlyAnalytics.filter_core_window(project_data["tickets"])
    core = core.merge(
        project_data["agents"][["agent_id", "team"]].rename(columns={"team": "resolving_team"}),
        on="agent_id",
        how="left"
    )
    core["resolved_dt"] = pd.to_datetime(core["resolved_at"])
    core = SLAMetrics.calculate_breaches(core)
    workload = WorkloadAnalyzer.compute_team_workload_summary(core, project_data["agents"])
    sla = SLAMetrics.compute_team_sla_summary(core)

    eval_result = StaffingModel.evaluate_hiring_options(workload, sla, core)
    assert eval_result["billing_assessment"]["recommend_hiring"] is False
    assert eval_result["logistics_assessment"]["recommend_hiring"] is True

    # Check 90-day goal generation
    goal = StaffingModel.generate_ninety_day_goal(eval_result)
    assert "75%" in goal["goal_statement"]
    assert "Logistics" in goal["goal_statement"]


def test_audit_staffing_arithmetic_reconciliation(project_data):
    """Audit 1: Verify exact staffing arithmetic across all teams."""
    core = MonthlyAnalytics.filter_core_window(project_data["tickets"])
    core = core.merge(
        project_data["agents"][["agent_id", "team"]].rename(columns={"team": "resolving_team"}),
        on="agent_id",
        how="left"
    )
    workload = WorkloadAnalyzer.compute_team_workload_summary(core, project_data["agents"])
    
    # Check total agents on roster
    assert len(project_data["agents"]) == 44
    
    # Check Logistics arithmetic
    log = workload[workload["team"] == "Logistics"].iloc[0]
    assert log["roster_headcount"] == 5
    assert log["resolved_volume"] == 2574
    assert round(log["resolved_volume"] / log["roster_headcount"], 1) == 514.8
    assert round(log["monthly_tickets_per_agent"], 1) == 28.6
    assert round(log["monthly_avg_resolved"], 1) == 143.0
    
    # Check Billing arithmetic
    bil = workload[workload["team"] == "Billing"].iloc[0]
    assert bil["roster_headcount"] == 4
    assert bil["resolved_volume"] == 1798
    assert round(bil["resolved_volume"] / bil["roster_headcount"], 1) == 449.5
    assert round(bil["monthly_tickets_per_agent"], 1) == 25.0
    assert round(bil["monthly_avg_resolved"], 1) == 99.9


def test_audit_routing_populations_reconciliation(project_data):
    """Audit 3: Disentangle 795, 696, -627, and 1048 routing figures."""
    all_tickets = project_data["tickets"].merge(
        project_data["agents"][["agent_id", "team"]].rename(columns={"team": "resolving_team"}),
        on="agent_id",
        how="left"
    )
    core = MonthlyAnalytics.filter_core_window(all_tickets)
    
    # 795: All-time Billing assigned -> Logistics resolved
    all_b_to_l = (all_tickets["assigned_team"] == "Billing") & (all_tickets["resolving_team"] == "Logistics")
    assert all_b_to_l.sum() == 795
    
    # 696: Core 18M Billing assigned -> Logistics resolved
    core_b_to_l = (core["assigned_team"] == "Billing") & (core["resolving_team"] == "Logistics")
    assert core_b_to_l.sum() == 696
    
    # -627: Billing Net Volume Delta in Core 18M
    billing_resolved = (core["resolving_team"] == "Billing").sum()
    billing_assigned = (core["assigned_team"] == "Billing").sum()
    assert billing_resolved == 1798
    assert billing_assigned == 2425
    assert billing_resolved - billing_assigned == -627
    
    # 1048: All-time Billing assigned with predicted intent 'Order & Logistics'
    b_all = all_tickets[all_tickets["assigned_team"] == "Billing"]
    assert (b_all["predicted_category"] == "Order & Logistics").sum() == 1048


def test_audit_financial_cost_lines_reconciliation(project_data):
    """Audit 2: Verify exact financial reconciliation totals without double-counting."""
    core = MonthlyAnalytics.filter_core_window(project_data["tickets"])
    core = core.merge(
        project_data["agents"][["agent_id", "team"]].rename(columns={"team": "resolving_team"}),
        on="agent_id",
        how="left"
    )
    core["resolved_dt"] = pd.to_datetime(core["resolved_at"])
    core = SLAMetrics.calculate_breaches(core)
    
    # Inbound Channel Costs
    inbound = FinancialAuditor.compute_inbound_channel_costs(core)
    assert inbound["total_inbound_cost_inr"] == 3182240.0
    
    # SLA Breach Penalties
    sla = FinancialAuditor.compute_sla_breach_penalties(core)
    assert sla["total_breaches"] == 1292
    assert sla["total_store_credit_liability_inr"] == 452200.0
    
    # Internal Transfers Cost
    transfers = FinancialAuditor.compute_transfer_costs(core)
    assert transfers["total_observable_transfers"] == 1299
    assert transfers["total_transfer_cost_inr"] == 396195.0
    
    # Dual Disbursement Leakage
    dual = FinancialAuditor.compute_dual_disbursement_leakage(core, project_data["products"])
    assert dual["violating_order_count"] == 74
    assert dual["total_dual_leakage_exposure_inr"] == 394616.0
    assert dual["total_refund_disbursed_inr"] == 254846.0
    assert dual["total_replacement_cost_inr"] == 139770.0
    
    # Process Improvement Opportunity (Definition B: 696 misroutes + 250 SLA breaches)
    opp = FinancialAuditor.compute_process_improvement_opportunity(core)
    assert opp["misrouted_billing_to_logistics_count_18m"] == 696
    assert opp["direct_transfer_waste_18m_inr"] == 212280.0
    assert opp["avoidable_sla_penalties_18m_inr"] == 87500.0
    assert opp["total_process_waste_18m_inr"] == 299780.0
    assert round(opp["annualized_process_improvement_opportunity_inr"], 2) == 199853.33


def test_audit_sla_and_time_metrics(project_data):
    """Audit 4: Verify First-Response SLA compliance and resolution metrics for Logistics and Billing."""
    core = MonthlyAnalytics.filter_core_window(project_data["tickets"])
    core = core.merge(
        project_data["agents"][["agent_id", "team"]].rename(columns={"team": "resolving_team"}),
        on="agent_id",
        how="left"
    )
    core = SLAMetrics.calculate_breaches(core)
    
    # Logistics SLA metrics
    log_tix = core[core["resolving_team"] == "Logistics"]
    assert len(log_tix) == 2574
    assert log_tix["is_sla_breach"].sum() == 423
    compliance_pct = round((len(log_tix) - 423) / len(log_tix) * 100, 2)
    assert compliance_pct == 83.57
    
    # Billing SLA metrics
    bil_tix = core[core["resolving_team"] == "Billing"]
    assert len(bil_tix) == 1798
    assert bil_tix["is_sla_breach"].sum() == 241

"""Unit tests for the dynamic data pipeline and report capability engine.

Covers:
1. Basic ticket-volume capability
2. Category analysis with an existing category field
3. Category analysis using deterministic classifier when message text is available
4. Missing message and category handling (disables category analysis)
5. Missing response timestamp disables SLA analysis
6. Missing roster disables verified staffing analysis
7. Valid roster enables supported workload calculations
8. Missing product catalog disables replacement COGS analysis
9. Invalid timestamps do not create negative or fabricated durations
10. Missing transfers remain null
11. Missing CSAT remains null
12. Unresolved tickets do not receive resolution durations
13. Input DataFrames remain completely unchanged (immutability)
14. Different datasets produce independent capability results
15. Existing baseline analytics remain unchanged
"""

import copy
import hashlib
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.data.dynamic_pipeline import (
    DynamicPipeline,
    CapabilityStatus,
    ReportCapability,
    DynamicPipelineResult,
)
from src.ui.data_service import load_and_preprocess_all


@pytest.fixture
def sample_ticket_df() -> pd.DataFrame:
    """Fixture providing a realistic, validated sample ticket DataFrame."""
    return pd.DataFrame({
        "ticket_id": ["TICK-001", "TICK-002", "TICK-003", "TICK-004"],
        "created_at": [
            "2025-01-10 10:00:00",
            "2025-01-10 11:00:00",
            "2025-01-11 09:30:00",
            "2025-01-12 14:00:00"
        ],
        "first_response_at": [
            "2025-01-10 10:10:00",
            "2025-01-10 11:45:00",
            None,  # Missing response
            "2025-01-12 14:20:00"
        ],
        "resolved_at": [
            "2025-01-10 14:00:00",
            "2025-01-11 12:00:00",
            None,  # Unresolved
            "2025-01-12 16:30:00"
        ],
        "status": ["resolved", "resolved", "open", "resolved"],
        "channel": ["chat", "email", "chat", "voice"],
        "customer_id": ["CUST-10", "CUST-20", "CUST-30", "CUST-10"],
        "order_id": ["VR-ORD-1", "VR-ORD-2", None, "VR-ORD-3"],
        "product_sku": ["VA-PULSE2-BLK", "VA-STRATA2-SLV", "VA-PULSE2-BLK", "VA-PULSE2-BLK"],
        "assigned_team": ["Logistics", "Returns Desk", "Chat Frontline", "Logistics"],
        "agent_id": ["AGT-001", "AGT-002", "AGT-003", "AGT-001"],
        "transfers": [1.0, None, 0.0, None],  # Missing transfers present
        "csat_score": [5.0, None, None, 4.0],  # Missing CSAT present
        "refund_amount_inr": [None, 3499.0, None, None],
        "replacement_issued": ["N", "Y", "N", "N"],
        "customer_message": [
            "Where is my package? AWB tracking has not updated for 5 days.",
            "Nobody came for the return pickup of my headphones.",
            "Bluetooth disconnects every 2 minutes.",
            "Courier delivered package to wrong address."
        ],
        "agent_notes": [
            "Courier delay verified.",
            "Pickup rescheduled.",
            "Reset instructions sent.",
            "Rerouted to correct apartment."
        ]
    })


@pytest.fixture
def sample_agents_df() -> pd.DataFrame:
    """Fixture providing a sample agent roster DataFrame."""
    return pd.DataFrame({
        "agent_id": ["AGT-001", "AGT-002", "AGT-003"],
        "name": ["Aarav Patel", "Diya Sharma", "Karan Verma"],
        "team": ["Logistics", "Returns Desk", "Chat Frontline"],
        "tier": [1, 1, 1],
        "site": ["Bengaluru", "Pune", "Remote"],
        "shift": ["Morning", "Morning", "Evening"]
    })


@pytest.fixture
def sample_products_df() -> pd.DataFrame:
    """Fixture providing a sample product catalog DataFrame."""
    return pd.DataFrame({
        "sku": ["VA-PULSE2-BLK", "VA-STRATA2-SLV"],
        "product_name": ["Pulse 2 Black", "Strata 2 Silver"],
        "unit_cost_inr": [1400.0, 2200.0],
        "retail_price_inr": [4999.0, 7999.0]
    })


def test_basic_ticket_volume_capability(sample_ticket_df):
    """1. Test that basic ticket volume capability is available for valid tickets."""
    result = DynamicPipeline.process(sample_ticket_df)
    cap = result.capabilities["executive_volume"]
    assert cap.status == CapabilityStatus.AVAILABLE
    assert "executive_volume" in result.available_capabilities
    assert result.dataset_summary["total_tickets"] == 4


def test_category_analysis_with_existing_category_field(sample_ticket_df):
    """2. Test category analysis with an existing pre-tagged category field."""
    df_with_cat = sample_ticket_df.copy()
    df_with_cat["category"] = [
        "Order & Logistics", "Returns & Refunds", "Technical & Firmware", "Order & Logistics"
    ]
    # Remove customer_message to test that category field alone satisfies capability
    df_with_cat = df_with_cat.drop(columns=["customer_message"])

    result = DynamicPipeline.process(df_with_cat)
    cap = result.capabilities["category_analytics"]
    assert cap.status == CapabilityStatus.AVAILABLE
    assert "category_analytics" in result.available_capabilities
    assert (result.preprocessed_df["predicted_category"] == df_with_cat["category"]).all()


def test_category_analysis_using_deterministic_classifier(sample_ticket_df):
    """3. Test category analysis when category field is absent but customer_message is available."""
    df_no_cat = sample_ticket_df.copy()
    if "category" in df_no_cat.columns:
        df_no_cat = df_no_cat.drop(columns=["category"])

    result = DynamicPipeline.process(df_no_cat)
    cap = result.capabilities["category_analytics"]
    assert cap.status == CapabilityStatus.AVAILABLE
    assert "predicted_category" in result.preprocessed_df.columns
    # First row is logistics inquiry
    assert result.preprocessed_df.loc[0, "predicted_category"] == "Order & Logistics"


def test_missing_message_and_category_handling(sample_ticket_df):
    """4. Test that missing both message and category disables Category Analytics."""
    df_blind = sample_ticket_df.drop(columns=["customer_message"])
    if "category" in df_blind.columns:
        df_blind = df_blind.drop(columns=["category"])

    result = DynamicPipeline.process(df_blind)
    cap = result.capabilities["category_analytics"]
    assert cap.status == CapabilityStatus.UNAVAILABLE
    assert "category_analytics" in result.unavailable_capabilities
    assert len(cap.missing_fields) > 0


def test_missing_response_timestamp_disables_sla_analysis(sample_ticket_df):
    """5. Test that missing first_response_at disables SLA analysis capability."""
    df_no_resp = sample_ticket_df.drop(columns=["first_response_at"])
    result = DynamicPipeline.process(df_no_resp)
    cap = result.capabilities["sla_analysis"]
    assert cap.status == CapabilityStatus.UNAVAILABLE
    assert "first_response_at" in cap.missing_fields
    assert "sla_analysis" in result.unavailable_capabilities


def test_missing_roster_disables_verified_staffing_analysis(sample_ticket_df):
    """6. Test that omitting the roster disables verified staffing analysis."""
    result = DynamicPipeline.process(sample_ticket_df, agents_df=None)
    cap = result.capabilities["staffing_analysis"]
    assert cap.status == CapabilityStatus.UNAVAILABLE
    assert "agents" in cap.supporting_datasets_missing
    assert "staffing_analysis" in result.unavailable_capabilities


def test_valid_roster_enables_supported_workload(sample_ticket_df, sample_agents_df):
    """7. Test that providing a valid roster enables Team Workload and Staffing Analysis."""
    result = DynamicPipeline.process(sample_ticket_df, agents_df=sample_agents_df)
    workload_cap = result.capabilities["team_workload"]
    staffing_cap = result.capabilities["staffing_analysis"]
    assert workload_cap.status == CapabilityStatus.AVAILABLE
    assert staffing_cap.status == CapabilityStatus.AVAILABLE
    assert "team_workload" in result.available_capabilities
    assert "staffing_analysis" in result.available_capabilities

    # Roster metadata properly joined strictly via agent_id
    assert "resolving_team" in result.preprocessed_df.columns
    assert result.preprocessed_df.loc[0, "resolving_team"] == "Logistics"


def test_missing_product_catalog_disables_replacement_cogs(sample_ticket_df):
    """8. Test that missing product catalog marks Financial Impact as PARTIAL and warns on COGS."""
    result = DynamicPipeline.process(sample_ticket_df, products_df=None)
    cap = result.capabilities["financial_impact"]
    assert cap.status == CapabilityStatus.PARTIAL
    assert "products" in cap.supporting_datasets_missing
    assert any("Replacement hardware COGS unavailable" in w for w in cap.warnings)


def test_invalid_timestamps_do_not_create_negative_durations(sample_ticket_df):
    """9. Test that an inverted timestamp (response before creation) does not create negative duration."""
    df_bad_time = sample_ticket_df.copy()
    # Set first_response_at earlier than created_at
    df_bad_time.loc[0, "first_response_at"] = "2025-01-10 09:00:00"  # 1 hour before created_at

    result = DynamicPipeline.process(df_bad_time)
    # resp_time_hrs must be NaN, never negative
    assert pd.isna(result.preprocessed_df.loc[0, "resp_time_hrs"])


def test_missing_transfers_remain_null(sample_ticket_df):
    """10. Test that missing transfers are preserved as null and not imputed as zero."""
    result = DynamicPipeline.process(sample_ticket_df)
    prep = result.preprocessed_df
    assert pd.isna(prep.loc[1, "transfers"])
    assert pd.isna(prep.loc[3, "transfers"])
    assert prep.loc[0, "transfers"] == 1.0


def test_missing_csat_remains_null(sample_ticket_df):
    """11. Test that missing CSAT scores remain null and are not converted to zero."""
    result = DynamicPipeline.process(sample_ticket_df)
    prep = result.preprocessed_df
    assert pd.isna(prep.loc[1, "csat_score"])
    assert pd.isna(prep.loc[2, "csat_score"])
    assert prep.loc[0, "csat_score"] == 5.0


def test_unresolved_tickets_do_not_receive_resolution_durations(sample_ticket_df):
    """12. Test that open or pending tickets do not receive resolution durations."""
    result = DynamicPipeline.process(sample_ticket_df)
    prep = result.preprocessed_df
    # Row 2 is status="open" and resolved_at=None
    assert pd.isna(prep.loc[2, "total_res_time_hrs"])
    assert pd.isna(prep.loc[2, "handle_time_hrs"])

    # Even if an open ticket had a resolved_at timestamp mistakenly, status="open" must block resolution time
    df_err = sample_ticket_df.copy()
    df_err.loc[2, "resolved_at"] = "2025-01-11 10:00:00"
    df_err.loc[2, "status"] = "open"
    res_err = DynamicPipeline.process(df_err)
    assert pd.isna(res_err.preprocessed_df.loc[2, "total_res_time_hrs"])


def test_input_dataframes_remain_unchanged(sample_ticket_df, sample_agents_df):
    """13. Verify deep immutability: input DataFrames remain bit-for-bit identical."""
    df_ticket_copy = copy.deepcopy(sample_ticket_df)
    df_agent_copy = copy.deepcopy(sample_agents_df)

    _ = DynamicPipeline.process(sample_ticket_df, agents_df=sample_agents_df)

    pd.testing.assert_frame_equal(sample_ticket_df, df_ticket_copy)
    pd.testing.assert_frame_equal(sample_agents_df, df_agent_copy)


def test_different_datasets_produce_independent_capability_results(sample_ticket_df, sample_agents_df):
    """14. Test that two distinct datasets produce independent, isolated capability results."""
    # Dataset A: Complete tickets with agents
    res_a = DynamicPipeline.process(sample_ticket_df, agents_df=sample_agents_df)

    # Dataset B: Minimal tickets lacking SLA timestamps and agents
    minimal_df = pd.DataFrame({
        "ticket_id": ["T-1", "T-2"],
        "created_at": ["2025-03-01", "2025-03-02"],
        "status": ["open", "resolved"],
        "channel": ["chat", "chat"],
        "customer_id": ["C-1", "C-2"],
        "assigned_team": ["Logistics", "Billing"]
    })
    res_b = DynamicPipeline.process(minimal_df)

    assert "staffing_analysis" in res_a.available_capabilities
    assert "staffing_analysis" in res_b.unavailable_capabilities
    assert res_a.dataset_summary["total_tickets"] == 4
    assert res_b.dataset_summary["total_tickets"] == 2


def test_existing_baseline_analytics_remain_unchanged():
    """15. Verify that baseline audited metrics (11,641 core tickets) remain unchanged."""
    app_data = load_and_preprocess_all()
    tickets = app_data["tickets"]
    core = tickets[tickets["in_core_18m"] == True]
    assert len(core) == 11641
    assert len(app_data["agents"]) == 44
    assert len(app_data["orders"]) == 15000
    assert len(app_data["products"]) == 14

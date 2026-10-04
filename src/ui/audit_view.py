"""Audit Reconciliation view for Streamlit dashboard.

Displays the complete forensic reconciliation table from Step 3.1,
providing transparency on verified metrics, corrected calculations, proxies, and data gaps.
"""

import streamlit as st
import pandas as pd


def render_audit_reconciliation():
    """Render Master Audit Reconciliation tab content."""
    st.header("🔍 Master Metric Reconciliation & Data Integrity Audit")
    st.markdown(
        "Complete audit trail independently recomputed and verified across Steps 1 through 3.1. "
        "Ensures 100% mathematical rigor before presenting recommendations to Priya Raman and Arjun Mehta."
    )

    st.info(
        "**Audit Status Legend:**\n"
        "• **Verified:** Exact match to source records and business logic.\n"
        "• **Corrected:** Recomputed and adjusted for temporal scope, population definition, or sub-component split.\n"
        "• **Proxy:** Operational proxy used where policy standards require heuristic text matching.\n"
        "• **Unverified:** Data unavailable in source files (e.g., absence of shift attendance timecards)."
    )

    reconciliation_records = [
        {"Metric Identifier": "Core Period Volume", "Previously Reported": "11,641 tickets", "Recomputed Audit": "11,641 tickets", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "Exact 1 Jan 2025 – 30 Jun 2026 inclusive window."},
        {"Metric Identifier": "Total Dataset Volume", "Previously Reported": "11,780 tickets", "Recomputed Audit": "11,780 tickets", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "Includes 139 tickets from 2024 pilot pre-period."},
        {"Metric Identifier": "Total Agent Roster", "Previously Reported": "44 agents", "Recomputed Audit": "44 agents", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "Static snapshot roster; all 44 observed active in core period."},
        {"Metric Identifier": "Logistics Headcount", "Previously Reported": "5 agents", "Recomputed Audit": "5 agents", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "All 5 agents based at Bengaluru site."},
        {"Metric Identifier": "Billing Headcount", "Previously Reported": "4 agents", "Recomputed Audit": "4 agents", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "2 Bengaluru, 2 Indore."},
        {"Metric Identifier": "Logistics Resolved Vol.", "Previously Reported": "2,574 tickets", "Recomputed Audit": "2,574 tickets", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "Core 18M resolving volume (143.0 tickets/mo)."},
        {"Metric Identifier": "Billing Resolved Vol.", "Previously Reported": "1,798 tickets", "Recomputed Audit": "1,798 tickets", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "Core 18M resolving volume (99.9 tickets/mo)."},
        {"Metric Identifier": "Logistics Monthly Tix/Ag", "Previously Reported": "28.6 tix/agent/mo", "Recomputed Audit": "28.6 tix/agent/mo", "Status": "Verified", "Classification": "Roster Avg", "Reconciliation Explanation": "2,574 / 5 / 18 = 28.60 tix/agent/month (highest in company)."},
        {"Metric Identifier": "Billing Monthly Tix/Ag", "Previously Reported": "25.0 tix/agent/mo", "Recomputed Audit": "25.0 tix/agent/mo", "Status": "Verified", "Classification": "Roster Avg", "Reconciliation Explanation": "1,798 / 4 / 18 = 24.97 tix/agent/month."},
        {"Metric Identifier": "Escalations Tix/Ag", "Previously Reported": "6.0 tix/agent/mo", "Recomputed Audit": "6.0 tix/agent/mo", "Status": "Verified", "Classification": "Roster Avg", "Reconciliation Explanation": "Tier 2 certified RMA queue; not comparable to Tier 1 queues."},
        {"Metric Identifier": "Billing Net Volume Delta", "Previously Reported": "-627 tickets", "Recomputed Audit": "-627 tickets", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "1,798 resolved − 2,425 assigned = -627 net delta."},
        {"Metric Identifier": "Core Billing → Logistics", "Previously Reported": "627 / 795 (conflicted)", "Recomputed Audit": "696 tickets", "Status": "Corrected", "Classification": "Observed", "Reconciliation Explanation": "696 gross misrouted tickets in core 18M (627 was net delta; 795 was all-time)."},
        {"Metric Identifier": "All-Time Billing → Log.", "Previously Reported": "795 tickets", "Recomputed Audit": "795 tickets", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "696 core + 99 pilot = 795 all-time gross hand-offs."},
        {"Metric Identifier": "AI Intent Mismatch (Bill)", "Previously Reported": "1,048 tickets", "Recomputed Audit": "1,048 (All) / 919 (18M)", "Status": "Verified", "Classification": "Model Output", "Reconciliation Explanation": "Intake bot tagged Billing, but AI intent is Order & Logistics."},
        {"Metric Identifier": "Inbound Handling Cost", "Previously Reported": "₹31,82,240", "Recomputed Audit": "₹31,82,240.00", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "Exact sum of Policy §4 channel rates across 11,641 tix."},
        {"Metric Identifier": "SLA Credit Liability", "Previously Reported": "₹4,52,200", "Recomputed Audit": "₹4,52,200.00", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "1,292 breaches × ₹350 store credit per Policy §3."},
        {"Metric Identifier": "Observable Transfers", "Previously Reported": "1,299 transfers", "Recomputed Audit": "1,299 transfers", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "Sum of transfers across 7,728 post-migration tickets."},
        {"Metric Identifier": "Transfer Handling Cost", "Previously Reported": "₹3,96,195", "Recomputed Audit": "₹3,96,195.00", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "1,299 transfers × ₹305 re-handling fee per Policy §4."},
        {"Metric Identifier": "Repeat Contact Volume", "Previously Reported": "3,079 tickets", "Recomputed Audit": "3,079 tickets", "Status": "Proxy", "Classification": "Estimated", "Reconciliation Explanation": "Customer-level 30-day window proxy (26.45% of volume)."},
        {"Metric Identifier": "Repeat Contact Cost", "Previously Reported": "₹8,44,250", "Recomputed Audit": "₹8,44,250.00", "Status": "Proxy", "Classification": "Estimated", "Reconciliation Explanation": "Channel handling cost of 3,079 proxy repeat contacts."},
        {"Metric Identifier": "Dual Disbursement Orders", "Previously Reported": "74 orders", "Recomputed Audit": "74 orders", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "Orders receiving both refund and replacement."},
        {"Metric Identifier": "Dual Disbursement Total", "Previously Reported": "₹3,94,616", "Recomputed Audit": "₹3,94,616.00", "Status": "Verified", "Classification": "Exposure", "Reconciliation Explanation": "Unmonitored compliance leakage; zero salvage value credited."},
        {"Metric Identifier": "Dual Disb. Refund Sub-part", "Previously Reported": "₹2,60,456", "Recomputed Audit": "₹2,54,846.00", "Status": "Corrected", "Classification": "Observed", "Reconciliation Explanation": "Exact refund sum disbursed across the 74 violating orders."},
        {"Metric Identifier": "Dual Disb. Repl. Sub-part", "Previously Reported": "₹1,34,160", "Recomputed Audit": "₹139,770.00", "Status": "Corrected", "Classification": "Observed", "Reconciliation Explanation": "Exact replacement unit manufacturing + ₹340 logistics."},
        {"Metric Identifier": "Annual Two-Hire Budget", "Previously Reported": "₹9,00,000", "Recomputed Audit": "₹9,00,000.00", "Status": "Verified", "Classification": "Parameter", "Reconciliation Explanation": "2 hires × ₹4.5 Lakh fully loaded salary benchmark."},
        {"Metric Identifier": "Process Improvement ROI", "Previously Reported": "₹1.47L / ₹2.09L / ₹2.5L", "Recomputed Audit": "₹1,99,853.33/yr", "Status": "Corrected", "Classification": "Hypothetical", "Reconciliation Explanation": "(696 xfers × ₹305 + 250 SLA × ₹350) / 1.5 = ₹1,99,853/yr (~₹2.00L)."},
        {"Metric Identifier": "Logistics SLA Compliance", "Previously Reported": "83.6%", "Recomputed Audit": "83.57%", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "2,151 compliant / 2,574 resolved tickets."},
        {"Metric Identifier": "Logistics Median Res Time", "Previously Reported": "26.03 hours", "Recomputed Audit": "26.03 hours", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "Total duration from created_at to resolved_at."},
        {"Metric Identifier": "Logistics Median Hdl Time", "Previously Reported": "24.47 hours", "Recomputed Audit": "24.47 hours", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "Duration from first_response_at to resolved_at."},
        {"Metric Identifier": "Billing Median Res Time", "Previously Reported": "1.22 hours", "Recomputed Audit": "1.22 hours", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "73 minutes from created_at to resolved_at."},
        {"Metric Identifier": "Billing Median Hdl Time", "Previously Reported": "0.38 hours (23m)", "Recomputed Audit": "0.38 hours (23m)", "Status": "Verified", "Classification": "Observed", "Reconciliation Explanation": "Active agent touch time is only 23 minutes."},
        {"Metric Identifier": "Legacy Negative Durations", "Previously Reported": "0 remaining", "Recomputed Audit": "0 remaining", "Status": "Verified", "Classification": "Corrected", "Reconciliation Explanation": "+05:30 offset successfully resolved 2,575 anomalies."},
        {"Metric Identifier": "Agent Shift/Leave Records", "Previously Reported": "Not reported", "Recomputed Audit": "Unavailable", "Status": "Unverified", "Classification": "Data Gap", "Reconciliation Explanation": "Roster lacks active timecards; metrics use roster average."}
    ]

    rec_df = pd.DataFrame(reconciliation_records)
    st.dataframe(
        rec_df,
        column_config={
            "Metric Identifier": st.column_config.TextColumn("Metric", width="medium"),
            "Previously Reported": "Previous Value",
            "Recomputed Audit": "Audit Recomputed Value",
            "Status": st.column_config.TextColumn("Audit Status", width="small"),
            "Classification": "Nature",
            "Reconciliation Explanation": st.column_config.TextColumn("Forensic Root Cause & Scope", width="large")
        },
        use_container_width=True,
        hide_index=True
    )

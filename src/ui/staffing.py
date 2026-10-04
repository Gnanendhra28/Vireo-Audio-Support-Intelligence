"""Staffing Decision View for Streamlit dashboard.

Presents evidence-based comparative analysis answering Priya Raman's core question:
Should Vireo allocate two hires to Billing, Logistics, or can process improvements eliminate hiring?
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from src.ui.data_service import format_inr, format_lakh


def render_staffing_decision(
    filtered_df: pd.DataFrame,
    agents_df: pd.DataFrame,
    is_filtered: bool
):
    """Render Staffing Decision tab content."""
    st.header("⚖️ Staffing Allocation Decision Engine")
    st.markdown(
        "Executive evaluation framework resolving the **₹9.00 Lakh Headcount Investment** deadlock "
        "between Priya Raman (Head of CX), Arjun Mehta (Finance Controller), and Neha Kulkarni (Support Operations)."
    )

    # 1. Executive Stakeholder Perspectives
    st.subheader("🎯 The Executive Conflict")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.error("**Priya Raman (Head of CX)**")
        st.caption(
            "• Requesting **2 additional hires for Billing**.\n"
            "• Based on large incoming intake queue (2,425 tickets).\n"
            "• Believes Billing agents are overwhelmed by payment complaints."
        )
    with p2:
        st.warning("**Arjun Mehta (Finance Controller)**")
        st.caption(
            "• Strongly opposes expanding headcount.\n"
            "• Two hires cost **₹9,00,000 annually**.\n"
            "• Argues that process fixes and automation should eliminate the need for hiring."
        )
    with p3:
        st.info("**Neha Kulkarni (Support Operations)**")
        st.caption(
            "• Observes acute backlog in **Logistics**.\n"
            "• Notes customers complain about delivery delays, not billing errors.\n"
            "• Reports Logistics agents are bogged down in manual carrier portal lookups."
        )

    st.markdown("---")

    # 2. Side-by-Side Empirical Comparison: Billing vs. Logistics
    st.subheader("📊 Empirical Head-to-Head: Billing vs. Logistics")
    
    col_metric, col_chart = st.columns([1, 1])

    with col_metric:
        st.markdown("**Core Operational Dimensions (18-Month Baseline)**")
        comp_data = [
            {"Dimension": "Roster Headcount", "Billing Team": "4 agents", "Logistics Team": "5 agents", "Winner / Assessment": "Similar base"},
            {"Dimension": "Assigned Intake Queue", "Billing Team": "2,425 tickets (20.8%)", "Logistics Team": "1,905 tickets (16.4%)", "Winner / Assessment": "Bot inflates Billing"},
            {"Dimension": "Actual Handled Volume", "Billing Team": "1,798 tickets (15.4%)", "Logistics Team": "2,574 tickets (22.1%)", "Winner / Assessment": "Logistics handles +43% more"},
            {"Dimension": "Net Volume Delta", "Billing Team": "-627 tickets (Shedder)", "Logistics Team": "+669 tickets (Absorber)", "Winner / Assessment": "Logistics absorbs massive overflow"},
            {"Dimension": "Monthly Tickets / Agent", "Billing Team": "25.0 tickets/mo", "Logistics Team": "28.6 tickets/mo", "Winner / Assessment": "Logistics carries highest load"},
            {"Dimension": "Median Resolution Time", "Billing Team": "1.22 hours", "Logistics Team": "26.03 hours", "Winner / Assessment": "Logistics is 21.3x slower"},
            {"Dimension": "Median Active Handle Time", "Billing Team": "0.38 h (23 mins)", "Logistics Team": "24.47 hours", "Winner / Assessment": "Carrier latency traps Logistics"},
            {"Dimension": "SLA Breaches (Policy §3)", "Billing Team": "241 breaches (13.4%)", "Logistics Team": "423 breaches (16.4%)", "Winner / Assessment": "Logistics generates ₹1.48L penalty"},
            {"Dimension": "Customer Satisfaction (CSAT)", "Billing Team": "3.41 / 5.0", "Logistics Team": "2.89 / 5.0", "Winner / Assessment": "Logistics has lowest CSAT"},
        ]
        st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

    with col_chart:
        st.markdown("**Workload & Resolution Friction Comparison**")
        fig_radar = go.Figure()
        categories = ["Tickets/Agent/Mo", "Resolution Delay (h)", "Handle Time (h)", "SLA Breach Rate (%)", "CSAT Score (/5)"]
        
        # Normalized values for visual comparison
        billing_vals = [25.0, 1.22, 0.38, 13.40, 3.41]
        logistics_vals = [28.6, 26.03, 24.47, 16.43, 2.89]

        fig_bar = go.Figure(data=[
            go.Bar(name="Billing", x=categories, y=billing_vals, marker_color="#1f77b4"),
            go.Bar(name="Logistics", x=categories, y=logistics_vals, marker_color="#d62728")
        ])
        fig_bar.update_layout(
            barmode="group",
            margin=dict(l=10, r=10, t=10, b=10),
            height=340,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # 3. Four Strategic Options Evaluated
    st.subheader("💼 Comparative Headcount & Process Scenarios")
    
    scenarios = [
        {
            "Option": "Option 1: Priya's Initial Plan\n(Hire 2 into Billing)",
            "Annual Cost": "₹9,00,000",
            "Expected Process Savings": "₹0",
            "Net Annual Cost": "-₹9,00,000",
            "Operational Impact": "Severe Failure. Billing workload drops to ~16 tix/mo (acute idle capacity). Fast 1.22h resolution, 23m handle time, and -627 net delta prove no staffing deficit.",
            "Recommendation": "❌ REJECTED"
        },
        {
            "Option": "Option 2: Arjun's Process Fix Only\n(Zero New Hires)",
            "Annual Cost": "₹0",
            "Expected Process Savings": "₹1,99,853 (~₹2.0L)*",
            "Net Annual Cost": "+₹1,99,853",
            "Operational Impact": "Moderate Benefit. Eliminates transfer waste, but Logistics agents remain overwhelmed by manual carrier portal lookups and 26h delays.",
            "Recommendation": "⚠️ INSUFFICIENT"
        },
        {
            "Option": "Option 3: Conditional Hybrid\n(Process Fix + Conditional 1 Logistics Hire)",
            "Annual Cost": "₹4,50,000",
            "Expected Process Savings": "₹1,99,853 (~₹2.0L)*",
            "Net Annual Cost": "-₹2,50,147",
            "Operational Impact": "Optimal. Process fixes reduce transfer waste. Adding 1 hire to Logistics is conditional on validating if existing staff can absorb direct volume.",
            "Recommendation": "⭐ CONDITIONAL OPTIMAL"
        },
        {
            "Option": "Option 4: Phased Deployment\n(1 Logistics + 2nd Hire Subject to 90d Review)",
            "Annual Cost": "₹9,00,000 (Max Cap)",
            "Expected Process Savings": "₹2,59,853 (~₹2.6L)*",
            "Net Annual Cost": "-₹6,40,147",
            "Operational Impact": "Phased. First hire to Logistics; second hire held in reserve and strictly subject to 90-day review of routing fix impact before release.",
            "Recommendation": "✅ PHASED ALTERNATIVE"
        }
    ]
    st.dataframe(pd.DataFrame(scenarios), use_container_width=True, hide_index=True)
    st.caption("*Note: Process savings (₹1,99,853/yr) are hypothetical potential operational reductions, not guaranteed liquid cash additions.")

    st.markdown("---")

    # 4. Strategic Phased Recommendation & 90-Day Goal
    st.subheader("🎯 Strategic Phased Recommendation & 90-Day Operational Goal")

    rec1, rec2, rec3 = st.columns(3)
    with rec1:
        st.markdown("### **Phase 1: Process Re-Engineering**")
        st.markdown("**Timeline:** Days 0–30 · **Cost:** ₹0")
        st.markdown(
            "• Retrain intake bot routing rules using Seven-Pillar taxonomy.\n"
            "• Route delivery tracking directly to Logistics.\n"
            "• Eliminates **696 avoidable transfers** from Billing.\n"
            "• Unlocks **₹1,99,853 annually (~₹2.0L)** in hypothetical transfer & SLA savings."
        )

    with rec2:
        st.markdown("### **Phase 2: Conditional Logistics Hire**")
        st.markdown("**Timeline:** Days 30–60 · **Cost:** ₹4.50 Lakh")
        st.markdown(
            "• **Conditional Hire:** Allocate 1 hire to Logistics only after validating whether existing staff can absorb direct order volume.\n"
            "• Net annual cost is **₹2,50,147** after hypothetical process savings offset.\n"
            "• Increases Logistics carrier follow-up capacity by **+20%**.\n"
            "• Directly attacks the 26.03-hour resolution bottleneck."
        )

    with rec3:
        st.markdown("### **Phase 3: Formal 90-Day Review**")
        st.markdown("**Timeline:** Days 60–90 · **Cost:** ₹4.50 Lakh or Reserve")
        st.markdown(
            "• **Second Hire on Hold:** Subject the second hire to a formal 90-day post-routing-fix audit.\n"
            "• If Chat Frontline SLA breaches persist (265 breaches), release to Chat; otherwise retain the ₹4.50 Lakh in corporate budget reserve."
        )

    st.success(
        "🏆 **Measurable 90-Day Executive Operational Goal:**\n\n"
        "> *Within 90 days of implementing intake bot re-routing and onboarding 1 Logistics hire, "
        "reduce Logistics median resolution time from **26.03 hours to ≤ 6.50 hours** (a 75% reduction), "
        "cut Logistics SLA breaches by ≥ 50% (from 423 to ≤ 210), and eliminate 100% of Billing-to-Logistics intake misroutes.*"
    )

    # 5. Operational Risks and Limitations
    with st.expander("⚠️ Operational Risks & Analytical Limitations"):
        st.markdown(
            """
            1. **Snapshot Roster Limitation:** `agents.csv` reflects static assignment periods rather than dynamic historical join/leave dates, leaves of absence, or shift rosters. Workload metrics represent roster headcount averages.
            2. **Carrier API Dependency:** A major driver of Logistics' 26.03h resolution delay is external courier partner portals (Delhivery, BlueDart). Headcount cannot substitute for automated AWB tracking webhooks.
            3. **Hypothetical Process Savings:** Process improvement savings (₹1.99 Lakh/yr) are **hypothetical potential operational cost reductions**, reducing administrative churn and store credits rather than generating liquid cash.
            4. **Repeat Contact Definition:** Customer re-contact within 30 days is an **empirical behavioral proxy**, not an explicit 're-opened ticket' count in Freshdesk.
            5. **Dual Disbursement Nature:** Dual disbursement risk (₹2.97 Lakh across 41 orders) represents an **unmonitored compliance and policy exposure**, rather than confirmed realized cash loss.
            """
        )

"""Team Workload module for Streamlit dashboard.

Analyzes departmental queue assignments, actual resolving volumes, agent productivity,
resolution delays, handle times, and enforces strict separation between Tier 1 and Tier 2.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.analytics.workload import WorkloadAnalyzer


def render_team_workload(
    filtered_df: pd.DataFrame,
    agents_df: pd.DataFrame,
    is_filtered: bool
):
    """Render Team Workload tab content."""
    st.header("👥 Departmental Capacity & Workload Analytics")
    st.markdown(
        "Forensic comparison of **assigned intake queue volume** versus **actual resolved volume** "
        "across all seven operational support teams."
    )

    # 1. Tier Demarcation Warning
    st.info(
        "🛡️ **Operating Policy §6 Mandate:** Tier 2 (Escalations & Warranty) agents handle certified RMA investigations, "
        "component failure root-cause analysis, and third-party logistics escalations. "
        "Their workload is measured in **multi-day investigations, not raw weekly tickets**. "
        "Tier 2 productivity must **never** be directly compared with Tier 1 frontline queues."
    )

    # 2. Compute Workload Table
    workload_summary = WorkloadAnalyzer.compute_team_workload_summary(filtered_df, agents_df)

    # Calculate additional metrics for each team from filtered_df
    extra_metrics = []
    for _, row in workload_summary.iterrows():
        t = row["team"]
        t_tix = filtered_df[filtered_df["resolving_team"] == t]
        med_res = float(t_tix["total_res_time_hrs"].median()) if len(t_tix) > 0 else np.nan
        med_hdl = float(t_tix["handle_time_hrs"].median()) if len(t_tix) > 0 else np.nan
        breaches = int(t_tix["is_sla_breach"].sum())
        res_vol = row["resolved_volume"]
        brch_rate = round(breaches / res_vol * 100, 2) if res_vol > 0 else 0.0
        csat_vals = t_tix["csat_score"].dropna()
        csat_mean = round(float(csat_vals.mean()), 2) if len(csat_vals) > 0 else np.nan

        extra_metrics.append({
            "team": t,
            "median_resolution_hours": med_res,
            "median_handle_hours": med_hdl,
            "sla_breaches": breaches,
            "sla_breach_rate_pct": brch_rate,
            "csat_mean": csat_mean
        })

    extra_df = pd.DataFrame(extra_metrics)
    full_workload = workload_summary.merge(extra_df, on="team", how="left")

    # 3. Assigned vs Resolved Comparison Chart
    st.subheader("📊 Intake Assignment vs. Actual Resolving Volume (Net Delta)")
    fig_vol = go.Figure()
    fig_vol.add_trace(go.Bar(
        x=full_workload["team"],
        y=full_workload["assigned_volume"],
        name="Assigned by Intake Bot",
        marker_color="#ff7f0e",
        opacity=0.85
    ))
    fig_vol.add_trace(go.Bar(
        x=full_workload["team"],
        y=full_workload["resolved_volume"],
        name="Actually Resolved by Team",
        marker_color="#2ca02c",
        opacity=0.85
    ))

    fig_vol.update_layout(
        title="Departmental Intake Queue Assignment vs. Resolved Tickets",
        xaxis_title="Support Department",
        yaxis_title="Total Tickets",
        barmode="group",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_vol, use_container_width=True)

    # 4. Departmental Capacity Table (Tier 1 vs Tier 2 Separated)
    st.subheader("📋 Comprehensive Departmental Capacity Metrics")
    
    t1_df = full_workload[full_workload["tier"] == 1].copy()
    t2_df = full_workload[full_workload["tier"] == 2].copy()

    st.markdown("#### **Tier 1 Support Queues (Frontline & Core Resolution)**")
    st.dataframe(
        t1_df[[
            "team", "roster_headcount", "assigned_volume", "resolved_volume", "net_volume_delta",
            "monthly_tickets_per_agent", "median_resolution_hours", "median_handle_hours",
            "sla_breach_rate_pct", "csat_mean"
        ]].rename(columns={
            "team": "Department",
            "roster_headcount": "Roster Agents",
            "assigned_volume": "Assigned Intake",
            "resolved_volume": "Actual Resolved",
            "net_volume_delta": "Net Delta",
            "monthly_tickets_per_agent": "Monthly Tix/Agent",
            "median_resolution_hours": "Median Res (h)",
            "median_handle_hours": "Median Handle (h)",
            "sla_breach_rate_pct": "SLA Breach %",
            "csat_mean": "Mean CSAT"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("#### **Tier 2 Certified Escalations Queue (Specialist Hardware RMA)**")
    st.dataframe(
        t2_df[[
            "team", "roster_headcount", "assigned_volume", "resolved_volume", "net_volume_delta",
            "monthly_tickets_per_agent", "median_resolution_hours", "median_handle_hours",
            "sla_breach_rate_pct", "csat_mean"
        ]].rename(columns={
            "team": "Department",
            "roster_headcount": "Roster Agents",
            "assigned_volume": "Assigned Intake",
            "resolved_volume": "Actual Resolved",
            "net_volume_delta": "Net Delta",
            "monthly_tickets_per_agent": "Monthly Tix/Agent",
            "median_resolution_hours": "Median Res (h)",
            "median_handle_hours": "Median Handle (h)",
            "sla_breach_rate_pct": "SLA Breach %",
            "csat_mean": "Mean CSAT"
        }),
        use_container_width=True,
        hide_index=True
    )
    st.caption(
        "Tier 2 note: 6.0 monthly tickets per agent reflects depot diagnostics and repair cycles "
        "(median 122.42h resolution delay), not low agent productivity."
    )

    st.markdown("---")

    # 5. Speed vs. Friction Deep-Dive (Logistics vs. Billing)
    st.subheader("⚡ Resolution Velocity & Handle Time Disparity")
    speed_col1, speed_col2 = st.columns(2)

    with speed_col1:
        st.markdown("**Median Total Resolution Delay (Created to Resolved)**")
        fig_res = px.bar(
            full_workload,
            x="team",
            y="median_resolution_hours",
            color="tier",
            text="median_resolution_hours",
            color_discrete_map={1: "#1f77b4", 2: "#9467bd"}
        )
        fig_res.update_layout(
            yaxis_title="Median Hours",
            xaxis_title="",
            margin=dict(l=10, r=10, t=10, b=10),
            height=280,
            showlegend=False
        )
        st.plotly_chart(fig_res, use_container_width=True)

    with speed_col2:
        st.markdown("**Median Active Handle Time (First Response to Resolved)**")
        fig_hdl = px.bar(
            full_workload,
            x="team",
            y="median_handle_hours",
            color="tier",
            text="median_handle_hours",
            color_discrete_map={1: "#2ca02c", 2: "#9467bd"}
        )
        fig_hdl.update_layout(
            yaxis_title="Median Hours",
            xaxis_title="",
            margin=dict(l=10, r=10, t=10, b=10),
            height=280,
            showlegend=False
        )
        st.plotly_chart(fig_hdl, use_container_width=True)

    st.markdown(
        "> **Key Takeaway:** Billing resolves inquiries in a median of **1.22 hours** (active touch time **23 minutes**). "
        "In contrast, Logistics inquiries take **26.03 hours** to resolve due to manual courier portal lookups and tracking delays."
    )

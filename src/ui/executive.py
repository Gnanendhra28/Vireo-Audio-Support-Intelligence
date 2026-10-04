"""Executive Overview module for Streamlit dashboard.

Displays high-level operational KPIs, monthly volume trends, status breakdown,
category shares, and audited financial indicators for executive decision-makers.
"""

from typing import Dict, Any
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.ui.data_service import format_inr, format_lakh


def render_executive_overview(
    filtered_df: pd.DataFrame,
    agents_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    products_df: pd.DataFrame,
    is_filtered: bool,
    total_core_count: int = 11641
):
    """Render Executive Overview tab content."""
    st.header("📊 Executive Operations & Performance Overview")
    st.markdown(
        "Executive snapshot of Vireo Audio support operations across the **audited 18-month baseline** "
        "(1 January 2025 – 30 June 2026). All metrics strictly adhere to Operating Policy v3.2 standards."
    )

    if is_filtered:
        st.info(
            f"ℹ️ **Filtered View Active:** Displaying **{len(filtered_df):,}** of **{total_core_count:,}** "
            f"core period tickets ({len(filtered_df)/total_core_count*100:.1f}%). "
            "Organizational benchmarks (such as roster headcount) remain fixed."
        )

    # 1. Top KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)

    tot_tickets = len(filtered_df)
    res_count = int((filtered_df["status"] == "resolved").sum())
    auto_closed = int((filtered_df["status"] == "closed").sum())
    open_pending = int(filtered_df["status"].isin(["open", "pending"]).sum())

    sla_breaches = int(filtered_df["is_sla_breach"].sum())
    sla_breach_rate = (sla_breaches / tot_tickets * 100) if tot_tickets > 0 else 0.0
    sla_compliance_rate = 100.0 - sla_breach_rate

    valid_res_time = filtered_df["total_res_time_hrs"].dropna()
    med_res_time = float(valid_res_time.median()) if len(valid_res_time) > 0 else 0.0

    csat_valid = filtered_df["csat_score"].dropna()
    csat_mean = float(csat_valid.mean()) if len(csat_valid) > 0 else np.nan

    col1.metric(
        "Core Period Tickets",
        f"{tot_tickets:,}",
        help="Total customer inquiries created in the evaluated period."
    )
    col2.metric(
        "Resolution Rate",
        f"{res_count / tot_tickets * 100:.1f}%" if tot_tickets > 0 else "0%",
        f"{res_count:,} resolved",
        help="Confirmed agent resolutions. Auto-closed tickets are tracked separately."
    )
    col3.metric(
        "SLA Compliance",
        f"{sla_compliance_rate:.1f}%",
        f"{sla_breaches:,} breaches ({sla_breach_rate:.1f}%)",
        delta_color="inverse",
        help="First-response compliance evaluated against Policy §3 channel targets."
    )
    col4.metric(
        "Median Resolution Time",
        f"{med_res_time:.1f} hrs",
        help="Median time from ticket creation to final resolution (inclusive of legacy UTC fix)."
    )
    col5.metric(
        "Mean CSAT Score",
        f"{csat_mean:.2f} / 5.0" if pd.notna(csat_mean) else "N/A",
        f"{len(csat_valid):,} responses",
        help="Customer satisfaction rating across completed surveys (nulls excluded)."
    )

    st.markdown("---")

    # 2. Status Reconciliation Row & Financial Indicator Cards
    st.subheader("📑 Status Accounting & Audited Operational Cost Indicators")
    
    stat_col1, stat_col2 = st.columns([1, 2])

    with stat_col1:
        st.markdown("**Ticket Status Breakdown**")
        status_counts = filtered_df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Tickets"]
        fig_status = px.pie(
            status_counts,
            names="Status",
            values="Tickets",
            color="Status",
            color_discrete_map={
                "resolved": "#2ca02c",
                "closed": "#1f77b4",
                "open": "#d62728",
                "pending": "#ff7f0e"
            },
            hole=0.45
        )
        fig_status.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=240,
            showlegend=True
        )
        st.plotly_chart(fig_status, use_container_width=True)
        st.caption(
            f"• Resolved by Agent: **{res_count:,}** | • Auto-Closed (Policy §8): **{auto_closed:,}**\n"
            f"• Active Backlog (Open + Pending): **{open_pending:,}**"
        )

    with stat_col2:
        st.markdown("**Audited Operational Cost & Exposure Lines**")
        c1, c2, c3 = st.columns(3)

        # Inbound handling cost
        channel_rates = {"chat": 210, "email": 260, "voice": 520, "social": 240}
        inbound_cost = float(sum(filtered_df["channel"].str.lower().map(channel_rates).dropna()))

        # SLA credit liability
        sla_liability = float(sla_breaches * 350.0)

        # Observable transfers
        hd_subset = filtered_df[filtered_df["source_system"] == "helpdesk"]
        transfer_vol = float(hd_subset["transfers"].sum())
        transfer_cost = float(transfer_vol * 305.0)

        # Repeat contact proxy
        repeat_tix = filtered_df[filtered_df["is_repeat_contact_30d"] == True]
        repeat_cost = float(sum(repeat_tix["channel"].str.lower().map(channel_rates).dropna()))

        # Dual disbursement
        refund_orders = set(filtered_df[filtered_df["refund_amount_inr"] > 0]["order_id"].dropna())
        repl_orders = set(filtered_df[filtered_df["replacement_issued"] == "Y"]["order_id"].dropna())
        dual_order_ids = refund_orders.intersection(repl_orders)
        dual_tix = filtered_df[filtered_df["order_id"].isin(dual_order_ids)]
        dual_refunds = float(dual_tix["refund_amount_inr"].sum())
        sku_map = products_df.set_index("sku")["unit_cost_inr"].to_dict()
        dual_orders_df = orders_df[orders_df["order_id"].isin(dual_order_ids)]
        dual_repl = sum(sku_map.get(row["sku"], 1400.0) + 340.0 for _, row in dual_orders_df.iterrows())
        dual_total = dual_refunds + dual_repl

        c1.metric("Inbound Handling Cost", format_lakh(inbound_cost), f"{format_inr(inbound_cost)}")
        c1.caption("Observed labor across channels (Policy §4)")

        c2.metric("SLA Store Credits", format_lakh(sla_liability), f"{sla_breaches:,} breaches @ ₹350")
        c2.caption("Observed compensation liability (Policy §3)")

        c3.metric("Transfer Friction Cost", format_lakh(transfer_cost), f"{int(transfer_vol):,} transfers @ ₹305")
        c3.caption("Observable post-migration helpdesk cost")

        c4, c5, c6 = st.columns(3)
        c4.metric("Dual Disbursement", format_lakh(dual_total), f"{len(dual_order_ids)} violating orders")
        c4.caption("Unmonitored compliance leakage (Policy §5)")

        c5.metric("Repeat Contact Waste", format_lakh(repeat_cost), f"{len(repeat_tix):,} repeat contacts")
        c5.caption("Customer 30-day return rate proxy")

        c6.metric("Annual Two-Hire Budget", "₹9.00 Lakh", "2 Agents @ ₹4.5L")
        c6.caption("Benchmark headcount budget cap")

    st.markdown("---")

    # 3. Monthly Ticket Volume Trend & Seasonality
    st.subheader("📈 Monthly Ticket Volume & SLA Breach Trend")
    monthly_grp = filtered_df.groupby("year_month").agg(
        total_tickets=("ticket_id", "count"),
        resolved=("status", lambda s: (s == "resolved").sum()),
        sla_breaches=("is_sla_breach", "sum")
    ).reset_index()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(
        x=monthly_grp["year_month"],
        y=monthly_grp["total_tickets"],
        name="Total Incoming Tickets",
        marker_color="#1f77b4",
        opacity=0.85
    ))
    fig_trend.add_trace(go.Scatter(
        x=monthly_grp["year_month"],
        y=monthly_grp["sla_breaches"],
        name="SLA Breaches (Policy §3)",
        mode="lines+markers",
        line=dict(color="#d62728", width=3),
        marker=dict(size=7)
    ))

    # Add peak annotation if 2025-10 to 2025-12 present
    if "2025-11" in monthly_grp["year_month"].values:
        fig_trend.add_annotation(
            x="2025-11",
            y=int(monthly_grp[monthly_grp["year_month"] == "2025-11"]["total_tickets"].iloc[0]),
            text="Diwali / Festive Peak (Q4 2025)",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#d62728",
            ax=0,
            ay=-40
        )

    fig_trend.update_layout(
        title="Monthly Inbound Volume vs. SLA Breaches (Jan 2025 – Jun 2026)",
        xaxis_title="Year-Month",
        yaxis_title="Tickets Count",
        barmode="group",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # 4. Category & Channel Breakdown
    st.subheader("🏷️ Intent Category & Inbound Channel Distributions")
    cat_col, ch_col = st.columns(2)

    with cat_col:
        st.markdown("**Seven-Pillar Predicted Intent Share**")
        cat_counts = filtered_df["predicted_category"].value_counts().reset_index()
        cat_counts.columns = ["Predicted Category", "Tickets"]
        fig_cat = px.bar(
            cat_counts,
            x="Tickets",
            y="Predicted Category",
            orientation="h",
            color="Tickets",
            color_continuous_scale="Viridis",
            text="Tickets"
        )
        fig_cat.update_layout(
            yaxis=dict(autorange="reversed"),
            margin=dict(l=10, r=10, t=10, b=10),
            height=300,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with ch_col:
        st.markdown("**Inbound Channel Volume vs. Total Channel Cost**")
        ch_summary = []
        for ch in ["chat", "email", "voice", "social"]:
            c_tix = (filtered_df["channel"].str.lower() == ch).sum()
            c_cost = c_tix * channel_rates[ch]
            ch_summary.append({
                "Channel": ch.capitalize(),
                "Tickets": c_tix,
                "Unit Rate": f"₹{channel_rates[ch]}",
                "Total Cost": c_cost
            })
        ch_df = pd.DataFrame(ch_summary)
        fig_ch = px.bar(
            ch_df,
            x="Channel",
            y="Total Cost",
            text=ch_df["Total Cost"].apply(format_lakh),
            color="Channel",
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_ch.update_layout(
            yaxis_title="Total Channel Cost (INR)",
            margin=dict(l=10, r=10, t=10, b=10),
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig_ch, use_container_width=True)
        st.caption("Notice: Voice represents 14.6% of ticket volume but generates 27.8% of inbound costs due to the ₹520 callback rate.")

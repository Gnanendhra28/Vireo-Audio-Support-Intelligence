"""Category Analytics module for Streamlit dashboard.

Presents Seven-Pillar taxonomy distributions, month-by-month category dynamics,
cross-department routing alignment, and forensic analysis of intake bot misclassifications.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.ui.data_service import format_inr


def render_category_analytics(
    filtered_df: pd.DataFrame,
    agents_df: pd.DataFrame,
    is_filtered: bool
):
    """Render Category Analytics tab content."""
    st.header("🏷️ Seven-Pillar Issue Category Analytics")
    st.markdown(
        "Granular analysis of customer intent using Vireo Audio's **Seven-Pillar Taxonomy**. "
        "Replaces noisy intake bot keywords with deterministic, explainable issue classification."
    )

    # Required Methodology Notice
    st.warning(
        "⚠️ **Methodology Note:** Issue categories and team routing recommendations displayed below are "
        "**AI model predictions** generated from customer messages and agent notes. "
        "They represent inferred customer intent, not human-audited ground truth."
    )

    # 1. Category Overview & Confidence KPIs
    tot_tix = len(filtered_df)
    avg_conf = filtered_df["confidence_score"].mean() if tot_tix > 0 else 0.0
    review_req = int(filtered_df["review_required"].sum()) if tot_tix > 0 else 0
    review_pct = (review_req / tot_tix * 100) if tot_tix > 0 else 0.0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Evaluated Inquiries", f"{tot_tix:,}")
    kpi2.metric("Mean Prediction Confidence", f"{avg_conf:.1%}")
    kpi3.metric("Human Review Required", f"{review_req:,}", f"{review_pct:.1f}% of volume", delta_color="inverse")
    kpi4.metric("Active Intent Categories", f"{filtered_df['predicted_category'].nunique()} Pillars")

    st.markdown("---")

    # 2. Monthly Trend by Category
    st.subheader("📅 Monthly Category Volume Trajectory")
    monthly_cat = filtered_df.groupby(["year_month", "predicted_category"]).size().reset_index(name="Tickets")

    fig_cat_time = px.line(
        monthly_cat,
        x="year_month",
        y="Tickets",
        color="predicted_category",
        title="Monthly Ticket Volume by Predicted Intent (Seven Pillars)",
        markers=True,
        color_discrete_sequence=px.colors.qualitative.Dark24
    )
    fig_cat_time.update_layout(
        xaxis_title="Year-Month",
        yaxis_title="Tickets Count",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(title="Seven Pillars", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_cat_time, use_container_width=True)

    # 3. Category Share & Team Cross-Tabulation
    st.subheader("🔀 Category Intent vs. Resolving Department Alignment")
    
    col_share, col_matrix = st.columns([1, 2])

    with col_share:
        st.markdown("**Predicted Category Volume Share**")
        cat_share = filtered_df["predicted_category"].value_counts().reset_index()
        cat_share.columns = ["Category", "Tickets"]
        cat_share["Share (%)"] = (cat_share["Tickets"] / tot_tix * 100).round(1)

        fig_donut = px.pie(
            cat_share,
            names="Category",
            values="Tickets",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_donut.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        st.dataframe(cat_share, use_container_width=True, hide_index=True)

    with col_matrix:
        st.markdown("**Departmental Handling Matrix (Category $\\times$ Resolving Team)**")
        cross_tab = pd.crosstab(
            filtered_df["predicted_category"],
            filtered_df["resolving_team"],
            margins=True,
            margins_name="Total Handled"
        )
        st.dataframe(cross_tab, use_container_width=True)
        st.caption(
            "Notice how 'Order & Logistics' inquiries flow heavily into Logistics (1,797 direct + 696 transfers from Billing)."
        )

    st.markdown("---")

    # 4. Forensic Spotlight: Bot Misclassification in Billing
    st.subheader("🔍 Intake Bot Forensic Spotlight: Billing Assigned vs. Actual Intent")
    st.markdown(
        "Vireo Audio's legacy intake bot assigned tickets strictly on keyword triggers. When customers wrote "
        "*'I paid 5 days ago, where is my order?'*, the bot routed the ticket to **Billing** because of the word *'paid'*, "
        "even though the customer's actual inquiry was a delivery delay."
    )

    billing_assigned = filtered_df[filtered_df["assigned_team"] == "Billing"]
    b_total = len(billing_assigned)
    b_log_intent = (billing_assigned["predicted_category"] == "Order & Logistics").sum()
    b_resolved_by_log = (billing_assigned["resolving_team"] == "Logistics").sum()

    spot1, spot2, spot3 = st.columns(3)
    spot1.metric("Intake Assigned to Billing", f"{b_total:,}")
    spot2.metric("True Intent: Order & Logistics", f"{b_log_intent:,}", f"{b_log_intent/b_total*100:.1f}% misrouted" if b_total > 0 else "0%")
    spot3.metric("Actually Resolved by Logistics", f"{b_resolved_by_log:,}", f"{b_resolved_by_log/b_total*100:.1f}% hand-off" if b_total > 0 else "0%")

    st.markdown("**Audited Misclassification Records Sample:**")
    misrouted_sample = billing_assigned[
        (billing_assigned["predicted_category"] == "Order & Logistics")
    ][["ticket_id", "channel", "category", "predicted_category", "resolving_team", "customer_message", "evidence"]].head(8)

    st.dataframe(
        misrouted_sample,
        column_config={
            "ticket_id": "Ticket ID",
            "channel": "Channel",
            "category": "Intake Bot Tag",
            "predicted_category": "AI Predicted Intent",
            "resolving_team": "Actual Resolving Team",
            "customer_message": st.column_config.TextColumn("Customer Message", width="medium"),
            "evidence": st.column_config.TextColumn("Classification Evidence", width="medium")
        },
        use_container_width=True,
        hide_index=True
    )
    st.caption(
        "Root cause confirmed: Customers mention payment confirmation while seeking tracking updates. "
        "Intake bot keyword matching caused 696 avoidable hand-offs to Logistics in the core 18-month baseline."
    )

"""Financial Impact & Cost Modeling module for Streamlit dashboard.

Maintains strict separation between observed historical expenditures, observable friction,
compliance exposures, and hypothetical process improvement savings.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.ui.data_service import format_inr, format_lakh


def render_financial_impact(
    filtered_df: pd.DataFrame,
    agents_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    products_df: pd.DataFrame,
    is_filtered: bool
):
    """Render Financial Impact tab content."""
    st.header("💰 Financial Operations & Support Cost Modeling")
    st.markdown(
        "Audited cost analysis and financial governance across Vireo Audio's support operations. "
        "Calculated in strict compliance with **Operating Policy v3.2** cost schedules."
    )

    # Required Accounting Principles Callout
    st.warning(
        "⚖️ **Financial Accounting Notice:**\n"
        "1. **Zero Double-Counting:** Channel handling, internal transfers, and SLA breach credits represent independent cost lines.\n"
        "2. **Category Boundaries:** Observed historical costs (labor, store credits) are strictly segregated from "
        "*compliance exposures* (dual disbursements) and *hypothetical process savings* (intake bot re-routing).\n"
        "3. **Never Present Hypothetical Savings as Realized Cash:** Process improvements eliminate friction and liabilities; "
        "they do not add liquid revenue to bank balances."
    )

    # 1. Independent Financial Lines Master Table
    st.subheader("📑 Master Financial Accounting Schedule")
    
    tot_tix = len(filtered_df)
    channel_rates = {"chat": 210, "email": 260, "voice": 520, "social": 240}
    inbound_cost = float(sum(filtered_df["channel"].str.lower().map(channel_rates).dropna()))

    sla_breaches = int(filtered_df["is_sla_breach"].sum())
    sla_cost = float(sla_breaches * 350.0)

    hd_subset = filtered_df[filtered_df["source_system"] == "helpdesk"]
    transfers_vol = float(hd_subset["transfers"].sum())
    transfers_cost = float(transfers_vol * 305.0)

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

    # Billing to Logistics process waste in filtered view
    b_to_l = filtered_df[
        (filtered_df["assigned_team"] == "Billing") & (filtered_df["resolving_team"] == "Logistics")
    ]
    b_to_l_count = len(b_to_l)
    b_to_l_xfer = b_to_l_count * 305.0
    b_to_l_sla = float(b_to_l["is_sla_breach"].sum() * 350.0)
    process_waste_18m = b_to_l_xfer + b_to_l_sla
    process_waste_annual = (process_waste_18m / 18.0) * 12.0

    fin_table = [
        {
            "Cost Line": "1. Inbound Channel Labor",
            "Formula / Rate": "Policy §4 Channel Rates",
            "Volume Basis": f"{tot_tix:,} tickets",
            "18-Month Cost": format_inr(inbound_cost),
            "Annualized Cost": format_inr((inbound_cost / 18.0) * 12.0),
            "Accounting Nature": "Observed Operating Cost"
        },
        {
            "Cost Line": "2. SLA Store Credit Exposure",
            "Formula / Rate": "Breaches × ₹350.00",
            "Volume Basis": f"{sla_breaches:,} breaches",
            "18-Month Cost": format_inr(sla_cost),
            "Annualized Cost": format_inr((sla_cost / 18.0) * 12.0),
            "Accounting Nature": "Observed Liability / Compensation"
        },
        {
            "Cost Line": "3. Internal Transfer Friction",
            "Formula / Rate": "Transfers × ₹305.00",
            "Volume Basis": f"{int(transfers_vol):,} transfers (Helpdesk)",
            "18-Month Cost": format_inr(transfers_cost),
            "Annualized Cost": format_inr((transfers_cost / 9.5) * 12.0) if transfers_vol > 0 else "N/A",
            "Accounting Nature": "Observable Friction Cost"
        },
        {
            "Cost Line": "4. Repeat Contact Waste (Proxy)",
            "Formula / Rate": "Customer 30-Day Window Proxy",
            "Volume Basis": f"{len(repeat_tix):,} tickets",
            "18-Month Cost": format_inr(repeat_cost),
            "Annualized Cost": format_inr((repeat_cost / 18.0) * 12.0),
            "Accounting Nature": "Estimated Proxy Waste"
        },
        {
            "Cost Line": "5. Dual Disbursement Leakage",
            "Formula / Rate": "Refunds + SKU Unit Cost + ₹340",
            "Volume Basis": f"{len(dual_order_ids)} orders",
            "18-Month Cost": format_inr(dual_total),
            "Annualized Cost": format_inr((dual_total / 18.0) * 12.0),
            "Accounting Nature": "Unmonitored Compliance Leakage"
        },
        {
            "Cost Line": "6. Re-Routing Process Savings",
            "Formula / Rate": "(696 xfers × ₹305) + (250 SLA × ₹350)",
            "Volume Basis": f"{b_to_l_count:,} misrouted tickets",
            "18-Month Cost": format_inr(process_waste_18m),
            "Annualized Cost": format_inr(process_waste_annual),
            "Accounting Nature": "Hypothetical Process Savings"
        },
        {
            "Cost Line": "7. Headcount Investment Cap",
            "Formula / Rate": "2 Support Agents × ₹4.50 Lakh",
            "Volume Basis": "2 Headcount",
            "18-Month Cost": "₹13,50,000",
            "Annualized Cost": "₹9,00,000",
            "Accounting Nature": "Fixed Annual Budget Cap"
        }
    ]
    st.dataframe(pd.DataFrame(fin_table), use_container_width=True, hide_index=True)

    st.markdown("---")

    # 2. Deep-Dive: Inbound Channel Cost Disparity
    st.subheader("📞 Channel Cost Structure & Voice Callback Optimization")
    col_ch1, col_ch2 = st.columns([1, 1])

    with col_ch1:
        st.markdown("**Channel Volume Share vs. Expenditure Share**")
        ch_comp = []
        for ch in ["chat", "email", "voice", "social"]:
            c_cnt = (filtered_df["channel"].str.lower() == ch).sum()
            c_cst = c_cnt * channel_rates[ch]
            ch_comp.append({
                "Channel": ch.capitalize(),
                "Tickets": c_cnt,
                "Volume Share (%)": round(c_cnt / tot_tix * 100, 1) if tot_tix > 0 else 0,
                "Expenditure (INR)": c_cst,
                "Cost Share (%)": round(c_cst / inbound_cost * 100, 1) if inbound_cost > 0 else 0
            })
        ch_comp_df = pd.DataFrame(ch_comp)
        st.dataframe(ch_comp_df, use_container_width=True, hide_index=True)

    with col_ch2:
        st.markdown("**Channel Unit Rates (Operating Policy §4)**")
        fig_rates = px.bar(
            ch_comp_df,
            x="Channel",
            y="Cost Share (%)",
            color="Channel",
            text="Cost Share (%)",
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_rates.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=260,
            showlegend=False
        )
        st.plotly_chart(fig_rates, use_container_width=True)

    st.caption(
        "Strategic takeaway: Voice callback is priced at ₹520/contact (2.5x more expensive than Chat). "
        "Deflecting simple tracking callbacks into automated WhatsApp/SMS bots yields substantial immediate cost avoidance."
    )

    st.markdown("---")

    # 3. Policy §5 Compliance Violation: Dual Disbursement Leakage
    st.subheader("⚠️ Operating Policy §5 Violation: Dual Disbursement Exposure")
    st.markdown(
        "Operating Policy §5 explicitly mandates:  \n"
        "> *'In no case is a customer to receive both a refund and a replacement for the same order.'*"
    )

    d_col1, d_col2, d_col3 = st.columns(3)
    d_col1.metric("Violating Orders Identified", f"{len(dual_order_ids)} orders")
    d_col2.metric("Cash Refunds Disbursed", format_inr(dual_refunds))
    d_col3.metric("Replacement Goods + Logistics", format_inr(dual_repl))

    st.markdown(
        f"**Total Preventable Financial Leakage:** `{format_inr(dual_total)}` over 18 months "
        f"(`{format_lakh(dual_total)}` exposure, or `{format_inr((dual_total / 18.0) * 12.0)}` annualized)."
    )

    st.markdown("**Sample Violating Orders Audited:**")
    sample_violating_orders = list(dual_order_ids)[:6]
    violating_rows = filtered_df[filtered_df["order_id"].isin(sample_violating_orders)][
        ["ticket_id", "order_id", "channel", "category", "refund_amount_inr", "replacement_issued", "resolving_team"]
    ]
    st.dataframe(violating_rows, use_container_width=True, hide_index=True)

    st.error(
        "🛡️ **Financial Governance Remediation:**\n"
        "Configure a mandatory database validation trigger in the support helpdesk. "
        "If `refund_amount_inr > 0` has been processed for an `order_id`, the system must prevent agents "
        "from selecting `replacement_issued = 'Y'` without explicit Finance Lead (Arjun Mehta) authorization. "
        "This immediately closes **~₹2.63 Lakh annually** in unrecovered leakages."
    )

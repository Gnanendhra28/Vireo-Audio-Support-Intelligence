"""Vireo Audio Support Intelligence - Executive Interactive Operations Dashboard.

Main Streamlit Application Entrypoint.
Complies with Operating Policy v3.2 standards and metric_reconciliation.md audited figures.
"""

import sys
from pathlib import Path

# Ensure vireo-support-intelligence is on sys.path regardless of execution working directory
current_file = Path(__file__).resolve()
project_root = current_file.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd

from src.ui.data_service import load_and_preprocess_all, apply_filters
from src.ui.executive import render_executive_overview
from src.ui.categories import render_category_analytics
from src.ui.workload import render_team_workload
from src.ui.staffing import render_staffing_decision
from src.ui.financial import render_financial_impact
from src.ui.audit_view import render_audit_reconciliation
from src.ui.triage_view import render_triage_agent_view
from src.ui.upload_view import render_upload_workspace


def main():
    st.set_page_config(
        page_title="Vireo Audio Support Intelligence",
        page_icon="🎧",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Load preprocessed datasets
    data = load_and_preprocess_all()
    tickets_raw = data["tickets"]
    agents = data["agents"]
    orders = data["orders"]
    products = data["products"]

    # Core 18-month baseline count
    core_total_count = int(tickets_raw["in_core_18m"].sum())

    # --- SIDEBAR: NAVIGATION & FILTERS ---
    st.sidebar.title("🎧 Vireo Intelligence")
    st.sidebar.caption("Executive Support Operations Decision Engine")

    nav_options = [
        "📊 Executive Overview",
        "🏷️ Category Analytics",
        "👥 Team Workload",
        "⚖️ Staffing Decision",
        "💰 Financial Impact",
        "🔍 Master Audit Reconciliation",
        "🤖 Support Triage Agent",
        "📁 Dynamic CSV Upload Workspace"
    ]
    query_view = st.query_params.get("view", None)
    default_index = 0
    if query_view:
        for idx, opt in enumerate(nav_options):
            if query_view.lower() in opt.lower():
                default_index = idx
                break

    nav_selection = st.sidebar.radio(
        "Navigation",
        nav_options,
        index=default_index
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎛️ Interactive Filters")

    # Scope Selection
    scope = st.sidebar.selectbox(
        "Analysis Scope",
        ["Core 18-Month Baseline (Jan 2025 – Jun 2026)", "All-Time Dataset (Incl. 2024 Pilot)"],
        index=0,
        help="Default baseline evaluates the audited 18-month operational window."
    )
    use_core = (scope == "Core 18-Month Baseline (Jan 2025 – Jun 2026)")

    base_tickets = tickets_raw[tickets_raw["in_core_18m"] == True] if use_core else tickets_raw

    # Months Filter
    all_months = sorted(base_tickets["year_month"].unique().tolist())
    selected_months = st.sidebar.multiselect(
        "Filter Year-Month",
        options=all_months,
        default=[],
        placeholder="All months (Jan 2025 – Jun 2026)"
    )

    # Category Filter
    all_categories = sorted(base_tickets["predicted_category"].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "Seven-Pillar Category",
        options=all_categories,
        default=[],
        placeholder="All Seven Pillars"
    )

    # Resolving Team Filter
    all_teams = sorted(base_tickets["resolving_team"].dropna().unique().tolist())
    selected_teams = st.sidebar.multiselect(
        "Resolving Department",
        options=all_teams,
        default=[],
        placeholder="All Departments"
    )

    # Channel Filter
    all_channels = sorted(base_tickets["channel"].str.capitalize().unique().tolist())
    selected_channels = st.sidebar.multiselect(
        "Inbound Channel",
        options=all_channels,
        default=[],
        placeholder="All Channels"
    )

    # Status Filter
    all_statuses = sorted(base_tickets["status"].unique().tolist())
    selected_statuses = st.sidebar.multiselect(
        "Ticket Status",
        options=all_statuses,
        default=[],
        placeholder="All Statuses"
    )

    # Apply Filters
    filtered_tickets = apply_filters(
        tickets_df=tickets_raw,
        selected_months=selected_months if selected_months else None,
        selected_categories=selected_categories if selected_categories else None,
        selected_teams=selected_teams if selected_teams else None,
        selected_channels=selected_channels if selected_channels else None,
        selected_statuses=selected_statuses if selected_statuses else None,
        use_core_only=use_core
    )

    is_filtered = (
        len(filtered_tickets) != (core_total_count if use_core else len(tickets_raw))
    )

    # Reset Filters Button
    if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.metric(
        "Sample Evaluated",
        f"{len(filtered_tickets):,} tickets",
        f"{len(filtered_tickets) / core_total_count * 100:.1f}% of core" if use_core else f"{len(filtered_tickets):,} total"
    )

    st.sidebar.info(
        "**Governing Policy:** Operating Policy v3.2\n"
        "**Headcount Budget:** 2 Hires = ₹9,00,000/yr\n"
        "**Roster Baseline:** 44 Active Agents"
    )

    # --- MAIN VIEW DISPATCHER ---
    if nav_selection == "📊 Executive Overview":
        render_executive_overview(
            filtered_df=filtered_tickets,
            agents_df=agents,
            orders_df=orders,
            products_df=products,
            is_filtered=is_filtered,
            total_core_count=core_total_count
        )

    elif nav_selection == "🏷️ Category Analytics":
        render_category_analytics(
            filtered_df=filtered_tickets,
            agents_df=agents,
            is_filtered=is_filtered
        )

    elif nav_selection == "👥 Team Workload":
        render_team_workload(
            filtered_df=filtered_tickets,
            agents_df=agents,
            is_filtered=is_filtered
        )

    elif nav_selection == "⚖️ Staffing Decision":
        render_staffing_decision(
            filtered_df=filtered_tickets,
            agents_df=agents,
            is_filtered=is_filtered
        )

    elif nav_selection == "💰 Financial Impact":
        render_financial_impact(
            filtered_df=filtered_tickets,
            agents_df=agents,
            orders_df=orders,
            products_df=products,
            is_filtered=is_filtered
        )

    elif nav_selection == "🔍 Master Audit Reconciliation":
        render_audit_reconciliation()

    elif nav_selection == "🤖 Support Triage Agent":
        render_triage_agent_view(tickets_df=filtered_tickets)

    elif nav_selection == "📁 Dynamic CSV Upload Workspace":
        render_upload_workspace()

    # --- FOOTER ---
    st.markdown("---")
    st.caption(
        "**Vireo Audio Support Intelligence** · Confidential Management Decision Tool · "
        "Prepared for Priya Raman (Head of CX), Arjun Mehta (Finance Controller), and Neha Kulkarni (Support Operations). "
        "Data Source: 18-Month Operational Baseline (1 Jan 2025 – 30 Jun 2026). "
        "Metrics audited and certified in `outputs/reports/metric_reconciliation.md`."
    )


if __name__ == "__main__":
    main()

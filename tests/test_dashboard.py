"""Unit tests for the Streamlit interactive dashboard and UI service modules.

Covers:
- Dataset loading, preprocessing, and caching
- Interactive filtering behavior across all dimensions
- Currency formatting for INR Indian numbering
- Rendering functions module integrity
"""

import pytest
import pandas as pd
import numpy as np

from src.ui.data_service import (
    load_and_preprocess_all,
    apply_filters,
    format_inr,
    format_lakh
)
from src.ui.executive import render_executive_overview
from src.ui.categories import render_category_analytics
from src.ui.workload import render_team_workload
from src.ui.staffing import render_staffing_decision
from src.ui.financial import render_financial_impact
from src.ui.audit_view import render_audit_reconciliation
from src.ui.triage_view import render_triage_agent_view
from src.ui.upload_view import render_upload_workspace


@pytest.fixture(scope="module")
def app_data():
    """Load preprocessed app data once for test module."""
    return load_and_preprocess_all()


def test_ui_data_loading_and_core_scope(app_data):
    """Verify that dashboard data loads with expected shapes and core period scoping."""
    tickets = app_data["tickets"]
    agents = app_data["agents"]
    orders = app_data["orders"]
    products = app_data["products"]

    assert len(tickets) == 11780
    assert len(agents) == 44
    assert len(orders) == 15000
    assert len(products) == 14

    # Core 18M filter must yield exactly 11,641 tickets
    core_tix = tickets[tickets["in_core_18m"] == True]
    assert len(core_tix) == 11641

    # Verify no negative durations after legacy +05:30 correction
    valid_handles = core_tix["handle_time_hrs"].dropna()
    assert (valid_handles >= 0).all(), "Found negative handle times in core period"


def test_ui_filtering_behavior(app_data):
    """Verify interactive multi-dimensional filtering."""
    tickets = app_data["tickets"]

    # 1. Month filtering
    jan_2025 = apply_filters(tickets, selected_months=["2025-01"], use_core_only=True)
    assert len(jan_2025) > 0
    assert (jan_2025["year_month"] == "2025-01").all()

    # 2. Category filtering
    order_logistics = apply_filters(tickets, selected_categories=["Order & Logistics"], use_core_only=True)
    assert len(order_logistics) > 0
    assert (order_logistics["predicted_category"] == "Order & Logistics").all()

    # 3. Department filtering
    logistics_team = apply_filters(tickets, selected_teams=["Logistics"], use_core_only=True)
    assert len(logistics_team) == 2574
    assert (logistics_team["resolving_team"] == "Logistics").all()

    # 4. Channel filtering
    chat_only = apply_filters(tickets, selected_channels=["Chat"], use_core_only=True)
    assert len(chat_only) == 5290
    assert (chat_only["channel"].str.lower() == "chat").all()

    # 5. Status filtering
    resolved_only = apply_filters(tickets, selected_statuses=["resolved"], use_core_only=True)
    assert len(resolved_only) == 10007
    assert (resolved_only["status"] == "resolved").all()

    # 6. Combined multi-criteria filtering
    combined = apply_filters(
        tickets,
        selected_months=["2025-01", "2025-02"],
        selected_teams=["Billing"],
        selected_channels=["Chat"],
        selected_statuses=["resolved"],
        use_core_only=True
    )
    assert len(combined) > 0
    assert (combined["year_month"].isin(["2025-01", "2025-02"])).all()
    assert (combined["resolving_team"] == "Billing").all()
    assert (combined["channel"].str.lower() == "chat").all()
    assert (combined["status"] == "resolved").all()

    # 7. All-time vs core toggle
    all_time = apply_filters(tickets, use_core_only=False)
    assert len(all_time) == 11780


def test_inr_currency_formatting():
    """Verify Indian numbering format and Lakh notation."""
    assert format_inr(3182240) == "₹31,82,240"
    assert format_inr(452200) == "₹4,52,200"
    assert format_inr(900000) == "₹9,00,000"
    assert format_inr(0) == "₹0"
    assert format_inr(150.50, precision=2) == "₹150.50"

    assert format_lakh(3182240) == "₹31.82 Lakh"
    assert format_lakh(452200) == "₹4.52 Lakh"
    assert format_lakh(900000) == "₹9.00 Lakh"


def test_view_render_callables_exist():
    """Verify that all UI view functions are callable and properly exposed."""
    assert callable(render_executive_overview)
    assert callable(render_category_analytics)
    assert callable(render_team_workload)
    assert callable(render_staffing_decision)
    assert callable(render_financial_impact)
    assert callable(render_audit_reconciliation)
    assert callable(render_triage_agent_view)
    assert callable(render_upload_workspace)


def test_dashboard_navigation_registration_and_integrity():
    """Verify that all eight navigation options are registered in app.py without regression."""
    import inspect
    import app

    source = inspect.getsource(app.main)

    expected_views = [
        "📊 Executive Overview",
        "🏷️ Category Analytics",
        "👥 Team Workload",
        "⚖️ Staffing Decision",
        "💰 Financial Impact",
        "🔍 Master Audit Reconciliation",
        "🤖 Support Triage Agent",
        "📁 Dynamic CSV Upload Workspace"
    ]

    for view in expected_views:
        assert f'"{view}"' in source, f"Missing view in app.py navigation: {view}"

    # Verify dispatcher branches exist for triage and upload
    assert 'nav_selection == "🤖 Support Triage Agent"' in source
    assert 'render_triage_agent_view' in source
    assert 'nav_selection == "📁 Dynamic CSV Upload Workspace"' in source
    assert 'render_upload_workspace' in source


def test_qa_metric_reconciliation(app_data):
    """Verify exact audited metric reconciliation for status counts and repeat costs."""
    tickets = app_data["tickets"]
    core = tickets[tickets["in_core_18m"] == True]

    # 1. Total core tickets
    assert len(core) == 11641

    # 2. Status reconciliation
    status_counts = core["status"].value_counts().to_dict()
    assert status_counts["resolved"] == 10007
    assert status_counts["closed"] == 1057
    assert status_counts["open"] == 332
    assert status_counts["pending"] == 245
    assert (status_counts["open"] + status_counts["pending"]) == 577

    # 3. Repeat contact reconciliation (3,079 tickets, ₹8,44,250.00)
    repeats = core[core["is_repeat_contact_30d"] == True]
    assert len(repeats) == 3079

    channel_rates = {"chat": 210.0, "email": 260.0, "voice": 520.0, "social": 240.0}
    repeat_cost = sum(len(repeats[repeats["channel"].str.lower() == ch]) * rate for ch, rate in channel_rates.items())
    assert repeat_cost == 844250.0


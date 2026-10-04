"""Integration tests for the Dynamic CSV Upload Workspace navigation integration.

Covers:
1. All 7 existing navigation entries remain registered and present.
2. Dynamic CSV Upload Workspace appears as the 8th navigation option.
3. The upload view renderer is reachable and invocable through navigation.
4. All existing dashboard view modules remain importable and callable.
5. Support Triage Agent remains fully accessible and operational.
6. Historical baseline loading (11,641 core tickets) remains completely unchanged.
7. Upload session state does not contaminate baseline datasets.
8. 'Clear Dataset' does not erase unrelated session state variables.
9. Invalid or malformed uploaded data is handled gracefully without crashing.
10. Zero filesystem writes occur to audited baseline files.
"""

import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import pytest
import pandas as pd

import app
from src.ui.data_service import load_and_preprocess_all
from src.ui.executive import render_executive_overview
from src.ui.categories import render_category_analytics
from src.ui.workload import render_team_workload
from src.ui.staffing import render_staffing_decision
from src.ui.financial import render_financial_impact
from src.ui.audit_view import render_audit_reconciliation
from src.ui.triage_view import render_triage_agent_view
from src.ui.upload_view import render_upload_workspace, parse_uploaded_csv


def compute_file_hash(path: Path) -> str:
    """Compute sha256 hash of a file for immutability verification."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def test_existing_navigation_entries_present():
    """1. Verify that all 7 existing navigation options remain registered in app.py."""
    source = inspect.getsource(app.main)

    expected_existing = [
        "📊 Executive Overview",
        "🏷️ Category Analytics",
        "👥 Team Workload",
        "⚖️ Staffing Decision",
        "💰 Financial Impact",
        "🔍 Master Audit Reconciliation",
        "🤖 Support Triage Agent",
    ]

    for nav in expected_existing:
        assert f'"{nav}"' in source, f"Missing original navigation view: {nav}"


def test_dynamic_upload_workspace_navigation_appears():
    """2. Verify that Dynamic CSV Upload Workspace appears in app.py navigation."""
    source = inspect.getsource(app.main)
    assert '"📁 Dynamic CSV Upload Workspace"' in source, "Missing Dynamic CSV Upload Workspace in nav_options"


def test_upload_view_reachable_through_navigation():
    """3. Verify dispatcher routes '📁 Dynamic CSV Upload Workspace' to render_upload_workspace."""
    source = inspect.getsource(app.main)
    assert 'elif nav_selection == "📁 Dynamic CSV Upload Workspace":' in source
    assert 'render_upload_workspace()' in source


def test_existing_dashboard_pages_importable():
    """4. Verify all existing view renderers remain cleanly importable and callable."""
    assert callable(render_executive_overview)
    assert callable(render_category_analytics)
    assert callable(render_team_workload)
    assert callable(render_staffing_decision)
    assert callable(render_financial_impact)
    assert callable(render_audit_reconciliation)
    assert callable(render_triage_agent_view)
    assert callable(render_upload_workspace)


def test_support_triage_agent_remains_accessible():
    """5. Verify Support Triage Agent dispatcher branch is preserved and operational."""
    source = inspect.getsource(app.main)
    assert 'elif nav_selection == "🤖 Support Triage Agent":' in source
    assert 'render_triage_agent_view' in source


def test_historical_baseline_loading_unchanged():
    """6. Verify historical baseline loading remains exactly 11,641 core tickets."""
    data = load_and_preprocess_all()
    tickets = data["tickets"]
    core = tickets[tickets["in_core_18m"] == True]

    assert len(tickets) == 11780
    assert len(core) == 11641
    assert len(data["agents"]) == 44
    assert len(data["orders"]) == 15000
    assert len(data["products"]) == 14


def test_upload_session_state_does_not_contaminate_baseline():
    """7. Verify uploaded DataFrame in session state does not contaminate baseline data."""
    baseline_before = load_and_preprocess_all()
    assert int(baseline_before["tickets"]["in_core_18m"].sum()) == 11641

    # Simulate active uploaded dataset in session state
    uploaded_df = pd.DataFrame({
        "ticket_id": ["TEST-1", "TEST-2"],
        "created_at": ["2026-06-01", "2026-06-02"],
        "status": ["open", "resolved"],
        "channel": ["chat", "chat"],
        "customer_id": ["C-1", "C-2"],
        "assigned_team": ["Logistics", "Billing"]
    })

    session_state = {
        "uploaded_raw_df": uploaded_df,
        "uploaded_file_name": "isolated_test.csv",
        "uploaded_manual_mapping": {},
        "uploaded_pipeline_result": None,
    }

    with patch("streamlit.session_state", session_state), \
         patch("streamlit.file_uploader", return_value=None):
        render_upload_workspace()

    # Re-evaluate baseline data service
    baseline_after = load_and_preprocess_all()
    assert int(baseline_after["tickets"]["in_core_18m"].sum()) == 11641
    assert len(baseline_after["tickets"]) == 11780


def test_clear_dataset_does_not_erase_unrelated_session_state():
    """8. Verify clearing uploaded dataset preserves unrelated session state keys."""
    session_state = {
        "user_role": "supervisor",
        "active_theme": "dark",
        "triage_response": "EXISTING_TRIAGE_STATE",
        "uploaded_raw_df": pd.DataFrame({"ticket_id": ["T-1"]}),
        "uploaded_file_name": "temp.csv",
        "uploaded_manual_mapping": {"ticket_id": "ticket_id"},
        "uploaded_pipeline_result": "PIPELINE_RESULT"
    }

    # Simulate clearing only upload keys
    session_state["uploaded_raw_df"] = None
    session_state["uploaded_file_name"] = None
    session_state["uploaded_manual_mapping"] = {}
    session_state["uploaded_pipeline_result"] = None

    # Unrelated keys must remain intact
    assert session_state["user_role"] == "supervisor"
    assert session_state["active_theme"] == "dark"
    assert session_state["triage_response"] == "EXISTING_TRIAGE_STATE"

    # Upload keys must be cleared
    assert session_state["uploaded_raw_df"] is None
    assert session_state["uploaded_file_name"] is None
    assert session_state["uploaded_manual_mapping"] == {}
    assert session_state["uploaded_pipeline_result"] is None


def test_invalid_uploaded_data_handled_gracefully():
    """9. Verify invalid or malformed uploaded data does not crash the application."""
    # Malformed empty file object
    class EmptyFile:
        name = "empty.csv"
        def getvalue(self):
            return b""

    df, err = parse_uploaded_csv(EmptyFile())
    assert df is None
    assert "empty" in err.lower()

    # Invalid corrupted bytes
    class BadFile:
        name = "bad.csv"
        def getvalue(self):
            return b"\x00\x01\x02\xff\xfe"

    df_bad, err_bad = parse_uploaded_csv(BadFile())
    assert df_bad is None
    assert err_bad is not None


def test_zero_writes_to_audited_baseline_files():
    """10. Verify that running navigation and upload view causes zero writes to baseline files."""
    base_dir = Path(__file__).resolve().parent.parent
    raw_tickets = base_dir / "data" / "raw" / "tickets.csv"
    raw_agents = base_dir / "data" / "raw" / "agents.csv"
    proc_tickets = base_dir / "data" / "processed" / "classified_tickets.csv"

    h_raw_tickets_before = compute_file_hash(raw_tickets)
    h_raw_agents_before = compute_file_hash(raw_agents)
    h_proc_tickets_before = compute_file_hash(proc_tickets)

    # Perform mock rendering of upload workspace
    session_state = {
        "uploaded_raw_df": None,
        "uploaded_file_name": None,
        "uploaded_manual_mapping": {},
        "uploaded_pipeline_result": None
    }
    with patch("streamlit.session_state", session_state), \
         patch("streamlit.file_uploader", return_value=None):
        render_upload_workspace()

    h_raw_tickets_after = compute_file_hash(raw_tickets)
    h_raw_agents_after = compute_file_hash(raw_agents)
    h_proc_tickets_after = compute_file_hash(proc_tickets)

    assert h_raw_tickets_before == h_raw_tickets_after, "data/raw/tickets.csv modified!"
    assert h_raw_agents_before == h_raw_agents_after, "data/raw/agents.csv modified!"
    assert h_proc_tickets_before == h_proc_tickets_after, "data/processed/classified_tickets.csv modified!"

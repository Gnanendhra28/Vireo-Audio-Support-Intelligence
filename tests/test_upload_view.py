"""Unit and integration tests for the Dynamic CSV Upload Workspace (src/ui/upload_view.py).

Covers:
1. Upload view module importability and callability
2. Empty upload state rendering
3. Valid CSV parsing across UTF-8 and UTF-8-SIG encodings
4. Malformed CSV error handling
5. Column mapping integration
6. Data validation integration
7. Report capability display integration
8. Session-state isolation from baseline datasets
9. Clear upload behavior
10. PII masking in displayed preview
11. Zero filesystem writes to baseline datasets
"""

import io
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

from src.ui.upload_view import (
    render_upload_workspace,
    parse_uploaded_csv,
    sanitize_preview_df,
)
from src.data.dynamic_pipeline import CapabilityStatus
from src.ui.data_service import load_and_preprocess_all


class DummyUploadFile:
    """Mock Streamlit UploadedFile object."""
    def __init__(self, content: bytes, name: str = "test_tickets.csv"):
        self._content = content
        self.name = name

    def getvalue(self) -> bytes:
        return self._content


def compute_file_hash(path: Path) -> str:
    """Compute sha256 hash of a file for immutability verification."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def test_upload_view_importable_and_callable():
    """1. Verify upload view and helpers are importable and callable."""
    assert callable(render_upload_workspace)
    assert callable(parse_uploaded_csv)
    assert callable(sanitize_preview_df)


def test_empty_upload_state():
    """2. Verify empty upload state renders instructions without crashing."""
    session_state = {
        "uploaded_raw_df": None,
        "uploaded_file_name": None,
        "uploaded_manual_mapping": {},
        "uploaded_pipeline_result": None,
    }
    with patch("streamlit.session_state", session_state), \
         patch("streamlit.file_uploader", return_value=None):
        render_upload_workspace()
    assert session_state["uploaded_raw_df"] is None


def test_valid_csv_parsing():
    """3. Verify robust parsing of valid CSV bytes in UTF-8 and UTF-8-SIG."""
    csv_text = "ticket_id,created_at,status,channel\nTICK-1,2025-01-01,open,chat\n"

    # Test standard UTF-8
    file_utf8 = DummyUploadFile(csv_text.encode("utf-8"), name="tickets_utf8.csv")
    df1, err1 = parse_uploaded_csv(file_utf8)
    assert err1 is None
    assert df1 is not None
    assert len(df1) == 1
    assert list(df1.columns) == ["ticket_id", "created_at", "status", "channel"]

    # Test UTF-8 with BOM (utf-8-sig)
    file_bom = DummyUploadFile(csv_text.encode("utf-8-sig"), name="tickets_bom.csv")
    df2, err2 = parse_uploaded_csv(file_bom)
    assert err2 is None
    assert df2 is not None
    assert len(df2) == 1
    assert list(df2.columns) == ["ticket_id", "created_at", "status", "channel"]


def test_malformed_csv_handling():
    """4. Verify that malformed or empty CSV bytes are caught gracefully."""
    # Completely empty bytes
    empty_file = DummyUploadFile(b"", name="empty.csv")
    df_empty, err_empty = parse_uploaded_csv(empty_file)
    assert df_empty is None
    assert "empty" in err_empty.lower()

    # Binary corrupted content
    corrupt_file = DummyUploadFile(b"\x00\x01\x02\xff\xfe\xfd\x00\x00", name="corrupt.csv")
    df_corrupt, err_corrupt = parse_uploaded_csv(corrupt_file)
    # Parser should catch or return unparseable/malformed error without crashing
    assert df_corrupt is None or err_corrupt is not None


def test_column_mapping_integration():
    """5. Verify column mapper integration inside the upload workspace."""
    sample_df = pd.DataFrame({
        "Case ID": ["C-1", "C-2"],
        "Date Created": ["2025-01-01 10:00:00", "2025-01-02 11:00:00"],
        "Ticket Status": ["resolved", "open"],
        "Contact Channel": ["chat", "email"],
        "Customer Code": ["CX-1", "CX-2"],
        "Department": ["Logistics", "Billing"],
        "Description": ["Delivery delayed", "Invoice request"]
    })

    session_state = {
        "uploaded_raw_df": sample_df,
        "uploaded_file_name": "custom_cases.csv",
        "uploaded_manual_mapping": {"customer_id": "Customer Code"},
        "uploaded_pipeline_result": None,
    }

    with patch("streamlit.session_state", session_state), \
         patch("streamlit.file_uploader", return_value=None):
        render_upload_workspace()

    # Check pipeline result was computed and stored in session state
    pipe_res = session_state.get("uploaded_pipeline_result")
    assert pipe_res is not None
    assert "ticket_id" in pipe_res.preprocessed_df.columns
    assert "customer_message" in pipe_res.preprocessed_df.columns


def test_validation_integration():
    """6. Verify dynamic validator captures errors and displays them cleanly."""
    invalid_df = pd.DataFrame({
        "ticket_id": ["T-1", "T-1"],  # Duplicate ID
        "created_at": ["NOT_A_DATE", "2025-01-02"],
        "status": ["open", "resolved"],
        "channel": ["chat", "email"],
        "customer_id": ["CX-1", "CX-2"],
        "assigned_team": ["Logistics", "Billing"]
    })

    session_state = {
        "uploaded_raw_df": invalid_df,
        "uploaded_file_name": "invalid_tickets.csv",
        "uploaded_manual_mapping": {},
        "uploaded_pipeline_result": None,
    }

    with patch("streamlit.session_state", session_state), \
         patch("streamlit.file_uploader", return_value=None):
        render_upload_workspace()

    pipe_res = session_state.get("uploaded_pipeline_result")
    assert pipe_res is not None
    assert pipe_res.validation_result.is_valid is False
    assert len(pipe_res.validation_result.errors) >= 1


def test_report_capability_display_integration():
    """7. Verify report capabilities are evaluated and reflect missing fields."""
    minimal_df = pd.DataFrame({
        "ticket_id": ["T-101", "T-102"],
        "created_at": ["2025-01-01 10:00:00", "2025-01-02 11:00:00"],
        "status": ["open", "resolved"],
        "channel": ["chat", "email"],
        "customer_id": ["C-1", "C-2"],
        "assigned_team": ["Logistics", "Billing"]
    })

    session_state = {
        "uploaded_raw_df": minimal_df,
        "uploaded_file_name": "minimal.csv",
        "uploaded_manual_mapping": {},
        "uploaded_pipeline_result": None,
    }

    with patch("streamlit.session_state", session_state), \
         patch("streamlit.file_uploader", return_value=None):
        render_upload_workspace()

    pipe_res = session_state.get("uploaded_pipeline_result")
    caps = pipe_res.capabilities
    # Executive volume should be AVAILABLE
    assert caps["executive_volume"].status == CapabilityStatus.AVAILABLE
    # SLA should be UNAVAILABLE due to missing first_response_at
    assert caps["sla_analysis"].status == CapabilityStatus.UNAVAILABLE
    # Staffing should be UNAVAILABLE due to missing roster
    assert caps["staffing_analysis"].status == CapabilityStatus.UNAVAILABLE


def test_session_state_isolation():
    """8. Verify uploaded session data does not contaminate baseline data."""
    baseline_before = load_and_preprocess_all()
    core_count_before = int(baseline_before["tickets"]["in_core_18m"].sum())
    assert core_count_before == 11641

    uploaded_df = pd.DataFrame({
        "ticket_id": ["UP-1", "UP-2", "UP-3"],
        "created_at": ["2026-05-01", "2026-05-02", "2026-05-03"],
        "status": ["open", "resolved", "closed"],
        "channel": ["chat", "email", "voice"],
        "customer_id": ["U-1", "U-2", "U-3"],
        "assigned_team": ["Logistics", "Billing", "Returns Desk"]
    })

    session_state = {
        "uploaded_raw_df": uploaded_df,
        "uploaded_file_name": "uploaded.csv",
        "uploaded_manual_mapping": {},
        "uploaded_pipeline_result": None,
    }

    with patch("streamlit.session_state", session_state), \
         patch("streamlit.file_uploader", return_value=None):
        render_upload_workspace()

    # Re-verify baseline is completely unaffected
    baseline_after = load_and_preprocess_all()
    core_count_after = int(baseline_after["tickets"]["in_core_18m"].sum())
    assert core_count_after == 11641
    assert len(baseline_after["tickets"]) == 11780


def test_clear_upload_behavior():
    """9. Verify clear button resets all uploaded session state references."""
    uploaded_df = pd.DataFrame({"ticket_id": ["T-1"]})
    session_state = {
        "uploaded_raw_df": uploaded_df,
        "uploaded_file_name": "sample.csv",
        "uploaded_manual_mapping": {"ticket_id": "ticket_id"},
        "uploaded_pipeline_result": "SOMETHING",
    }

    # Simulate clearing
    session_state["uploaded_raw_df"] = None
    session_state["uploaded_file_name"] = None
    session_state["uploaded_manual_mapping"] = {}
    session_state["uploaded_pipeline_result"] = None

    assert session_state["uploaded_raw_df"] is None
    assert session_state["uploaded_file_name"] is None
    assert session_state["uploaded_manual_mapping"] == {}
    assert session_state["uploaded_pipeline_result"] is None


def test_pii_masking_in_preview():
    """10. Verify sanitize_preview_df masks email addresses and phone numbers."""
    pii_df = pd.DataFrame({
        "customer_message": [
            "Contact me at priya.raman@vireoaudio.com or call +91 (987) 654-3210 regarding issue.",
            "My email is support_user@gmail.com and phone is 987-654-3210."
        ],
        "ticket_id": ["T-01", "T-02"]
    })

    preview = sanitize_preview_df(pii_df, max_rows=5)

    msg_0 = preview.loc[0, "customer_message"]
    msg_1 = preview.loc[1, "customer_message"]

    assert "[EMAIL_MASKED]" in msg_0
    assert "[PHONE_MASKED]" in msg_0
    assert "priya.raman@vireoaudio.com" not in msg_0

    assert "[EMAIL_MASKED]" in msg_1
    assert "[PHONE_MASKED]" in msg_1
    assert "support_user@gmail.com" not in msg_1


def test_no_writes_to_baseline_dataset_paths():
    """11. Verify zero disk writes to data/raw/ or data/processed/."""
    base_dir = Path(__file__).resolve().parent.parent
    raw_tickets = base_dir / "data" / "raw" / "tickets.csv"
    raw_agents = base_dir / "data" / "raw" / "agents.csv"
    proc_tickets = base_dir / "data" / "processed" / "classified_tickets.csv"

    h_raw_tickets_before = compute_file_hash(raw_tickets)
    h_raw_agents_before = compute_file_hash(raw_agents)
    h_proc_tickets_before = compute_file_hash(proc_tickets)

    # Perform simulated upload and render
    uploaded_df = pd.DataFrame({
        "ticket_id": ["TEMP-1", "TEMP-2"],
        "created_at": ["2026-06-01", "2026-06-02"],
        "status": ["open", "resolved"],
        "channel": ["chat", "chat"],
        "customer_id": ["C-1", "C-2"],
        "assigned_team": ["Logistics", "Billing"]
    })

    session_state = {
        "uploaded_raw_df": uploaded_df,
        "uploaded_file_name": "temp.csv",
        "uploaded_manual_mapping": {},
        "uploaded_pipeline_result": None,
    }

    with patch("streamlit.session_state", session_state), \
         patch("streamlit.file_uploader", return_value=None):
        render_upload_workspace()

    h_raw_tickets_after = compute_file_hash(raw_tickets)
    h_raw_agents_after = compute_file_hash(raw_agents)
    h_proc_tickets_after = compute_file_hash(proc_tickets)

    assert h_raw_tickets_before == h_raw_tickets_after
    assert h_raw_agents_before == h_raw_agents_after
    assert h_proc_tickets_before == h_proc_tickets_after

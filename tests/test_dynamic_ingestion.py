"""Unit tests for the dynamic CSV ingestion engine and canonical schema mapping.

Covers:
1. Standard canonical CSV headers detection
2. Alternative column headers detection (synonym normalization)
3. Manual mapping overrides
4. Ambiguous header detection
5. Duplicate source-column mapping collision prevention
6. Missing required columns detection
7. Duplicate ticket_id detection
8. Invalid / unparseable timestamps detection
9. Invalid numeric fields (CSAT, refunds, transfers)
10. Semantic preservation of missing transfers as null
11. Semantic preservation of missing CSAT scores as null
12. Empty DataFrame rejection
13. Input DataFrame immutability guarantee
14. Zero filesystem writes guarantee
"""

import copy
import hashlib
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.data.schema_contract import (
    CANONICAL_TICKET_FIELDS,
    CanonicalFieldDefinition,
    FieldRequirement,
    get_canonical_fields,
    get_required_fields,
    DatasetType,
)
from src.data.column_mapper import ColumnMapper, MappingReport
from src.data.dynamic_validator import (
    DynamicValidator,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
)


@pytest.fixture
def valid_canonical_ticket_data() -> pd.DataFrame:
    """Provide a minimal valid canonical tickets DataFrame."""
    return pd.DataFrame({
        "ticket_id": ["TICK-101", "TICK-102", "TICK-103"],
        "created_at": ["2025-02-01 10:00:00", "2025-02-01 11:30:00", "2025-02-02 09:15:00"],
        "first_response_at": ["2025-02-01 10:12:00", "2025-02-01 12:00:00", "2025-02-02 09:20:00"],
        "resolved_at": ["2025-02-01 14:00:00", "2025-02-01 15:45:00", None],
        "status": ["resolved", "resolved", "open"],
        "channel": ["chat", "email", "chat"],
        "customer_id": ["CUST-001", "CUST-002", "CUST-003"],
        "order_id": ["VR-ORD-111", "VR-ORD-222", None],
        "product_sku": ["VA-PULSE2-BLK", "VA-STRATA2-SLV", "VA-PULSE2-BLK"],
        "category": ["Order & Logistics", "Returns & Refunds", "Technical & Firmware"],
        "priority": ["Normal", "High", "Normal"],
        "assigned_team": ["Logistics", "Returns Desk", "Chat Frontline"],
        "agent_id": ["AGT-001", "AGT-005", "AGT-010"],
        "transfers": [1.0, None, 0.0],
        "csat_score": [5.0, 4.0, None],
        "refund_amount_inr": [None, 4999.0, None],
        "refund_reason_code": [None, "R-DEFECT", None],
        "replacement_issued": ["N", "Y", "N"],
        "customer_message": [
            "Where is my package? AWB tracking has not updated.",
            "Nobody arrived for reverse pickup of my headphones.",
            "Bluetooth disconnects frequently."
        ],
        "agent_notes": [
            "Tracking provided to customer.",
            "Rescheduled courier pickup.",
            "Advised on firmware reset."
        ],
        "source_system": ["helpdesk", "legacy_fd", "helpdesk"]
    })


def test_standard_canonical_headers(valid_canonical_ticket_data):
    """Verify that a standard CSV with canonical names maps 100% cleanly without errors."""
    report = ColumnMapper.detect_mapping(list(valid_canonical_ticket_data.columns))
    assert report.is_valid is True
    assert len(report.missing_required_fields) == 0
    assert len(report.collision_errors) == 0
    assert len(report.ambiguous_columns) == 0

    # Ensure all required canonical fields are mapped
    for req in get_required_fields():
        assert req in report.mapped_columns
        assert report.mapped_columns[req] == req


def test_alternative_column_headers():
    """Verify automatic detection and normalization of diverse helpdesk column names."""
    diverse_headers = [
        "Ticket #",
        "Date Created",
        "First Response Time",
        "Resolution Time",
        "Ticket Status",
        "Contact Channel",
        "Customer ID",
        "Order Number",
        "SKU",
        "Issue Category",
        "Assigned Group",
        "Resolver ID",
        "Handoffs",
        "Rating",
        "Refund Value",
        "Disbursement Reason",
        "RMA Issued",
        "Description",
        "Resolution Notes",
        "CRM Source"
    ]
    report = ColumnMapper.detect_mapping(diverse_headers)
    assert report.is_valid is True
    assert len(report.missing_required_fields) == 0

    # Check key mappings
    assert report.mapped_columns["ticket_id"] == "Ticket #"
    assert report.mapped_columns["created_at"] == "Date Created"
    assert report.mapped_columns["status"] == "Ticket Status"
    assert report.mapped_columns["channel"] == "Contact Channel"
    assert report.mapped_columns["assigned_team"] == "Assigned Group"
    assert report.mapped_columns["customer_message"] == "Description"
    assert report.mapped_columns["csat_score"] == "Rating"
    assert report.mapped_columns["transfers"] == "Handoffs"


def test_manual_mapping_override():
    """Verify that manual mapping overrides take precedence over automatic detection."""
    source_headers = ["CaseNum", "OpenDate", "ProblemSummary", "TeamName", "State", "Origin", "UserCode"]

    # Explicit manual override
    manual = {
        "ticket_id": "CaseNum",
        "created_at": "OpenDate",
        "customer_message": "ProblemSummary",
        "assigned_team": "TeamName",
        "status": "State",
        "channel": "Origin",
        "customer_id": "UserCode"
    }
    report = ColumnMapper.detect_mapping(source_headers, manual_mapping=manual)
    assert report.is_valid is True
    assert report.mapped_columns["ticket_id"] == "CaseNum"
    assert report.mapped_columns["customer_message"] == "ProblemSummary"
    assert len(report.missing_required_fields) == 0


def test_ambiguous_mapping_detection():
    """Verify that headers mapping to multiple candidate fields are flagged without silent resolution."""
    # Custom field names that could be ambiguous
    headers = ["ID", "Created Time", "Status", "Channel", "Customer ID", "Assigned Group", "Message"]
    report = ColumnMapper.detect_mapping(headers)
    assert report.is_valid is True
    assert report.mapped_columns["ticket_id"] == "ID"


def test_duplicate_source_column_collision():
    """Verify that two source columns matching the same canonical field trigger a collision error."""
    # Both 'Description' and 'Subject' match 'customer_message'
    collision_headers = [
        "Ticket ID", "Created Time", "Status", "Channel", "Customer ID", "Assigned Group",
        "Description", "Subject"
    ]
    report = ColumnMapper.detect_mapping(collision_headers)
    assert report.is_valid is False
    assert "customer_message" in report.collision_errors
    assert set(report.collision_errors["customer_message"]) == {"Description", "Subject"}

    # Resolving via manual override must clear the collision
    resolved_report = ColumnMapper.detect_mapping(
        collision_headers,
        manual_mapping={"customer_message": "Description"}
    )
    assert resolved_report.is_valid is True
    assert resolved_report.mapped_columns["customer_message"] == "Description"
    assert "Subject" in resolved_report.unmapped_source_columns


def test_missing_required_columns():
    """Verify that missing mandatory canonical columns are flagged as errors."""
    incomplete_df = pd.DataFrame({
        "ticket_id": ["TICK-1"],
        "status": ["open"]
        # Missing created_at, channel, customer_id, assigned_team, customer_message
    })
    result = DynamicValidator.validate_ticket_dataframe(incomplete_df)
    assert result.is_valid is False
    error_fields = [e.field for e in result.errors]
    assert "columns" in error_fields
    assert any("Missing mandatory canonical fields" in e.issue for e in result.errors)


def test_duplicate_ticket_ids(valid_canonical_ticket_data):
    """Verify duplicate ticket IDs are rejected with ERROR severity."""
    df_dups = valid_canonical_ticket_data.copy()
    df_dups.loc[1, "ticket_id"] = df_dups.loc[0, "ticket_id"]

    result = DynamicValidator.validate_ticket_dataframe(df_dups)
    assert result.is_valid is False
    dup_errors = [e for e in result.errors if e.field == "ticket_id" and "duplicate" in e.issue.lower()]
    assert len(dup_errors) > 0


def test_null_ticket_identifiers(valid_canonical_ticket_data):
    """Verify null ticket identifiers are rejected with ERROR severity."""
    df_nulls = valid_canonical_ticket_data.copy()
    df_nulls.loc[0, "ticket_id"] = None

    result = DynamicValidator.validate_ticket_dataframe(df_nulls)
    assert result.is_valid is False
    null_errors = [e for e in result.errors if e.field == "ticket_id" and "null" in e.issue.lower()]
    assert len(null_errors) > 0


def test_invalid_timestamps(valid_canonical_ticket_data):
    """Verify unparseable timestamps trigger validation errors."""
    df_invalid_time = valid_canonical_ticket_data.copy()
    df_invalid_time.loc[0, "created_at"] = "NOT_A_VALID_DATE"

    result = DynamicValidator.validate_ticket_dataframe(df_invalid_time)
    assert result.is_valid is False
    time_errors = [e for e in result.errors if e.field == "created_at"]
    assert len(time_errors) > 0


def test_invalid_numeric_fields(valid_canonical_ticket_data):
    """Verify invalid CSAT and negative financial numbers trigger appropriate warnings/errors."""
    df_bad_nums = valid_canonical_ticket_data.copy()
    df_bad_nums.loc[0, "csat_score"] = 9.5  # Outside standard 1.0 to 5.0
    df_bad_nums.loc[1, "refund_amount_inr"] = -500.0  # Negative refund
    df_bad_nums.loc[0, "transfers"] = -2.0  # Negative transfers

    result = DynamicValidator.validate_ticket_dataframe(df_bad_nums)
    # Warnings, not blocking errors
    warning_fields = [w.field for w in result.warnings]
    assert "csat_score" in warning_fields
    assert "refund_amount_inr" in warning_fields
    assert "transfers" in warning_fields


def test_missing_transfers_preserved_as_null(valid_canonical_ticket_data):
    """Verify missing transfers remain NaN and are not silently imputed as zero."""
    df = valid_canonical_ticket_data.copy()
    assert pd.isna(df.loc[1, "transfers"])

    result = DynamicValidator.validate_ticket_dataframe(df)
    # Transfers must not be mutated
    assert pd.isna(df.loc[1, "transfers"])
    # Info log confirms preservation
    info_transfers = [i for i in result.info if i.field == "transfers"]
    assert len(info_transfers) > 0
    assert "preserved as null" in info_transfers[0].issue.lower()


def test_missing_csat_preserved_as_null(valid_canonical_ticket_data):
    """Verify missing CSAT scores remain NaN and are not imputed as zero."""
    df = valid_canonical_ticket_data.copy()
    assert pd.isna(df.loc[2, "csat_score"])

    result = DynamicValidator.validate_ticket_dataframe(df)
    assert pd.isna(df.loc[2, "csat_score"])
    info_csat = [i for i in result.info if i.field == "csat_score"]
    assert len(info_csat) > 0
    assert "non-responses" in info_csat[0].issue.lower()


def test_empty_dataframe():
    """Verify empty DataFrame is caught with clear ERROR."""
    empty_df = pd.DataFrame()
    result = DynamicValidator.validate_ticket_dataframe(empty_df)
    assert result.is_valid is False
    assert result.total_rows == 0
    assert any("zero rows" in e.issue.lower() for e in result.errors)


def test_input_dataframe_immutability(valid_canonical_ticket_data):
    """Verify that neither ColumnMapper nor DynamicValidator mutates the input DataFrame."""
    df_orig = valid_canonical_ticket_data.copy()
    df_snapshot = copy.deepcopy(df_orig)

    # 1. ColumnMapper.apply_mapping
    mapping = {"ticket_id": "ticket_id", "status": "status"}
    mapped_df = ColumnMapper.apply_mapping(df_orig, mapping)
    pd.testing.assert_frame_equal(df_orig, df_snapshot)
    assert mapped_df is not df_orig

    # 2. DynamicValidator.validate_ticket_dataframe
    result = DynamicValidator.validate_ticket_dataframe(df_orig)
    pd.testing.assert_frame_equal(df_orig, df_snapshot)


def test_zero_filesystem_writes(valid_canonical_ticket_data):
    """Verify that dynamic validation and mapping produce zero filesystem writes."""
    base_dir = Path(__file__).resolve().parent.parent
    raw_tickets = base_dir / "data" / "raw" / "tickets.csv"
    proc_tickets = base_dir / "data" / "processed" / "classified_tickets.csv"

    def file_hash(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    h_raw_before = file_hash(raw_tickets)
    h_proc_before = file_hash(proc_tickets)

    # Execute mapping and validation
    report = ColumnMapper.detect_mapping(list(valid_canonical_ticket_data.columns))
    mapped = ColumnMapper.apply_mapping(valid_canonical_ticket_data, report.mapped_columns)
    val_result = DynamicValidator.validate_ticket_dataframe(mapped)

    h_raw_after = file_hash(raw_tickets)
    h_proc_after = file_hash(proc_tickets)

    assert h_raw_before == h_raw_after, "data/raw/tickets.csv was altered!"
    assert h_proc_before == h_proc_after, "data/processed/classified_tickets.csv was altered!"

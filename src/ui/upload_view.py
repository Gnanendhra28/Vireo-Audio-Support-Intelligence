"""Dynamic CSV Upload Workspace for Streamlit.

Provides an isolated, in-memory workspace for support managers to upload custom
ticket CSV files, audit and customize canonical column mappings, inspect data
validation reports, review PII-sanitized previews, and evaluate report capabilities.

Strictly isolated from the audited 18-month baseline. Never writes to disk.
"""

import io
import re
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
import streamlit as st

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
from src.data.dynamic_pipeline import (
    DynamicPipeline,
    CapabilityStatus,
    ReportCapability,
    DynamicPipelineResult,
)


# PII masking patterns for secure in-memory previews
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")


def sanitize_preview_df(df: pd.DataFrame, max_rows: int = 10, max_str_len: int = 120) -> pd.DataFrame:
    """Create a sanitized, PII-masked preview copy of the DataFrame for UI rendering.

    Does not modify the underlying analytical DataFrame.

    Args:
        df: Input DataFrame.
        max_rows: Number of rows to include in the preview.
        max_str_len: Max character length for previewing long text.

    Returns:
        PII-sanitized DataFrame slice.
    """
    preview = df.head(max_rows).copy()

    for col in preview.columns:
        if preview[col].dtype == "object" or pd.api.types.is_string_dtype(preview[col]):
            # Mask emails and phones
            def _mask(val: Any) -> Any:
                if pd.isna(val) or val is None:
                    return val
                s = str(val)
                s = EMAIL_PATTERN.sub("[EMAIL_MASKED]", s)
                s = PHONE_PATTERN.sub("[PHONE_MASKED]", s)
                if len(s) > max_str_len:
                    s = s[:max_str_len] + "..."
                return s

            preview[col] = preview[col].apply(_mask)

    return preview


def parse_uploaded_csv(uploaded_file: Any) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Safely parse uploaded CSV bytes in memory across multiple common encodings.

    Args:
        uploaded_file: Streamlit UploadedFile object or binary buffer.

    Returns:
        Tuple of (Parsed DataFrame or None, Error message or None).
    """
    try:
        raw_bytes = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
    except Exception as e:
        return None, f"Could not read uploaded file content: {str(e)}"

    if not raw_bytes or len(raw_bytes.strip()) == 0:
        return None, "Uploaded CSV file is completely empty."

    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    for enc in encodings:
        try:
            content = raw_bytes.decode(enc)
            # Binary data with null bytes is not a valid text CSV
            if "\x00" in content:
                continue
            df = pd.read_csv(io.StringIO(content))
            if df.empty or len(df) == 0 or len(df.columns) == 0:
                continue
            return df, None
        except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError):
            continue
        except Exception as e:
            return None, f"Malformed CSV structure: {str(e)}"

    return None, "Failed to parse CSV. Ensure file is a valid non-empty CSV formatted in UTF-8 or standard text encoding."


def render_upload_workspace() -> None:
    """Render the Interactive Dynamic CSV Upload Workspace."""
    st.header("📁 Dynamic Dataset Ingestion & Validation Workspace")
    st.markdown(
        "Upload and evaluate external support ticket CSV datasets in an isolated session workspace. "
        "Review automatic canonical column mapping, inspect data quality validation, and evaluate "
        "analytical report capabilities without altering the audited baseline."
    )

    # Operational Safety Banner
    st.info(
        "🛡️ **Session Isolation & Zero-Persistence Guarantee:**\n\n"
        "- **In-Memory Only:** Uploaded data is parsed and evaluated entirely in transient session memory. No data is written to disk or database tables.\n"
        "- **Baseline Protection:** The audited 18-month historical baseline (`data/raw/` and `data/processed/`) remains completely untouched.\n"
        "- **Capability Gating:** Reports with missing mandatory fields are marked **Unavailable** and are never populated with fabricated zeros."
    )

    # Initialize Session State Keys
    if "uploaded_raw_df" not in st.session_state:
        st.session_state["uploaded_raw_df"] = None
    if "uploaded_file_name" not in st.session_state:
        st.session_state["uploaded_file_name"] = None
    if "uploaded_manual_mapping" not in st.session_state:
        st.session_state["uploaded_manual_mapping"] = {}
    if "uploaded_pipeline_result" not in st.session_state:
        st.session_state["uploaded_pipeline_result"] = None

    # -------------------------------------------------------------------------
    # SECTION A: Dataset Upload
    # -------------------------------------------------------------------------
    st.subheader("📤 A. In-Memory Dataset Upload")

    uploader_col, action_col = st.columns([3, 1])

    with uploader_col:
        uploaded_file = st.file_uploader(
            "Choose a Support Tickets CSV File:",
            type=["csv"],
            help="Upload a CSV containing customer support tickets (e.g. Zendesk, Freshdesk, or Salesforce Service Cloud export)."
        )

    with action_col:
        st.write("")
        st.write("")
        if st.session_state["uploaded_raw_df"] is not None:
            if st.button("🗑️ Clear Dataset", use_container_width=True):
                st.session_state["uploaded_raw_df"] = None
                st.session_state["uploaded_file_name"] = None
                st.session_state["uploaded_manual_mapping"] = {}
                st.session_state["uploaded_pipeline_result"] = None
                st.rerun()

    # Process new file upload
    if uploaded_file is not None:
        if st.session_state["uploaded_file_name"] != uploaded_file.name:
            parsed_df, err_msg = parse_uploaded_csv(uploaded_file)
            if err_msg:
                st.error(f"❌ {err_msg}")
                return
            st.session_state["uploaded_raw_df"] = parsed_df
            st.session_state["uploaded_file_name"] = uploaded_file.name
            st.session_state["uploaded_manual_mapping"] = {}
            st.session_state["uploaded_pipeline_result"] = None

    raw_df: Optional[pd.DataFrame] = st.session_state.get("uploaded_raw_df")
    file_name: Optional[str] = st.session_state.get("uploaded_file_name")

    if raw_df is None:
        st.info("👆 Select a CSV file above to begin dynamic column mapping and capability audit.")
        return

    # Display file metadata metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Active Filename", file_name)
    m2.metric("Row Count", f"{len(raw_df):,} rows")
    m3.metric("Column Count", f"{len(raw_df.columns)} columns")

    # -------------------------------------------------------------------------
    # SECTION B: Automatic & Manual Column Mapping
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("🏷️ B. Canonical Column Mapping & Header Detection")
    st.caption(
        "Source columns are matched against Vireo canonical field contracts. "
        "Review detected mappings below or override them manually."
    )

    source_cols = list(raw_df.columns)
    manual_overrides = dict(st.session_state["uploaded_manual_mapping"])

    # Run mapping detection
    mapping_report: MappingReport = ColumnMapper.detect_mapping(
        source_columns=source_cols,
        manual_mapping=manual_overrides,
        dataset_type=DatasetType.TICKETS
    )

    # Collision warning alert
    if mapping_report.collision_errors:
        for canon, srcs in mapping_report.collision_errors.items():
            st.error(
                f"⚠️ **Mapping Collision Detected:** Multiple source columns ({', '.join(srcs)}) "
                f"are attempting to map to `{canon}`. Select which column to use using the manual controls below."
            )

    canonical_options = ["-- Do Not Map --"] + list(CANONICAL_TICKET_FIELDS.keys())

    with st.expander("🛠️ Inspect & Adjust Column Mappings", expanded=not mapping_report.is_valid):
        st.markdown("Configure how source headers map to canonical schema fields:")
        grid_cols = st.columns(3)

        updated_manual = {}
        for idx, src_col in enumerate(source_cols):
            # Determine current mapped canonical target
            current_target = None
            for canon, s in mapping_report.mapped_columns.items():
                if s == src_col:
                    current_target = canon
                    break

            default_idx = (
                canonical_options.index(current_target)
                if current_target in canonical_options
                else 0
            )

            col_container = grid_cols[idx % 3]
            with col_container:
                chosen = st.selectbox(
                    f"Source: `{src_col}`",
                    options=canonical_options,
                    index=default_idx,
                    key=f"map_select_{src_col}"
                )
                if chosen != "-- Do Not Map --":
                    updated_manual[chosen] = src_col

        if updated_manual != st.session_state["uploaded_manual_mapping"]:
            st.session_state["uploaded_manual_mapping"] = updated_manual
            st.session_state["uploaded_pipeline_result"] = None
            st.rerun()

    # Re-evaluate mapping after adjustments
    final_report: MappingReport = ColumnMapper.detect_mapping(
        source_columns=source_cols,
        manual_mapping=st.session_state["uploaded_manual_mapping"],
        dataset_type=DatasetType.TICKETS
    )

    # Apply mapping in memory
    mapped_df = ColumnMapper.apply_mapping(raw_df, final_report.mapped_columns)

    # -------------------------------------------------------------------------
    # SECTION C: Validation Summary
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("🔍 C. Data Quality & Schema Validation Report")

    validation_result: ValidationResult = DynamicValidator.validate_ticket_dataframe(mapped_df)

    v1, v2, v3, v4 = st.columns(4)
    v1.metric("Validation Status", "PASSED ✅" if validation_result.is_valid else "BLOCKED ❌")
    v2.metric("Blocking Errors", len(validation_result.errors))
    v3.metric("Warnings", len(validation_result.warnings))
    v4.metric("Informational Notes", len(validation_result.info))

    if validation_result.errors:
        st.error("### 🛑 Fatal Schema & Data Errors")
        for err in validation_result.errors:
            st.markdown(f"- ❌ **Field `{err.field}`:** {err.issue} *(Fix: {err.recommendation})*")

    if validation_result.warnings:
        with st.expander(f"⚠️ View {len(validation_result.warnings)} Non-Blocking Data Quality Warnings", expanded=True):
            for w in validation_result.warnings:
                st.markdown(f"- 🔸 **Field `{w.field}`:** {w.issue} *(Recommendation: {w.recommendation})*")

    if validation_result.info:
        with st.expander(f"ℹ️ View {len(validation_result.info)} Policy & Null-Value Observations", expanded=False):
            for item in validation_result.info:
                st.markdown(f"- 🔹 **Field `{item.field}`:** {item.issue}")

    # -------------------------------------------------------------------------
    # SECTION D: Dataset Preview (PII-Masked)
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("👀 D. In-Memory Dataset Preview")
    st.caption(
        "Displays mapped canonical columns with privacy sanitization. "
        "Sensitive customer phone numbers and email addresses are masked for security."
    )

    preview_rows = st.slider("Preview Rows", min_value=5, max_value=25, value=5, step=5)
    sanitized_slice = sanitize_preview_df(mapped_df, max_rows=preview_rows)
    st.dataframe(sanitized_slice, use_container_width=True)

    # Column type and null counts overview
    with st.expander("📊 Inspect Column Data Types & Missing-Value Statistics", expanded=False):
        col_stats = []
        for c in mapped_df.columns:
            null_count = int(mapped_df[c].isna().sum())
            null_pct = round(null_count / len(mapped_df) * 100, 1)
            col_stats.append({
                "Column Name": c,
                "Data Type": str(mapped_df[c].dtype),
                "Missing Values": f"{null_count:,} ({null_pct}%)",
                "Non-Null Count": f"{len(mapped_df) - null_count:,}"
            })
        st.dataframe(pd.DataFrame(col_stats), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # SECTION E: Report Compatibility Panel
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📊 E. Report Capability Compatibility Panel")
    st.caption(
        "Granular feasibility evaluation across all seven core analytical reports. "
        "Unavailable reports are never presented as ₹0 or 0%."
    )

    # Run dynamic pipeline in memory
    pipeline_result: DynamicPipelineResult = DynamicPipeline.process(
        tickets_df=mapped_df,
        agents_df=None,     # Auxiliary upload can be added in future
        products_df=None,
        orders_df=None
    )
    st.session_state["uploaded_pipeline_result"] = pipeline_result

    # Display report capabilities grid
    caps = pipeline_result.capabilities

    for cap_id, cap in caps.items():
        with st.container():
            c_header, c_status = st.columns([3, 1])

            with c_header:
                if cap.status == CapabilityStatus.AVAILABLE:
                    st.markdown(f"#### ✅ {cap.name}")
                elif cap.status == CapabilityStatus.PARTIAL:
                    st.markdown(f"#### ⚠️ {cap.name}")
                else:
                    st.markdown(f"#### 🔒 {cap.name}")
                st.caption(cap.explanation)

            with c_status:
                if cap.status == CapabilityStatus.AVAILABLE:
                    st.success("AVAILABLE")
                elif cap.status == CapabilityStatus.PARTIAL:
                    st.warning("PARTIAL")
                else:
                    st.error("UNAVAILABLE")

            # Missing requirements explanation
            if cap.missing_fields or cap.supporting_datasets_missing or cap.warnings:
                details = []
                if cap.missing_fields:
                    details.append(f"**Missing Required Fields:** `{', '.join(cap.missing_fields)}`")
                if cap.supporting_datasets_missing:
                    details.append(f"**Missing Auxiliary Datasets:** `{', '.join(cap.supporting_datasets_missing)}`")
                for w in cap.warnings:
                    details.append(f"⚠️ *{w}*")
                st.markdown(" | ".join(details))

            st.markdown("---")

    # Final Workspace Governance Summary
    st.caption(
        "**Ingestion Governance Disclaimer:** Vireo Audio dynamic ingestion operates strictly in transient memory. "
        "No customer data or telemetry is written to storage disks or external APIs. "
        "To revert to the certified 18-month baseline, click 'Clear Dataset' at the top."
    )

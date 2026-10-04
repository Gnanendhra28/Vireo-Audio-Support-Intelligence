"""In-memory validation engine for uploaded support datasets.

Enforces schema contracts, detects data corruption, timestamp anomalies,
and domain invalidities without writing to disk or mutating source DataFrames.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field

from src.data.schema_contract import (
    CANONICAL_TICKET_FIELDS,
    CanonicalFieldDefinition,
    FieldRequirement,
    get_canonical_fields,
    get_required_fields,
    DatasetType,
)


class ValidationSeverity(str, Enum):
    """Severity classification of validation findings."""
    ERROR = "ERROR"        # Fatal schema or integrity flaw; pipeline execution blocked
    WARNING = "WARNING"    # Data quality risk or non-standard values; pipeline can proceed with caveats
    INFO = "INFO"          # Informational notice regarding dataset properties or null preservation


class ValidationIssue(BaseModel):
    """Individual data validation finding with actionable guidance."""
    severity: ValidationSeverity = Field(description="Issue severity level")
    field: str = Field(description="Affected canonical or source field name")
    issue: str = Field(description="Description of detected fault or anomaly")
    recommendation: str = Field(description="Actionable fix or operational recommendation")
    sample_values: Optional[List[str]] = Field(
        default=None,
        description="Sample problematic values for operator diagnosis"
    )


class ValidationResult(BaseModel):
    """Comprehensive validation report summarizing dataset integrity."""
    is_valid: bool = Field(description="True if zero ERROR issues were detected")
    total_rows: int = Field(description="Row count of evaluated dataset")
    total_columns: int = Field(description="Column count of evaluated dataset")
    errors: List[ValidationIssue] = Field(default_factory=list, description="Blocking errors")
    warnings: List[ValidationIssue] = Field(default_factory=list, description="Non-blocking warnings")
    info: List[ValidationIssue] = Field(default_factory=list, description="Informational observations")

    @property
    def all_issues(self) -> List[ValidationIssue]:
        """Aggregate list of all validation findings."""
        return self.errors + self.warnings + self.info


class DynamicValidator:
    """Validates in-memory candidate support DataFrames against canonical contracts."""

    @classmethod
    def validate_ticket_dataframe(
        cls,
        df: pd.DataFrame,
        dataset_type: DatasetType = DatasetType.TICKETS
    ) -> ValidationResult:
        """Execute comprehensive validation checks on an in-memory support tickets DataFrame.

        Never mutates the input DataFrame or writes to the filesystem.

        Args:
            df: Candidate DataFrame with canonicalized column headers.
            dataset_type: Dataset contract type (defaults to DatasetType.TICKETS).

        Returns:
            ValidationResult with categorized errors, warnings, and info items.
        """
        errors: List[ValidationIssue] = []
        warnings: List[ValidationIssue] = []
        info: List[ValidationIssue] = []

        total_rows = len(df)
        total_cols = len(df.columns)

        # -------------------------------------------------------------
        # 1. Empty Dataset Check
        # -------------------------------------------------------------
        if total_rows == 0 or total_cols == 0:
            errors.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                field="dataset",
                issue="Uploaded dataset contains zero rows or columns.",
                recommendation="Provide a populated CSV file containing support ticket records."
            ))
            return ValidationResult(
                is_valid=False,
                total_rows=total_rows,
                total_columns=total_cols,
                errors=errors,
                warnings=warnings,
                info=info
            )

        # -------------------------------------------------------------
        # 2. Required Fields Check
        # -------------------------------------------------------------
        required_fields = get_required_fields(dataset_type)
        missing_required = [f for f in required_fields if f not in df.columns]

        if missing_required:
            errors.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                field="columns",
                issue=f"Missing mandatory canonical fields: {', '.join(missing_required)}",
                recommendation="Map raw headers to required canonical fields before running analytics."
            ))

        # -------------------------------------------------------------
        # 3. Primary Key Uniqueness & Null Check (ticket_id)
        # -------------------------------------------------------------
        if "ticket_id" in df.columns:
            null_keys = int(df["ticket_id"].isna().sum())
            if null_keys > 0:
                errors.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field="ticket_id",
                    issue=f"Found {null_keys} rows with null or empty ticket_id.",
                    recommendation="Ensure all ticket records possess a non-null unique identifier."
                ))

            dup_keys = int(df["ticket_id"].duplicated().sum())
            if dup_keys > 0:
                sample_dups = df[df["ticket_id"].duplicated()]["ticket_id"].head(5).astype(str).tolist()
                errors.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field="ticket_id",
                    issue=f"Found {dup_keys} duplicate ticket_id values in dataset.",
                    recommendation="Deduplicate ticket records to ensure primary key uniqueness.",
                    sample_values=sample_dups
                ))

        # -------------------------------------------------------------
        # 4. Timestamp Validity & Chronological Checks
        # -------------------------------------------------------------
        dt_columns = ["created_at", "first_response_at", "resolved_at"]
        parsed_dates: Dict[str, pd.Series] = {}

        for col in dt_columns:
            if col in df.columns:
                series = df[col]
                # Check for unparseable timestamps
                converted = pd.to_datetime(series, format="mixed", errors="coerce")
                non_null_raw = series.dropna()
                unparseable_count = int(converted.isna().sum() - series.isna().sum())

                if unparseable_count > 0:
                    sample_unparseable = non_null_raw[converted.isna()].head(3).astype(str).tolist()
                    errors.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field=col,
                        issue=f"{unparseable_count} timestamp values in '{col}' could not be parsed.",
                        recommendation="Format datetime strings in standard ISO 8601 or YYYY-MM-DD HH:MM:SS format.",
                        sample_values=sample_unparseable
                    ))
                else:
                    parsed_dates[col] = converted

        # Chronological sanity: response before creation or resolution before response
        if "created_at" in parsed_dates and "first_response_at" in parsed_dates:
            resp_before_created = int(
                (parsed_dates["first_response_at"] < parsed_dates["created_at"]).sum()
            )
            if resp_before_created > 0:
                warnings.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="first_response_at",
                    issue=f"{resp_before_created} tickets report first_response_at earlier than created_at.",
                    recommendation="Audit intake logging or timezone reconciliation for initial reply timestamps."
                ))

        if "first_response_at" in parsed_dates and "resolved_at" in parsed_dates:
            res_before_resp = int(
                (parsed_dates["resolved_at"].notna() &
                 (parsed_dates["resolved_at"] < parsed_dates["first_response_at"])).sum()
            )
            if res_before_resp > 0:
                warnings.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="resolved_at",
                    issue=f"{res_before_resp} tickets report resolved_at earlier than first_response_at.",
                    recommendation="Verify ticket event reconstructor or resolution timestamp logging."
                ))

        # -------------------------------------------------------------
        # 5. Numeric Range and Domain Validations
        # -------------------------------------------------------------
        if "csat_score" in df.columns:
            csat_non_null = df["csat_score"].dropna()
            try:
                csat_numeric = pd.to_numeric(csat_non_null, errors="coerce")
                invalid_numeric = int(csat_numeric.isna().sum())
                if invalid_numeric > 0:
                    errors.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field="csat_score",
                        issue=f"{invalid_numeric} csat_score values are non-numeric strings.",
                        recommendation="Ensure CSAT values are numeric ratings between 1.0 and 5.0."
                    ))
                else:
                    out_of_bounds = int(((csat_numeric < 1.0) | (csat_numeric > 5.0)).sum())
                    if out_of_bounds > 0:
                        sample_out = csat_numeric[(csat_numeric < 1.0) | (csat_numeric > 5.0)].head(3).astype(str).tolist()
                        warnings.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            field="csat_score",
                            issue=f"{out_of_bounds} csat_score values fall outside standard 1.0 to 5.0 scale.",
                            recommendation="Check whether uploaded CSAT uses a 10-point scale or percentage format.",
                            sample_values=sample_out
                        ))
            except Exception:
                pass

        if "refund_amount_inr" in df.columns:
            refund_non_null = df["refund_amount_inr"].dropna()
            refund_numeric = pd.to_numeric(refund_non_null, errors="coerce")
            neg_refunds = int((refund_numeric < 0.0).sum())
            if neg_refunds > 0:
                warnings.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="refund_amount_inr",
                    issue=f"{neg_refunds} refund records have negative monetary values.",
                    recommendation="Verify that refunds represent positive disbursement values, not accounting debits."
                ))

        if "transfers" in df.columns:
            transfers_non_null = df["transfers"].dropna()
            transfers_numeric = pd.to_numeric(transfers_non_null, errors="coerce")
            neg_transfers = int((transfers_numeric < 0.0).sum())
            if neg_transfers > 0:
                warnings.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="transfers",
                    issue=f"{neg_transfers} transfer counts are negative.",
                    recommendation="Ensure transfer handoff counts are non-negative integers."
                ))

        # -------------------------------------------------------------
        # 6. Categorical Domain Checks (Channel, Status, Replacement)
        # -------------------------------------------------------------
        if "channel" in df.columns:
            valid_channels = {"chat", "email", "voice", "social"}
            observed_channels = set(df["channel"].dropna().astype(str).str.lower().unique())
            unknown_channels = observed_channels - valid_channels
            if unknown_channels:
                warnings.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="channel",
                    issue=f"Observed non-standard channels: {', '.join(unknown_channels)}",
                    recommendation="Map non-standard communication channels to standard ('chat', 'email', 'voice', 'social') to enable SLA and financial models.",
                    sample_values=list(unknown_channels)
                ))

        if "status" in df.columns:
            valid_statuses = {"resolved", "closed", "open", "pending"}
            observed_statuses = set(df["status"].dropna().astype(str).str.lower().unique())
            unknown_statuses = observed_statuses - valid_statuses
            if unknown_statuses:
                warnings.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="status",
                    issue=f"Observed non-standard statuses: {', '.join(unknown_statuses)}",
                    recommendation="Map lifecycle statuses to standard ('resolved', 'closed', 'open', 'pending') for accurate backlog accounting.",
                    sample_values=list(unknown_statuses)
                ))

        # -------------------------------------------------------------
        # 7. Semantic Missing Value Preservation Rules (Policy Safeguards)
        # -------------------------------------------------------------
        if "transfers" in df.columns:
            null_transfers = int(df["transfers"].isna().sum())
            if null_transfers > 0:
                info.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    field="transfers",
                    issue=f"{null_transfers} records have missing transfer values. Missing transfers are preserved as null.",
                    recommendation="Do not impute missing transfers as zero; evaluate transfers only on observable populations."
                ))

        if "csat_score" in df.columns:
            null_csat = int(df["csat_score"].isna().sum())
            if null_csat > 0:
                info.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    field="csat_score",
                    issue=f"{null_csat} records have missing CSAT scores. Missing scores represent non-responses.",
                    recommendation="Compute average CSAT strictly across respondent populations (excluding nulls)."
                ))

        if "refund_amount_inr" in df.columns:
            null_refunds = int(df["refund_amount_inr"].isna().sum())
            if null_refunds > 0:
                info.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    field="refund_amount_inr",
                    issue=f"{null_refunds} records have blank refund amounts.",
                    recommendation="Preserve nulls during ingestion; treat as 0.0 only within documented aggregate monetary sums."
                ))

        if "customer_message" in df.columns:
            blank_msgs = int((df["customer_message"].isna() | (df["customer_message"].astype(str).str.strip() == "")).sum())
            if blank_msgs > 0:
                warnings.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="customer_message",
                    issue=f"{blank_msgs} tickets contain blank or null customer messages.",
                    recommendation="Tickets with blank customer messages will default to INSUFFICIENT_INFORMATION during classification."
                ))

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            total_rows=total_rows,
            total_columns=total_cols,
            errors=errors,
            warnings=warnings,
            info=info
        )

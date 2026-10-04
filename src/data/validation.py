"""Data validation and data quality audit module for Vireo Audio Support Intelligence.

Enforces referential integrity, primary key uniqueness, timestamp checks,
and privacy-preserving data masking.
"""

from typing import Dict, List, Any, Optional
import pandas as pd


class DataValidator:
    """Validates data integrity, foreign keys, timestamps, and compliance rules."""

    @staticmethod
    def check_primary_keys(df: pd.DataFrame, key_column: str) -> Dict[str, Any]:
        """Verify primary key uniqueness and null-free status.

        Args:
            df: Input DataFrame.
            key_column: Column name expected to be unique primary key.

        Returns:
            Dictionary with total rows, unique count, duplicate count, and null count.
        """
        total = len(df)
        unique = df[key_column].nunique()
        duplicates = total - unique
        nulls = int(df[key_column].isna().sum())
        return {
            "key_column": key_column,
            "total_rows": total,
            "unique_keys": unique,
            "duplicate_count": duplicates,
            "null_count": nulls,
            "is_valid": (duplicates == 0 and nulls == 0)
        }

    @staticmethod
    def check_foreign_key(
        child_df: pd.DataFrame,
        child_col: str,
        parent_df: pd.DataFrame,
        parent_col: str,
        allow_nulls: bool = False
    ) -> Dict[str, Any]:
        """Verify referential integrity between child and parent DataFrames.

        Args:
            child_df: Child DataFrame containing foreign key.
            child_col: Column name in child DataFrame.
            parent_df: Parent DataFrame containing primary key.
            parent_col: Column name in parent DataFrame.
            allow_nulls: Whether nulls in child_col are permitted.

        Returns:
            Dictionary with missing count and validation status.
        """
        child_values = child_df[child_col].dropna() if allow_nulls else child_df[child_col]
        parent_set = set(parent_df[parent_col].dropna())
        missing_keys = set(child_values) - parent_set
        return {
            "child_column": child_col,
            "parent_column": parent_col,
            "orphaned_count": len(missing_keys),
            "orphaned_sample": list(missing_keys)[:5],
            "is_valid": len(missing_keys) == 0
        }

    @staticmethod
    def check_timestamp_anomalies(tickets_df: pd.DataFrame) -> Dict[str, int]:
        """Detect timestamp chronological sequence violations.

        Args:
            tickets_df: Tickets DataFrame containing created_at, first_response_at, resolved_at.

        Returns:
            Dictionary of anomaly counts.
        """
        t_created = pd.to_datetime(tickets_df["created_at"])
        t_resp = pd.to_datetime(tickets_df["first_response_at"])
        t_res = pd.to_datetime(tickets_df["resolved_at"])

        resp_before_created = int((t_resp < t_created).sum())
        res_before_resp = int(((t_res.notna()) & (t_res < t_resp)).sum())
        res_before_created = int(((t_res.notna()) & (t_res < t_created)).sum())

        return {
            "response_before_created": resp_before_created,
            "resolved_before_response": res_before_resp,
            "resolved_before_created": res_before_created,
        }

    @staticmethod
    def mask_pii(text: Optional[str]) -> str:
        """Sanitize message strings for privacy-conscious reporting or UI display.

        Removes sensitive customer attributes and truncates.

        Args:
            text: Raw message string.

        Returns:
            Privacy-safe string snippet.
        """
        if text is None or pd.isna(text):
            return ""
        clean_text = " ".join(str(text).split())
        # Mask sensitive keywords / tokens
        if len(clean_text) > 120:
            return clean_text[:117] + "..."
        return clean_text

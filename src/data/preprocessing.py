"""Data preprocessing module for Vireo Audio Support Intelligence.

Handles timezone corrections for legacy tickets, timestamp calculations,
SLA breach detection, fallback order joins, and roster enrichment.
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np


class DataPreprocessor:
    """Preprocesses and enriches support tickets with business policy metrics."""

    # SLA first-response targets in hours (Support Policy §3)
    SLA_TARGETS_HOURS = {
        "chat": 15.0 / 60.0,    # 15 minutes = 0.25 h
        "voice": 2.0,            # 2 hours callback
        "social": 4.0,           # 4 hours
        "email": 8.0,            # 8 hours
    }

    # Policy §3 store credit fee for breach
    SLA_BREACH_PENALTY_INR = 350.0

    @classmethod
    def apply_legacy_timestamp_correction(cls, tickets_df: pd.DataFrame) -> pd.DataFrame:
        """Correct legacy Freshdesk resolution timestamps from UTC to IST (+5h30m).

        Operating Policy §9 notes that Freshdesk resolution timestamps were
        reconstructed from the event log in UTC, whereas created_at and
        first_response_at are in IST.

        Args:
            tickets_df: DataFrame containing tickets data.

        Returns:
            DataFrame with normalized datetime objects.
        """
        df = tickets_df.copy()
        df["created_dt"] = pd.to_datetime(df["created_at"])
        df["first_response_dt"] = pd.to_datetime(df["first_response_at"])
        df["resolved_dt"] = pd.to_datetime(df["resolved_at"])

        # Apply +05:30:00 offset to legacy_fd resolved_dt
        legacy_mask = (df["source_system"] == "legacy_fd") & (df["resolved_dt"].notna())
        df.loc[legacy_mask, "resolved_dt"] = df.loc[legacy_mask, "resolved_dt"] + pd.Timedelta(hours=5, minutes=30)
        return df

    @classmethod
    def compute_workload_metrics(cls, tickets_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate first response time, handle time, resolution time, and SLA breach status.

        Args:
            tickets_df: DataFrame with normalized datetime columns (created_dt, etc.)

        Returns:
            DataFrame enriched with performance metrics.
        """
        df = tickets_df.copy()
        if "created_dt" not in df.columns:
            df = cls.apply_legacy_timestamp_correction(df)

        # Response time in hours
        df["resp_time_hrs"] = (df["first_response_dt"] - df["created_dt"]).dt.total_seconds() / 3600.0

        # Handle time in hours (first response to resolution)
        df["handle_time_hrs"] = np.where(
            df["resolved_dt"].notna(),
            (df["resolved_dt"] - df["first_response_dt"]).dt.total_seconds() / 3600.0,
            np.nan
        )

        # Total resolution time in hours (created to resolved)
        df["total_res_time_hrs"] = np.where(
            df["resolved_dt"].notna(),
            (df["resolved_dt"] - df["created_dt"]).dt.total_seconds() / 3600.0,
            np.nan
        )

        # Map channel SLA target
        df["sla_target_hrs"] = df["channel"].str.lower().map(cls.SLA_TARGETS_HOURS)

        # SLA breach flag (Policy §3: first response later than target)
        df["is_sla_breach"] = df["resp_time_hrs"] > df["sla_target_hrs"]

        # Breach credit liability
        df["sla_penalty_inr"] = np.where(df["is_sla_breach"], cls.SLA_BREACH_PENALTY_INR, 0.0)

        return df

    @classmethod
    def enrich_with_agent_roster(
        cls,
        tickets_df: pd.DataFrame,
        agents_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge agent metadata strictly via agent_id.

        Never joins on agent display name due to name duplication (e.g. Om Sharma).

        Args:
            tickets_df: Tickets DataFrame containing agent_id.
            agents_df: Agents roster DataFrame.

        Returns:
            Enriched DataFrame with resolving agent team, tier, and site.
        """
        df = tickets_df.copy()
        roster_subset = agents_df[["agent_id", "team", "tier", "site", "shift", "name"]].rename(
            columns={
                "team": "resolving_team",
                "tier": "resolving_tier",
                "site": "resolving_site",
                "shift": "resolving_shift",
                "name": "resolving_agent_name"
            }
        )
        return df.merge(roster_subset, on="agent_id", how="left")

    @classmethod
    def enrich_fallback_orders(
        cls,
        tickets_df: pd.DataFrame,
        orders_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Enrich tickets missing order_id using customer_id + product_sku fallback key.

        Args:
            tickets_df: Tickets DataFrame.
            orders_df: Orders DataFrame.

        Returns:
            Tickets DataFrame with inferred order_id and order_value_inr populated where missing.
        """
        df = tickets_df.copy()
        # Sort orders descending to prioritize latest order if multiple exist
        orders_sorted = orders_df.sort_values("order_date", ascending=False)
        fallback_lookup = orders_sorted.drop_duplicates(subset=["customer_id", "sku"])[
            ["customer_id", "sku", "order_id", "order_value_inr"]
        ].rename(columns={"sku": "product_sku", "order_id": "fallback_order_id", "order_value_inr": "fallback_order_value"})

        merged = df.merge(fallback_lookup, on=["customer_id", "product_sku"], how="left")
        merged["effective_order_id"] = merged["order_id"].fillna(merged["fallback_order_id"])
        return merged

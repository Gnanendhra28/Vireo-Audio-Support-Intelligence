"""Monthly business analytics and trends engine for Vireo Audio Support Intelligence.

Produces month-by-month operational KPIs across incoming volume, resolution velocity,
predicted categories, CSAT, transfers, and repeat contacts for the core 18-month window.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from src.analytics.sla import SLAMetrics


class MonthlyAnalytics:
    """Computes monthly support trends across the core 18-month analysis window."""

    START_DATE = "2025-01-01"
    END_DATE = "2026-06-30"

    @classmethod
    def filter_core_window(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Filter tickets strictly within the core 18-month window (2025-01-01 to 2026-06-30).

        Args:
            df: Tickets DataFrame containing created_at.

        Returns:
            Filtered DataFrame.
        """
        df_copy = df.copy()
        df_copy["created_dt"] = pd.to_datetime(df_copy["created_at"])
        mask = (df_copy["created_dt"] >= cls.START_DATE) & (df_copy["created_dt"] <= f"{cls.END_DATE} 23:59:59")
        return df_copy[mask].copy()

    @classmethod
    def compute_monthly_kpis(
        cls,
        tickets_df: pd.DataFrame,
        agents_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Compute month-by-month operational KPIs.

        Args:
            tickets_df: Classified tickets DataFrame.
            agents_df: Agents roster DataFrame.

        Returns:
            DataFrame indexed by Year-Month with core operational metrics.
        """
        core = cls.filter_core_window(tickets_df)

        # Merge resolving agent metadata
        if "resolving_team" not in core.columns:
            core = core.merge(
                agents_df[["agent_id", "team", "tier"]].rename(
                    columns={"team": "resolving_team", "tier": "resolving_tier"}
                ),
                on="agent_id",
                how="left"
            )

        # Apply legacy timestamp offset (+5h30m) to legacy_fd resolved_at
        core["first_response_dt"] = pd.to_datetime(core["first_response_at"])
        core["resolved_dt"] = pd.to_datetime(core["resolved_at"])
        legacy_mask = (core["source_system"] == "legacy_fd") & (core["resolved_dt"].notna())
        core.loc[legacy_mask, "resolved_dt"] = core.loc[legacy_mask, "resolved_dt"] + pd.Timedelta(hours=5, minutes=30)

        # Calculate durations
        core["handle_time_hrs"] = (core["resolved_dt"] - core["first_response_dt"]).dt.total_seconds() / 3600.0
        core["total_res_time_hrs"] = (core["resolved_dt"] - core["created_dt"]).dt.total_seconds() / 3600.0

        # Calculate SLA breaches
        core = SLAMetrics.calculate_breaches(core)

        # Calculate repeat contacts within 30 days
        core_sorted = core.sort_values(["customer_id", "created_dt"]).copy()
        core_sorted["prev_resolved_dt"] = core_sorted.groupby("customer_id")["resolved_dt"].shift(1)
        core_sorted["days_since_prev_res"] = (
            core_sorted["created_dt"] - core_sorted["prev_resolved_dt"]
        ).dt.total_seconds() / (24 * 3600.0)
        core_sorted["is_repeat_contact_30d"] = (
            (core_sorted["days_since_prev_res"] >= 0) & (core_sorted["days_since_prev_res"] <= 30)
        )
        core = core_sorted

        # Creation month period
        core["month"] = core["created_dt"].dt.to_period("M").astype(str)

        monthly_records = []
        for m, grp in core.groupby("month"):
            total_incoming = len(grp)
            resolved_count = int((grp["status"] == "resolved").sum())
            closed_count = int((grp["status"] == "closed").sum())
            open_count = int((grp["status"] == "open").sum())
            pending_count = int((grp["status"] == "pending").sum())
            sla_breaches = int(grp["is_sla_breach"].sum())

            # Durations (only for resolved/closed where valid)
            valid_res = grp["total_res_time_hrs"].dropna()
            med_res = float(valid_res.median()) if len(valid_res) > 0 else np.nan
            valid_handle = grp["handle_time_hrs"].dropna()
            med_handle = float(valid_handle.median()) if len(valid_handle) > 0 else np.nan

            # CSAT strictly on responses (excluding nulls)
            csat_valid = grp["csat_score"].dropna()
            csat_count = len(csat_valid)
            csat_mean = float(csat_valid.mean()) if csat_count > 0 else np.nan

            # Observable transfers (helpdesk only; legacy is null)
            hd_grp = grp[grp["source_system"] == "helpdesk"]
            transfers_count = int(hd_grp["transfers"].sum()) if len(hd_grp) > 0 else 0
            transfers_observable = len(hd_grp)

            # Repeat contacts
            repeats = int(grp["is_repeat_contact_30d"].sum())

            monthly_records.append({
                "month": m,
                "incoming_tickets": total_incoming,
                "resolved_tickets": resolved_count,
                "auto_closed_tickets": closed_count,
                "open_backlog": open_count,
                "pending_backlog": pending_count,
                "active_backlog_total": open_count + pending_count,
                "sla_breaches": sla_breaches,
                "sla_breach_rate_pct": round(sla_breaches / total_incoming * 100, 2),
                "median_resolution_hours": round(med_res, 2),
                "median_handle_hours": round(med_handle, 2),
                "csat_response_count": csat_count,
                "csat_mean_score": round(csat_mean, 2) if pd.notna(csat_mean) else np.nan,
                "observable_transfers": transfers_count,
                "helpdesk_tickets_sampled": transfers_observable,
                "repeat_contacts_30d": repeats,
                "repeat_contact_rate_pct": round(repeats / total_incoming * 100, 2)
            })

        return pd.DataFrame(monthly_records)

    @classmethod
    def compute_monthly_category_volume(cls, tickets_df: pd.DataFrame) -> pd.DataFrame:
        """Compute monthly volume breakdown across the Seven-Pillar predicted categories.

        Args:
            tickets_df: Classified tickets DataFrame.

        Returns:
            Pivot table of Month x Predicted Category.
        """
        core = cls.filter_core_window(tickets_df)
        core["month"] = core["created_dt"].dt.to_period("M").astype(str)
        pivot = pd.crosstab(
            core["month"],
            core["predicted_category"],
            margins=True,
            margins_name="Total Incoming"
        )
        return pivot

    @classmethod
    def compute_monthly_resolving_team_volume(
        cls,
        tickets_df: pd.DataFrame,
        agents_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Compute monthly volume breakdown across actual resolving departments.

        Args:
            tickets_df: Classified tickets DataFrame.
            agents_df: Agents roster DataFrame.

        Returns:
            Pivot table of Month x Resolving Department.
        """
        core = cls.filter_core_window(tickets_df)
        if "resolving_team" not in core.columns:
            core = core.merge(
                agents_df[["agent_id", "team"]].rename(columns={"team": "resolving_team"}),
                on="agent_id",
                how="left"
            )

        core["month"] = core["created_dt"].dt.to_period("M").astype(str)
        pivot = pd.crosstab(
            core["month"],
            core["resolving_team"],
            margins=True,
            margins_name="Total Handled"
        )
        return pivot

"""SLA performance and breach liability analytics module for Vireo Audio Support Intelligence.

Enforces Operating Policy §3 first-response targets and calculates store credit liabilities.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class SLAMetrics:
    """Computes first-response duration, breach flags, and financial penalty liabilities."""

    # Policy §3 First-Response Targets in Hours
    CHANNEL_TARGETS_HOURS = {
        "chat": 0.25,    # 15 minutes
        "voice": 2.0,    # 2 hours callback
        "social": 4.0,   # 4 hours
        "email": 8.0     # 8 hours
    }

    # Policy §3 store credit issued per qualifying breach
    BREACH_PENALTY_INR = 350.0

    @classmethod
    def calculate_breaches(cls, tickets_df: pd.DataFrame) -> pd.DataFrame:
        """Enrich tickets DataFrame with response times, SLA targets, and breach flags.

        Args:
            tickets_df: DataFrame with created_at, first_response_at, channel.

        Returns:
            DataFrame with resp_time_hrs, sla_target_hrs, is_sla_breach, sla_penalty_inr.
        """
        df = tickets_df.copy()
        df["created_dt"] = pd.to_datetime(df["created_at"])
        df["first_response_dt"] = pd.to_datetime(df["first_response_at"])

        df["resp_time_hrs"] = (df["first_response_dt"] - df["created_dt"]).dt.total_seconds() / 3600.0

        # Map channel targets
        df["sla_target_hrs"] = df["channel"].str.lower().map(cls.CHANNEL_TARGETS_HOURS)

        # Flag breach: first response later than policy target
        df["is_sla_breach"] = df["resp_time_hrs"] > df["sla_target_hrs"]
        df["sla_penalty_inr"] = np.where(df["is_sla_breach"], cls.BREACH_PENALTY_INR, 0.0)

        return df

    @classmethod
    def compute_channel_sla_summary(cls, enriched_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate SLA compliance metrics by support channel.

        Args:
            enriched_df: DataFrame output from calculate_breaches.

        Returns:
            Summary DataFrame by channel.
        """
        records = []
        for ch, grp in enriched_df.groupby("channel"):
            total = len(grp)
            breaches = int(grp["is_sla_breach"].sum())
            breach_rate = breaches / total * 100 if total > 0 else 0.0
            compliance_rate = 100.0 - breach_rate
            penalty = breaches * cls.BREACH_PENALTY_INR
            med_resp = grp["resp_time_hrs"].median()

            records.append({
                "channel": ch,
                "target_hours": cls.CHANNEL_TARGETS_HOURS.get(str(ch).lower(), np.nan),
                "total_tickets": total,
                "median_response_hours": round(med_resp, 3),
                "sla_breaches": breaches,
                "compliance_rate_pct": round(compliance_rate, 2),
                "breach_rate_pct": round(breach_rate, 2),
                "penalty_credit_liability_inr": penalty
            })

        return pd.DataFrame(records)

    @classmethod
    def compute_team_sla_summary(cls, enriched_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate SLA compliance metrics by resolving department.

        Args:
            enriched_df: DataFrame output from calculate_breaches.

        Returns:
            Summary DataFrame by resolving team.
        """
        if "resolving_team" not in enriched_df.columns:
            return pd.DataFrame()

        records = []
        for team, grp in enriched_df.groupby("resolving_team"):
            total = len(grp)
            breaches = int(grp["is_sla_breach"].sum())
            breach_rate = breaches / total * 100 if total > 0 else 0.0
            compliance_rate = 100.0 - breach_rate
            penalty = breaches * cls.BREACH_PENALTY_INR

            records.append({
                "team": team,
                "total_resolved": total,
                "sla_breaches": breaches,
                "compliance_rate_pct": round(compliance_rate, 2),
                "breach_rate_pct": round(breach_rate, 2),
                "penalty_credit_liability_inr": penalty
            })

        return pd.DataFrame(records).sort_values("sla_breaches", ascending=False)

"""Workload and queue distribution analytics module for Vireo Audio Support Intelligence.

Analyzes team-by-team workload, assigned vs resolved volumes, net routing deltas,
and operational backlogs with strict Tier 1 vs Tier 2 separation.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class WorkloadAnalyzer:
    """Analyzes departmental ticket volume, agent assignments, and capacity trends."""

    @staticmethod
    def compute_team_workload_summary(
        tickets_df: pd.DataFrame,
        agents_df: pd.DataFrame,
        start_date: str = "2025-01-01",
        end_date: str = "2026-06-30"
    ) -> pd.DataFrame:
        """Compute comprehensive assigned vs resolved workload metrics by department.

        Strictly enforces separate reporting of Tier 1 and Tier 2 teams.

        Args:
            tickets_df: Classified tickets DataFrame containing created_at, resolved_at, etc.
            agents_df: Agents roster DataFrame.
            start_date: Inclusive start date (YYYY-MM-DD).
            end_date: Inclusive end date (YYYY-MM-DD).

        Returns:
            DataFrame of workload metrics per department.
        """
        df = tickets_df.copy()
        df["created_dt"] = pd.to_datetime(df["created_at"])

        # Filter core analysis window
        mask = (df["created_dt"] >= start_date) & (df["created_dt"] <= f"{end_date} 23:59:59")
        core = df[mask].copy()

        # Join agent roster to get resolving team and tier
        roster_subset = agents_df[["agent_id", "team", "tier"]].rename(
            columns={"team": "resolving_team", "tier": "resolving_tier"}
        )
        if "resolving_team" not in core.columns:
            core = core.merge(roster_subset, on="agent_id", how="left")

        # Headcount per team from roster
        roster_headcount = agents_df.groupby("team")["agent_id"].count().to_dict()

        # Active agents observed resolving tickets in core window
        active_agents = core.groupby("resolving_team")["agent_id"].nunique().to_dict()

        # Assigned volume (intake bot view)
        assigned_vol = core.groupby("assigned_team")["ticket_id"].count().to_dict()

        # Resolved volume (actual handling view)
        resolved_vol = core.groupby("resolving_team")["ticket_id"].count().to_dict()

        # Unique teams
        all_teams = sorted(set(list(assigned_vol.keys()) + list(resolved_vol.keys())))

        months_in_period = 18.0  # Jan 2025 - Jun 2026
        results = []

        for team in all_teams:
            asgn = assigned_vol.get(team, 0)
            res = resolved_vol.get(team, 0)
            hc = roster_headcount.get(team, 0)
            active_hc = active_agents.get(team, 0)
            tier = 2 if "Escalations" in team else 1

            team_tickets = core[core["resolving_team"] == team]
            open_pending = (team_tickets["status"].isin(["open", "pending"])).sum()

            monthly_avg_res = res / months_in_period
            tickets_per_agent_mo = monthly_avg_res / hc if hc > 0 else 0.0

            results.append({
                "team": team,
                "tier": tier,
                "roster_headcount": hc,
                "active_observed_agents": active_hc,
                "assigned_volume": asgn,
                "resolved_volume": res,
                "net_volume_delta": res - asgn,
                "monthly_avg_resolved": round(monthly_avg_res, 1),
                "monthly_tickets_per_agent": round(tickets_per_agent_mo, 1),
                "open_pending_backlog": int(open_pending)
            })

        return pd.DataFrame(results)

    @staticmethod
    def compute_routing_matrix(
        tickets_df: pd.DataFrame,
        agents_df: pd.DataFrame,
        start_date: str = "2025-01-01",
        end_date: str = "2026-06-30"
    ) -> pd.DataFrame:
        """Generate crosstab of initial assigned team vs actual resolving team.

        Args:
            tickets_df: Tickets DataFrame.
            agents_df: Agents roster DataFrame.
            start_date: Inclusive start date.
            end_date: Inclusive end date.

        Returns:
            Crosstab DataFrame showing routing leakage.
        """
        df = tickets_df.copy()
        df["created_dt"] = pd.to_datetime(df["created_at"])
        core = df[(df["created_dt"] >= start_date) & (df["created_dt"] <= f"{end_date} 23:59:59")].copy()

        if "resolving_team" not in core.columns:
            core = core.merge(
                agents_df[["agent_id", "team"]].rename(columns={"team": "resolving_team"}),
                on="agent_id",
                how="left"
            )

        return pd.crosstab(
            core["assigned_team"],
            core["resolving_team"],
            rownames=["Initial Assigned Team"],
            colnames=["Actual Resolving Team"],
            margins=True
        )

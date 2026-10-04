"""Data loading, caching, filtering, and currency formatting service for Streamlit UI.

Maintains strict fidelity to audited metrics and Operating Policy v3.2 standards.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
import numpy as np
import streamlit as st


def get_base_dir() -> Path:
    """Resolve the project base directory reliably regardless of invocation path."""
    current = Path(__file__).resolve()
    # Path is src/ui/data_service.py -> parent.parent.parent is vireo-support-intelligence
    return current.parent.parent.parent


@st.cache_data(show_spinner="Loading support operations datasets...")
def load_and_preprocess_all() -> Dict[str, pd.DataFrame]:
    """Load and preprocess all datasets with cached execution.

    Applies:
    - Legacy Freshdesk resolution timestamp normalization (+05:30)
    - Resolving agent roster metadata enrichment via agent_id
    - First-response SLA breach detection against Policy §3 standards
    - Duration calculations (response time, active handle time, total resolution time)
    - Repeat contact detection (30-day window proxy)
    - Core 18-month window flag (2025-01-01 to 2026-06-30)

    Returns:
        Dictionary containing preprocessed DataFrames for tickets, agents, orders, and products.
    """
    base = get_base_dir()
    tickets_path = base / "data" / "processed" / "classified_tickets.csv"
    agents_path = base / "data" / "raw" / "agents.csv"
    orders_path = base / "data" / "raw" / "orders.csv"
    products_path = base / "data" / "raw" / "products.csv"

    tickets = pd.read_csv(tickets_path)
    agents = pd.read_csv(agents_path)
    orders = pd.read_csv(orders_path)
    products = pd.read_csv(products_path)

    # Convert datetimes
    tickets["created_dt"] = pd.to_datetime(tickets["created_at"])
    tickets["first_response_dt"] = pd.to_datetime(tickets["first_response_at"])
    tickets["resolved_dt"] = pd.to_datetime(tickets["resolved_at"])

    # Legacy Freshdesk offset correction (+05:30) on resolved_dt
    legacy_mask = (tickets["source_system"] == "legacy_fd") & (tickets["resolved_dt"].notna())
    tickets.loc[legacy_mask, "resolved_dt"] = tickets.loc[legacy_mask, "resolved_dt"] + pd.Timedelta(hours=5, minutes=30)

    # Enrich with agent metadata strictly on agent_id
    agent_info = agents[["agent_id", "team", "tier", "site", "shift", "name"]].rename(
        columns={
            "team": "resolving_team",
            "tier": "resolving_tier",
            "site": "resolving_site",
            "shift": "resolving_shift",
            "name": "resolving_agent_name"
        }
    )
    tickets = tickets.merge(agent_info, on="agent_id", how="left")

    # Calculate response, handle, and total resolution times
    tickets["resp_time_hrs"] = (tickets["first_response_dt"] - tickets["created_dt"]).dt.total_seconds() / 3600.0
    tickets["handle_time_hrs"] = np.where(
        tickets["resolved_dt"].notna(),
        (tickets["resolved_dt"] - tickets["first_response_dt"]).dt.total_seconds() / 3600.0,
        np.nan
    )
    tickets["total_res_time_hrs"] = np.where(
        tickets["resolved_dt"].notna(),
        (tickets["resolved_dt"] - tickets["created_dt"]).dt.total_seconds() / 3600.0,
        np.nan
    )

    # Policy §3 SLA targets
    sla_targets = {"chat": 0.25, "voice": 2.0, "social": 4.0, "email": 8.0}
    tickets["sla_target_hrs"] = tickets["channel"].str.lower().map(sla_targets)
    tickets["is_sla_breach"] = tickets["resp_time_hrs"] > tickets["sla_target_hrs"]
    tickets["sla_penalty_inr"] = np.where(tickets["is_sla_breach"], 350.0, 0.0)

    # Year-month string
    tickets["year_month"] = tickets["created_dt"].dt.to_period("M").astype(str)

    # Core 18-month window flag (1 Jan 2025 to 30 Jun 2026)
    core_mask = (tickets["created_dt"] >= "2025-01-01") & (tickets["created_dt"] <= "2026-06-30 23:59:59")
    tickets["in_core_18m"] = core_mask

    # Repeat contact proxy calculation (evaluated strictly within core window to match audited monthly engine)
    tickets["is_repeat_contact_30d"] = False

    # Compute for core 18-month tickets strictly within the core population (11,641)
    core_tickets = tickets[core_mask].sort_values(["customer_id", "created_dt"]).copy()
    core_tickets["prev_resolved_dt"] = core_tickets.groupby("customer_id")["resolved_dt"].shift(1)
    core_tickets["days_since_prev_res"] = (
        core_tickets["created_dt"] - core_tickets["prev_resolved_dt"]
    ).dt.total_seconds() / (24 * 3600.0)
    core_is_repeat = (
        (core_tickets["days_since_prev_res"] >= 0) & (core_tickets["days_since_prev_res"] <= 30)
    )
    tickets.loc[core_tickets.index, "is_repeat_contact_30d"] = core_is_repeat

    # For non-core tickets (pre-2025 pilot), compute within non-core partition
    non_core_tickets = tickets[~core_mask].sort_values(["customer_id", "created_dt"]).copy()
    if len(non_core_tickets) > 0:
        non_core_tickets["prev_resolved_dt"] = non_core_tickets.groupby("customer_id")["resolved_dt"].shift(1)
        non_core_tickets["days_since_prev_res"] = (
            non_core_tickets["created_dt"] - non_core_tickets["prev_resolved_dt"]
        ).dt.total_seconds() / (24 * 3600.0)
        non_core_is_repeat = (
            (non_core_tickets["days_since_prev_res"] >= 0) & (non_core_tickets["days_since_prev_res"] <= 30)
        )
        tickets.loc[non_core_tickets.index, "is_repeat_contact_30d"] = non_core_is_repeat

    return {
        "tickets": tickets,
        "agents": agents,
        "orders": orders,
        "products": products
    }


def apply_filters(
    tickets_df: pd.DataFrame,
    selected_months: Optional[List[str]] = None,
    selected_categories: Optional[List[str]] = None,
    selected_teams: Optional[List[str]] = None,
    selected_channels: Optional[List[str]] = None,
    selected_statuses: Optional[List[str]] = None,
    use_core_only: bool = True
) -> pd.DataFrame:
    """Filter tickets dataframe according to user selections.

    Args:
        tickets_df: Preprocessed tickets DataFrame.
        selected_months: List of year-month strings (e.g., ['2025-01', '2025-02']).
        selected_categories: List of predicted categories.
        selected_teams: List of resolving teams.
        selected_channels: List of channels (chat, email, etc.).
        selected_statuses: List of ticket statuses (resolved, closed, etc.).
        use_core_only: If True, restrict to core 18M baseline (default: True).

    Returns:
        Filtered DataFrame.
    """
    df = tickets_df.copy()

    if use_core_only:
        df = df[df["in_core_18m"] == True]

    if selected_months:
        df = df[df["year_month"].isin(selected_months)]

    if selected_categories:
        df = df[df["predicted_category"].isin(selected_categories)]

    if selected_teams:
        df = df[df["resolving_team"].isin(selected_teams)]

    if selected_channels:
        df = df[df["channel"].str.lower().isin([c.lower() for c in selected_channels])]

    if selected_statuses:
        df = df[df["status"].isin(selected_statuses)]

    return df


def format_inr(value: float, precision: int = 0) -> str:
    """Format a monetary value in Indian Rupees (INR) with Indian numbering grouping.

    Examples:
        3182240 -> "₹31,82,240"
        452200 -> "₹4,52,200"
    """
    if pd.isna(value):
        return "₹0"
    val = round(value, precision)
    is_neg = val < 0
    val_str = str(abs(int(val)))

    if len(val_str) <= 3:
        formatted = val_str
    else:
        last3 = val_str[-3:]
        remaining = val_str[:-3]
        # Group by 2 digits for remaining
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted = ",".join(groups) + "," + last3

    if precision > 0:
        dec = f"{abs(val) - abs(int(val)):.{precision}f}"[1:]
        formatted += dec

    prefix = "-₹" if is_neg else "₹"
    return f"{prefix}{formatted}"


def format_lakh(value: float) -> str:
    """Format large INR numbers in Lakhs.

    Example:
        3182240 -> "₹31.82 Lakh"
        900000 -> "₹9.00 Lakh"
    """
    if pd.isna(value):
        return "₹0.00 Lakh"
    lakhs = value / 100000.0
    return f"₹{lakhs:.2f} Lakh"

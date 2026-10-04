"""Financial operations and support cost modeling for Vireo Audio Support Intelligence.

Implements Operating Policy v3.2 cost standards: channel contact rates, transfer costs,
SLA credit penalties, repeat-contact waste, dual-disbursement leakage, and hiring ROI.
Strictly avoids double-counting across cost categories.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class FinancialAuditor:
    """Calculates support operational costs, SLA penalties, and process improvement ROI."""

    # Policy §4 Planning Cost Standards
    CHANNEL_COSTS = {
        "chat": 210.0,
        "email": 260.0,
        "voice": 520.0,
        "social": 240.0
    }
    BLENDED_CHANNEL_COST = 290.0
    TRANSFER_COST_INR = 305.0
    SLA_BREACH_CREDIT_INR = 350.0
    AGENT_HOURLY_RATE_INR = 165.0
    ANNUAL_TWO_HIRES_BUDGET_INR = 900000.0
    REPLACEMENT_LOGISTICS_SURCHARGE_INR = 340.0

    @classmethod
    def compute_inbound_channel_costs(cls, core_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate historical inbound handling costs across channels.

        Args:
            core_df: Filtered tickets DataFrame for the core 18-month window.

        Returns:
            Dictionary with breakdown by channel and total inbound expenditure.
        """
        breakdown = {}
        total_cost = 0.0

        for ch, rate in cls.CHANNEL_COSTS.items():
            count = int((core_df["channel"].str.lower() == ch).sum())
            cost = count * rate
            total_cost += cost
            breakdown[ch] = {
                "unit_rate_inr": rate,
                "ticket_count": count,
                "total_cost_inr": cost
            }

        return {
            "channel_breakdown": breakdown,
            "total_inbound_cost_inr": total_cost,
            "blended_effective_cost_inr": round(total_cost / len(core_df), 2) if len(core_df) > 0 else 0.0
        }

    @classmethod
    def compute_sla_breach_penalties(cls, core_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate automatic store credit liabilities issued for first-response SLA breaches.

        Args:
            core_df: Enriched tickets DataFrame with is_sla_breach flag.

        Returns:
            Dictionary with breach counts, rate, and total store credit liabilities.
        """
        breaches = int(core_df["is_sla_breach"].sum())
        total = len(core_df)
        total_credit = breaches * cls.SLA_BREACH_CREDIT_INR

        by_team = {}
        if "resolving_team" in core_df.columns:
            for team, grp in core_df.groupby("resolving_team"):
                team_breaches = int(grp["is_sla_breach"].sum())
                by_team[team] = {
                    "breaches": team_breaches,
                    "credit_inr": team_breaches * cls.SLA_BREACH_CREDIT_INR,
                    "breach_rate_pct": round(team_breaches / len(grp) * 100, 2) if len(grp) > 0 else 0.0
                }

        return {
            "total_breaches": breaches,
            "overall_breach_rate_pct": round(breaches / total * 100, 2) if total > 0 else 0.0,
            "total_store_credit_liability_inr": total_credit,
            "team_breakdown": by_team
        }

    @classmethod
    def compute_transfer_costs(cls, core_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate internal hand-off re-handling costs (Policy §4: ₹305/transfer).

        Only calculated on post-migration helpdesk tickets where transfers are observable.

        Args:
            core_df: Tickets DataFrame.

        Returns:
            Dictionary of observable transfer volumes and administrative re-handling costs.
        """
        hd_tickets = core_df[core_df["source_system"] == "helpdesk"]
        total_transfers = float(hd_tickets["transfers"].sum())
        total_cost = total_transfers * cls.TRANSFER_COST_INR

        by_team = {}
        if "resolving_team" in hd_tickets.columns:
            for team, grp in hd_tickets.groupby("resolving_team"):
                team_transfers = float(grp["transfers"].sum())
                by_team[team] = {
                    "observable_transfers": int(team_transfers),
                    "transfer_cost_inr": team_transfers * cls.TRANSFER_COST_INR
                }

        return {
            "helpdesk_tickets_evaluated": len(hd_tickets),
            "total_observable_transfers": int(total_transfers),
            "total_transfer_cost_inr": total_cost,
            "team_breakdown": by_team
        }

    @classmethod
    def compute_repeat_contact_costs(cls, core_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate avoidable channel handling costs caused by repeat contacts within 30 days.

        Args:
            core_df: Enriched tickets DataFrame with is_repeat_contact_30d flag.

        Returns:
            Dictionary with repeat contact counts and channel costs.
        """
        repeats = core_df[core_df["is_repeat_contact_30d"] == True]
        total_repeat_count = len(repeats)
        total_repeat_cost = 0.0
        by_channel = {}

        for ch, rate in cls.CHANNEL_COSTS.items():
            ch_count = int((repeats["channel"].str.lower() == ch).sum())
            ch_cost = ch_count * rate
            total_repeat_cost += ch_cost
            by_channel[ch] = {
                "count": ch_count,
                "cost_inr": ch_cost
            }

        return {
            "total_repeat_contacts": total_repeat_count,
            "repeat_contact_rate_pct": round(total_repeat_count / len(core_df) * 100, 2) if len(core_df) > 0 else 0.0,
            "total_repeat_cost_inr": total_repeat_cost,
            "channel_breakdown": by_channel
        }

    @classmethod
    def compute_dual_disbursement_leakage(
        cls,
        tickets_df: pd.DataFrame,
        products_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate unrecovered financial leakage from orders receiving BOTH a refund and replacement.

        Direct violation of Operating Policy §5.

        Args:
            tickets_df: Full tickets DataFrame.
            products_df: Products catalog DataFrame with unit_cost_inr.

        Returns:
            Dictionary with order count, refund value, replacement unit value, and total exposure.
        """
        valid_orders = tickets_df[tickets_df["order_id"].notna()].copy()
        sku_cost_map = products_df.set_index("sku")["unit_cost_inr"].to_dict()

        refund_orders = valid_orders[valid_orders["refund_amount_inr"] > 0].groupby("order_id")["refund_amount_inr"].sum()
        repl_orders = valid_orders[valid_orders["replacement_issued"] == "Y"].groupby("order_id")["product_sku"].first()

        violating_orders = set(refund_orders.index).intersection(set(repl_orders.index))
        order_count = len(violating_orders)

        total_refund_val = sum(refund_orders[ord_id] for ord_id in violating_orders)
        total_repl_val = 0.0

        for ord_id in violating_orders:
            sku = repl_orders[ord_id]
            unit_cost = sku_cost_map.get(sku, 1400.0)
            total_repl_val += (unit_cost + cls.REPLACEMENT_LOGISTICS_SURCHARGE_INR)

        return {
            "violating_order_count": order_count,
            "total_refund_disbursed_inr": total_refund_val,
            "total_replacement_cost_inr": total_repl_val,
            "total_dual_leakage_exposure_inr": total_refund_val + total_repl_val
        }

    @classmethod
    def compute_process_improvement_opportunity(
        cls,
        core_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Model financial impact of fixing bot routing and eliminating Billing-to-Logistics leakage.

        Separates observed historical costs from estimated avoidable waste and hypothetical savings.

        Args:
            core_df: Enriched tickets DataFrame for core 18-month window.

        Returns:
            Dictionary modeling process improvement vs. hiring scenarios.
        """
        # Tickets assigned to Billing but resolved by Logistics in core window
        misrouted_billing = core_df[
            (core_df["assigned_team"] == "Billing") & (core_df["resolving_team"] == "Logistics")
        ]
        misrouted_count = len(misrouted_billing)

        # Direct transfer cost saved if routed directly at intake (₹305/transfer)
        direct_transfer_savings = misrouted_count * cls.TRANSFER_COST_INR

        # SLA breach penalty associated with these misrouted tickets
        breaching_misrouted = int(misrouted_billing["is_sla_breach"].sum())
        avoidable_sla_penalties = breaching_misrouted * cls.SLA_BREACH_CREDIT_INR

        # Total direct process opportunity over 18 months
        total_18m_opportunity = direct_transfer_savings + avoidable_sla_penalties
        annualized_opportunity = (total_18m_opportunity / 18.0) * 12.0

        return {
            "misrouted_billing_to_logistics_count_18m": misrouted_count,
            "direct_transfer_waste_18m_inr": direct_transfer_savings,
            "avoidable_sla_penalties_18m_inr": avoidable_sla_penalties,
            "total_process_waste_18m_inr": total_18m_opportunity,
            "annualized_process_improvement_opportunity_inr": round(annualized_opportunity, 2),
            "two_hires_annual_budget_inr": cls.ANNUAL_TWO_HIRES_BUDGET_INR,
            "process_savings_vs_two_hires_pct": round(annualized_opportunity / cls.ANNUAL_TWO_HIRES_BUDGET_INR * 100, 2)
        }

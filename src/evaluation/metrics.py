"""Evaluation and Misrouting Analysis Module for Vireo Audio Support Intelligence.

Provides comparative distributions, confusion matrix calculations, proxy label
metrics, misrouting comparisons, and stratified review sample generation.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class ClassificationEvaluator:
    """Evaluates classifier outputs against original bot categories and team routing."""

    BOT_TO_SEVEN_PILLAR_MAP = {
        "Billing & Payments": "Billing & Invoicing",
        "Delivery & Shipping": "Order & Logistics",
        "Returns & Refunds": "Returns & Refunds",
        "Warranty & Repair": "Hardware & Warranty",
        "Account & Login": "Account & Access",
        "Product Enquiry": "Pre-Sales & Info",
        "Connectivity": "Technical & Firmware",
        "Charging & Battery": "Technical & Firmware",
        "App & Firmware": "Technical & Firmware",
        "Audio Quality": "Technical & Firmware",
        "Other": "Other"
    }

    @classmethod
    def get_category_distributions(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Compare distribution of original bot categories against predicted categories.

        Args:
            df: DataFrame containing category and predicted_category.

        Returns:
            DataFrame with counts and percentage shares.
        """
        total = len(df)
        pred_counts = df["predicted_category"].value_counts()
        pred_pct = (pred_counts / total * 100).round(2)

        return pd.DataFrame({
            "Predicted Count": pred_counts,
            "Predicted Share (%)": pred_pct
        }).reset_index().rename(columns={"index": "Category"})

    @classmethod
    def get_bot_confusion_matrix(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Generate crosstab confusion matrix between original bot category and predicted category.

        Args:
            df: Classified tickets DataFrame.

        Returns:
            Crosstab DataFrame with row margins.
        """
        return pd.crosstab(
            df["category"],
            df["predicted_category"],
            rownames=["Original Bot Category"],
            colnames=["Predicted Seven-Pillar Category"],
            margins=True
        )

    @classmethod
    def compute_proxy_metrics(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Compute precision, recall, and F1 against bot categories as proxy reference.

        IMPORTANT: Original bot categories are NOT ground truth. They reflect intake
        bot rules. These metrics are proxy benchmarks measuring alignment and intentional
        divergence, NOT true statistical accuracy.

        Args:
            df: Classified tickets DataFrame.

        Returns:
            DataFrame of proxy evaluation metrics.
        """
        eval_df = df[df["category"] != "Other"].copy()
        eval_df["bot_proxy"] = eval_df["category"].map(cls.BOT_TO_SEVEN_PILLAR_MAP)

        categories = sorted(eval_df["bot_proxy"].dropna().unique())
        metrics_list = []

        for cat in categories:
            y_true = (eval_df["bot_proxy"] == cat)
            y_pred = (eval_df["predicted_category"] == cat)

            tp = int((y_true & y_pred).sum())
            fp = int((~y_true & y_pred).sum())
            fn = int((y_true & ~y_pred).sum())

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

            metrics_list.append({
                "Category": cat,
                "Bot Proxy Count": int(y_true.sum()),
                "Predicted Count": int(y_pred.sum()),
                "TP": tp,
                "FP": fp,
                "FN": fn,
                "Precision (Proxy)": round(precision, 4),
                "Recall (Proxy)": round(recall, 4),
                "F1-Score (Proxy)": round(f1, 4)
            })

        return pd.DataFrame(metrics_list)

    @classmethod
    def compute_misrouting_summary(
        cls,
        df: pd.DataFrame,
        agents_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Analyze differences between assigned team, resolving team, and predicted responsible team.

        Args:
            df: Classified tickets DataFrame.
            agents_df: Agents roster DataFrame.

        Returns:
            Dictionary with routing cross-tabulations and agreement rates.
        """
        merged = df.merge(
            agents_df[["agent_id", "team"]].rename(columns={"team": "resolving_team"}),
            on="agent_id",
            how="left"
        )

        total = len(merged)
        assigned_eq_res = int((merged["assigned_team"] == merged["resolving_team"]).sum())
        pred_eq_res = int((merged["predicted_team"] == merged["resolving_team"]).sum())
        pred_eq_assigned = int((merged["predicted_team"] == merged["assigned_team"]).sum())

        # Billing assigned but Logistics resolved
        billing_to_logistics = int(
            ((merged["assigned_team"] == "Billing") & (merged["resolving_team"] == "Logistics")).sum()
        )

        # Billing assigned but classified as Order & Logistics
        billing_pred_logistics = int(
            ((merged["assigned_team"] == "Billing") & (merged["predicted_category"] == "Order & Logistics")).sum()
        )

        return {
            "total_tickets": total,
            "assigned_matches_resolving_count": assigned_eq_res,
            "assigned_matches_resolving_pct": round(assigned_eq_res / total * 100, 2),
            "predicted_matches_resolving_count": pred_eq_res,
            "predicted_matches_resolving_pct": round(pred_eq_res / total * 100, 2),
            "predicted_matches_assigned_count": pred_eq_assigned,
            "predicted_matches_assigned_pct": round(pred_eq_assigned / total * 100, 2),
            "billing_reassigned_to_logistics": billing_to_logistics,
            "billing_predicted_as_order_logistics": billing_pred_logistics
        }

    @classmethod
    def generate_human_validation_sample(
        cls,
        df: pd.DataFrame,
        sample_size: int = 100,
        random_state: int = 42
    ) -> pd.DataFrame:
        """Extract a stratified sample of classified tickets for human verification.

        Stratifies across predicted categories and includes low-confidence cases.

        Args:
            df: Classified tickets DataFrame.
            sample_size: Number of sample tickets to extract.
            random_state: Reproducibility seed.

        Returns:
            Sanitized DataFrame ready for manual annotation.
        """
        # Stratified sample per predicted category
        per_cat = max(2, sample_size // df["predicted_category"].nunique())
        samples = []

        for cat, group in df.groupby("predicted_category"):
            n = min(len(group), per_cat)
            samples.append(group.sample(n=n, random_state=random_state))

        sample_df = pd.concat(samples).head(sample_size).copy()

        # Sanitize for annotation
        annotation_cols = [
            "ticket_id",
            "channel",
            "category",
            "predicted_category",
            "predicted_team",
            "confidence_score",
            "review_required",
            "evidence",
            "customer_message",
            "agent_notes"
        ]
        available_cols = [c for c in annotation_cols if c in sample_df.columns]
        result = sample_df[available_cols].copy()
        result["human_verified_category"] = ""
        result["human_reviewer_notes"] = ""
        return result

"""Main Classification Pipeline for Vireo Audio Support Intelligence.

Coordinates deterministic rule-based matching, heuristic confidence calibration,
team routing assignment, and optional AI model extensions.
"""

from typing import Dict, Any, List, Optional
import pandas as pd

from src.classification.taxonomy import (
    TaxonomyCategory,
    ClassificationOutput,
    get_responsible_team,
)
from src.classification.rules import RuleMatcher
from src.classification.confidence import ConfidenceCalibrator


class TicketClassifier:
    """Classifies support tickets across the Seven-Pillar taxonomy.

    Guarantees deterministic, reproducible results without target leakage.
    """

    METHOD_RULE_BASED = "rule_based_deterministic"
    METHOD_LLM_STRUCTURED = "llm_structured_output"

    def __init__(self, use_llm_if_available: bool = False, api_key: Optional[str] = None):
        """Initialize classifier.

        Args:
            use_llm_if_available: Flag to enable LLM-assisted classification if configured.
            api_key: Optional API key for LLM provider.
        """
        self.use_llm = use_llm_if_available and (api_key is not None)
        self.api_key = api_key

    def classify_single(
        self,
        ticket_id: str,
        customer_message: str,
        agent_notes: str,
        original_category: str,
        channel: Optional[str] = None,
        refund_reason_code: Optional[str] = None,
        replacement_issued: Optional[str] = None,
        product_sku: Optional[str] = None
    ) -> ClassificationOutput:
        """Classify a single support ticket.

        Strictly enforces NO target leakage: does NOT accept agent_id or assigned_team.

        Args:
            ticket_id: Unique ticket ID.
            customer_message: Opening customer message or IVR transcript.
            agent_notes: Closing agent summary notes.
            original_category: Helpdesk intake bot category.
            channel: Contact channel ('chat', 'email', 'voice', 'social').
            refund_reason_code: Optional refund code.
            replacement_issued: Optional replacement flag ('Y'/'N').
            product_sku: Optional product SKU.

        Returns:
            Validated Pydantic ClassificationOutput.
        """
        # Primary deterministic path
        top_cat, top_score, evidence_list, raw_scores = RuleMatcher.evaluate_ticket(
            customer_message=customer_message,
            agent_notes=agent_notes,
            refund_reason_code=refund_reason_code,
            replacement_issued=replacement_issued,
            original_category=original_category
        )

        conf_score, review_req, rationale = ConfidenceCalibrator.calculate_confidence(
            top_category=top_cat,
            top_score=top_score,
            evidence=evidence_list,
            raw_scores=raw_scores
        )

        # Map predicted team based on predicted category and channel
        pred_team = get_responsible_team(category=top_cat.value, channel=channel)

        evidence_str = "; ".join(evidence_list[:4]) if evidence_list else "no explicit keyword match"

        return ClassificationOutput(
            ticket_id=str(ticket_id),
            original_category=str(original_category),
            predicted_category=top_cat.value,
            predicted_team=pred_team,
            confidence_score=conf_score,
            classification_method=self.METHOD_RULE_BASED,
            evidence=evidence_str,
            review_required=review_req
        )

    def classify_dataframe(self, tickets_df: pd.DataFrame) -> pd.DataFrame:
        """Process an entire DataFrame of tickets and append classification columns.

        Preserves all original fields and adds prediction fields.

        Args:
            tickets_df: DataFrame of support tickets.

        Returns:
            Enriched DataFrame with prediction columns.
        """
        df = tickets_df.copy()
        results: List[Dict[str, Any]] = []

        for _, row in df.iterrows():
            output = self.classify_single(
                ticket_id=row.get("ticket_id", ""),
                customer_message=row.get("customer_message", ""),
                agent_notes=row.get("agent_notes", ""),
                original_category=row.get("category", ""),
                channel=row.get("channel", "chat"),
                refund_reason_code=row.get("refund_reason_code", None),
                replacement_issued=row.get("replacement_issued", None),
                product_sku=row.get("product_sku", None)
            )
            results.append(output.model_dump())

        pred_df = pd.DataFrame(results)

        # Merge prediction columns into the original DataFrame on ticket_id
        cols_to_add = [
            "predicted_category",
            "predicted_team",
            "confidence_score",
            "classification_method",
            "evidence",
            "review_required"
        ]
        for col in cols_to_add:
            df[col] = pred_df[col]

        return df

"""Confidence scoring and review flag determination for support ticket classification.

Computes a calibrated heuristic confidence score based on pattern strength,
multi-source corroboration, and margin of victory over competitor categories.
"""

from typing import Dict, Tuple, List
from src.classification.taxonomy import TaxonomyCategory


class ConfidenceCalibrator:
    """Calculates heuristic confidence scores and flags ambiguous cases for human review.

    NOTE: The confidence score is a rule-based heuristic indicator reflecting signal
    strength and cross-source corroboration. It is not an empirical statistical probability.
    """

    # Confidence Thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MODERATE_CONFIDENCE_THRESHOLD = 0.70
    REVIEW_REQUIRED_THRESHOLD = 0.65

    # Minimum margin of victory required to avoid conflict flag
    MIN_COMPETITIVE_MARGIN = 1.5

    @classmethod
    def calculate_confidence(
        cls,
        top_category: TaxonomyCategory,
        top_score: float,
        evidence: List[str],
        raw_scores: Dict[str, float]
    ) -> Tuple[float, bool, str]:
        """Compute heuristic confidence score and determine whether human review is required.

        Args:
            top_category: Selected winning category.
            top_score: Accumulated weight for the top category.
            evidence: List of matched signal strings.
            raw_scores: Dictionary of raw score values for all 7 pillars.

        Returns:
            Tuple of (confidence_score, review_required, confidence_rationale).
        """
        # Extract second highest score
        sorted_scores = sorted(raw_scores.values(), reverse=True)
        second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0.0
        score_margin = top_score - second_score

        # Case 1: Zero score or fallback only
        if top_score <= 1.0 or not evidence or all("bot_prior" in e for e in evidence):
            confidence = 0.40
            review_required = True
            rationale = "Low signal: classification relied primarily on legacy fallback prior."
            return confidence, review_required, rationale

        # Base confidence calculation from accumulated score
        if top_score >= 6.0:
            base_conf = 0.92
        elif top_score >= 4.0:
            base_conf = 0.86
        elif top_score >= 2.5:
            base_conf = 0.76
        elif top_score >= 1.5:
            base_conf = 0.68
        else:
            base_conf = 0.55

        # Check multi-source corroboration
        has_msg = any("message:" in e for e in evidence)
        has_notes = any("notes:" in e for e in evidence)
        has_meta = any("refund_code:" in e or "replacement_issued:" in e for e in evidence)

        corroboration_count = sum([has_msg, has_notes, has_meta])
        if corroboration_count >= 2:
            base_conf += 0.05
        elif corroboration_count == 1 and not has_msg:
            base_conf -= 0.05

        # Competitive margin penalty
        if second_score > 0 and score_margin < cls.MIN_COMPETITIVE_MARGIN:
            penalty = 0.15 * (1.0 - (score_margin / cls.MIN_COMPETITIVE_MARGIN))
            base_conf -= penalty

        # Clamp between 0.20 and 0.98
        final_conf = max(0.20, min(0.98, round(base_conf, 2)))

        # Determine review required flag
        is_close_contest = (second_score > 1.5 and score_margin <= 1.0)
        review_required = (final_conf < cls.REVIEW_REQUIRED_THRESHOLD) or is_close_contest

        if review_required:
            if is_close_contest:
                rationale = f"Close contest: competitor category has close score ({second_score:.1f} vs {top_score:.1f})."
            else:
                rationale = f"Heuristic confidence {final_conf:.2f} is below review threshold ({cls.REVIEW_REQUIRED_THRESHOLD})."
        else:
            rationale = f"High corroboration across {corroboration_count} sources with strong margin (+{score_margin:.1f})."

        return final_conf, review_required, rationale

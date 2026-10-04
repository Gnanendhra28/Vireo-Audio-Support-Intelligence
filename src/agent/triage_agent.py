"""Core Human-in-the-Loop Support Triage Agent for Vireo Audio.

Implements a deterministic, 10-stage advisory triage workflow that evaluates
untrusted customer tickets, extracts intent signals, applies safety & policy
checks, and outputs explainable routing recommendations for human operators.

Strictly read-only: does not mutate tickets, issue refunds, or dispatch replacements.
"""

import re
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from src.classification.taxonomy import (
    TaxonomyCategory,
    TAXONOMY_REGISTRY,
    get_responsible_team,
)
from src.classification.rules import RuleMatcher
from src.classification.confidence import ConfidenceCalibrator
from src.data.validation import DataValidator


class TriageOutcome(str, Enum):
    """Possible governance outcomes from the Support Triage Agent."""
    RECOMMEND = "RECOMMEND"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class ExecutionTraceStep(BaseModel):
    """Individual auditable step in the agent reasoning chain."""
    stage: int = Field(ge=1, le=10, description="Stage number from 1 to 10")
    name: str = Field(description="Name of the execution stage")
    details: str = Field(description="Privacy-safe summary of stage findings")
    passed: bool = Field(description="Whether the stage completed without safety/data faults")


class TriageAgentRequest(BaseModel):
    """Input payload for the Support Triage Agent."""
    ticket_id: str = Field(default="TICK-NEW", description="Unique ticket identifier")
    customer_message: Optional[str] = Field(default="", description="Untrusted customer message or IVR transcript")
    channel: Optional[str] = Field(default="chat", description="Inbound communication channel")
    customer_id: Optional[str] = Field(default=None, description="Customer identifier")
    order_id: Optional[str] = Field(default=None, description="Associated order identifier")
    product_sku: Optional[str] = Field(default=None, description="Product SKU if known")
    original_category: Optional[str] = Field(default=None, description="Intake bot legacy tag")
    refund_reason_code: Optional[str] = Field(default=None, description="Policy §5 refund dropdown code")
    refund_amount: Optional[float] = Field(default=None, description="Refund amount if recorded")
    replacement_issued: Optional[str] = Field(default=None, description="Replacement flag ('Y'/'N')")
    agent_notes: Optional[str] = Field(default=None, description="Agent summary or triage notes")


class TriageAgentResponse(BaseModel):
    """Structured advisory output from the Support Triage Agent."""
    ticket_id: str = Field(description="Unique ticket identifier")
    outcome: TriageOutcome = Field(description="Final operational decision gate")
    recommended_category: Optional[str] = Field(default=None, description="Recommended Seven-Pillar category")
    recommended_team: Optional[str] = Field(default=None, description="Recommended responsible support team")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Calibrated heuristic confidence score")
    review_required: bool = Field(description="Whether human supervisor/operator approval is required")
    review_reasons: List[str] = Field(default_factory=list, description="Specific triggers requiring human review")
    matched_evidence: List[str] = Field(default_factory=list, description="Traceable text signals or metadata cues")
    policy_warnings: List[str] = Field(default_factory=list, description="Policy §5 / §6 compliance warnings")
    security_flags: List[str] = Field(default_factory=list, description="Detected security or prompt-injection alerts")
    information_requests: List[str] = Field(default_factory=list, description="Items needed from customer if incomplete")
    execution_trace: List[ExecutionTraceStep] = Field(default_factory=list, description="Auditable 10-stage execution trace")
    human_action_prompt: str = Field(description="Prescriptive action prompt for the human operator")


class SupportTriageAgent:
    """Production-grade deterministic Support Triage Agent.

    Evaluates support inquiries across 10 controlled stages, ensuring that
    customer text is treated as passive data, policy constraints are audited,
    and human operators retain full operational control.
    """

    # Prompt injection and adversarial syntax patterns
    INJECTION_PATTERNS = [
        re.compile(r"\b(?:ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions|system\s+prompt|disregard\s+(?:previous|all)\s+rules)\b", re.IGNORECASE),
        re.compile(r"\b(?:you\s+are\s+now|new\s+system\s+directive|admin\s+override|jailbreak|bypass\s+policy)\b", re.IGNORECASE),
        re.compile(r"\b(?:issue\s+refund\s+without\s+approval|grant\s+admin\s+privileges|drop\s+table)\b", re.IGNORECASE),
        re.compile(r"\b(?:developer\s+mode|sudo\s+approve|override\s+sla)\b", re.IGNORECASE),
    ]

    # Email and phone masking patterns for PII-safe traces
    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

    @classmethod
    def sanitize_pii(cls, text: Optional[str]) -> str:
        """Mask emails, phone numbers, and truncate long text for safe trace logging."""
        if not text:
            return ""
        s = str(text)
        s = cls.EMAIL_PATTERN.sub("[EMAIL_MASKED]", s)
        s = cls.PHONE_PATTERN.sub("[PHONE_MASKED]", s)
        return DataValidator.mask_pii(s)

    @classmethod
    def evaluate(cls, request: TriageAgentRequest) -> TriageAgentResponse:
        """Execute the 10-stage deterministic triage pipeline.

        Args:
            request: Validated TriageAgentRequest payload.

        Returns:
            TriageAgentResponse with auditable trace and human action prompts.
        """
        trace: List[ExecutionTraceStep] = []
        review_reasons: List[str] = []
        policy_warnings: List[str] = []
        security_flags: List[str] = []
        info_requests: List[str] = []

        raw_msg = (request.customer_message or "").strip()
        safe_msg_preview = cls.sanitize_pii(raw_msg)

        # -------------------------------------------------------------
        # STAGE 1: Input Validation
        # -------------------------------------------------------------
        stage1_passed = True
        is_empty_or_too_short = len(raw_msg) < 5
        has_agent_notes = bool(request.agent_notes and len(request.agent_notes.strip()) >= 5)

        if is_empty_or_too_short and not has_agent_notes:
            stage1_passed = False
            trace.append(ExecutionTraceStep(
                stage=1,
                name="Input Validation",
                details="Customer message is empty or under 5 characters with no agent notes.",
                passed=False
            ))
            info_requests.append("Customer inquiry description is missing or too brief. Request issue details from customer.")
            return TriageAgentResponse(
                ticket_id=request.ticket_id,
                outcome=TriageOutcome.INSUFFICIENT_INFORMATION,
                recommended_category=None,
                recommended_team=None,
                confidence_score=0.0,
                review_required=True,
                review_reasons=["Inquiry text contains insufficient substantive detail for automated routing."],
                matched_evidence=[],
                policy_warnings=[],
                security_flags=[],
                information_requests=info_requests,
                execution_trace=trace,
                human_action_prompt="Request issue description and details from customer before assigning queue."
            )

        trace.append(ExecutionTraceStep(
            stage=1,
            name="Input Validation",
            details=f"Valid input received: {len(raw_msg)} characters. Channel: {request.channel}.",
            passed=True
        ))

        # -------------------------------------------------------------
        # STAGE 2: Security Pattern Detection (Untrusted Text Handling)
        # -------------------------------------------------------------
        injection_found = False
        for pat in cls.INJECTION_PATTERNS:
            if pat.search(raw_msg):
                injection_found = True
                break

        if injection_found:
            security_flags.append(
                "Prompt injection / system override syntax detected in customer message. Text treated strictly as untrusted data."
            )
            review_reasons.append("Security Alert: Customer message contains instruction-override syntax; requires supervisor review.")
            trace.append(ExecutionTraceStep(
                stage=2,
                name="Security Scan",
                details="Adversarial command pattern flagged. Sanitized text locked as passive string literal.",
                passed=False
            ))
        else:
            trace.append(ExecutionTraceStep(
                stage=2,
                name="Security Scan",
                details="No prompt injection or instruction override patterns detected.",
                passed=True
            ))

        # -------------------------------------------------------------
        # STAGE 3: Intent Classification
        # -------------------------------------------------------------
        top_cat, top_score, raw_evidence, raw_scores = RuleMatcher.evaluate_ticket(
            customer_message=raw_msg,
            agent_notes=request.agent_notes or "",
            refund_reason_code=request.refund_reason_code,
            replacement_issued=request.replacement_issued,
            original_category=request.original_category or ""
        )
        rec_category = top_cat.value
        trace.append(ExecutionTraceStep(
            stage=3,
            name="Intent Classification",
            details=f"Evaluated Seven-Pillar patterns. Top category: {rec_category} (Score: {top_score:.1f}).",
            passed=True
        ))

        # -------------------------------------------------------------
        # STAGE 4: Evidence Extraction
        # -------------------------------------------------------------
        cleaned_evidence = [cls.sanitize_pii(e) for e in raw_evidence[:5]]
        trace.append(ExecutionTraceStep(
            stage=4,
            name="Evidence Extraction",
            details=f"Extracted {len(cleaned_evidence)} signal cues: {'; '.join(cleaned_evidence[:2]) if cleaned_evidence else 'None'}.",
            passed=True
        ))

        # -------------------------------------------------------------
        # STAGE 5: Team Recommendation
        # -------------------------------------------------------------
        rec_team = get_responsible_team(category=rec_category, channel=request.channel)
        trace.append(ExecutionTraceStep(
            stage=5,
            name="Team Recommendation",
            details=f"Mapped category '{rec_category}' on channel '{request.channel}' to department: '{rec_team}'.",
            passed=True
        ))

        # -------------------------------------------------------------
        # STAGE 6: Heuristic Confidence Assessment
        # -------------------------------------------------------------
        conf_score, calibrator_review, conf_rationale = ConfidenceCalibrator.calculate_confidence(
            top_category=top_cat,
            top_score=top_score,
            evidence=raw_evidence,
            raw_scores=raw_scores
        )
        trace.append(ExecutionTraceStep(
            stage=6,
            name="Confidence Assessment",
            details=f"Heuristic confidence: {conf_score:.2f} ({conf_rationale}).",
            passed=(conf_score >= ConfidenceCalibrator.REVIEW_REQUIRED_THRESHOLD)
        ))

        if conf_score < ConfidenceCalibrator.REVIEW_REQUIRED_THRESHOLD:
            review_reasons.append(
                f"Low heuristic confidence ({conf_score:.2f} < {ConfidenceCalibrator.REVIEW_REQUIRED_THRESHOLD})."
            )

        # -------------------------------------------------------------
        # STAGE 7: Category Ambiguity Detection
        # -------------------------------------------------------------
        sorted_scores = sorted(raw_scores.values(), reverse=True)
        second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0.0
        score_margin = top_score - second_score
        is_ambiguous = (second_score >= 1.5 and score_margin <= 1.0)

        # Detect intake bot mismatch
        bot_mismatch = (
            request.original_category
            and request.original_category.strip().lower() != "other"
            and request.original_category.strip().lower() != rec_category.lower()
            and top_score >= 2.5
        )

        if is_ambiguous:
            review_reasons.append(
                f"Category Ambiguity: Close competition with runner-up category (Top: {top_score:.1f} vs Runner-up: {second_score:.1f})."
            )
            trace.append(ExecutionTraceStep(
                stage=7,
                name="Ambiguity Detection",
                details=f"Competing intent detected. Score margin: {score_margin:.1f}.",
                passed=False
            ))
        elif bot_mismatch:
            review_reasons.append(
                f"Intake Routing Divergence: Intake bot assigned '{request.original_category}', but evidence strongly indicates '{rec_category}'."
            )
            trace.append(ExecutionTraceStep(
                stage=7,
                name="Ambiguity Detection",
                details=f"Intake mismatch flagged: Bot='{request.original_category}' vs Agent='{rec_category}'.",
                passed=True
            ))
        else:
            trace.append(ExecutionTraceStep(
                stage=7,
                name="Ambiguity Detection",
                details=f"Clear category intent margin (+{score_margin:.1f}).",
                passed=True
            ))

        # -------------------------------------------------------------
        # STAGE 8: Policy & Data Consistency Checks
        # -------------------------------------------------------------
        # Check A: Missing Order ID for Return / Warranty claims
        order_missing = not request.order_id or str(request.order_id).strip() == ""
        if rec_category in [TaxonomyCategory.RETURNS_REFUNDS.value, TaxonomyCategory.HARDWARE_WARRANTY.value]:
            if order_missing:
                policy_warnings.append(
                    "Missing Order ID: Policy §5/§6 requires a verified order ID to process return pickups or RMA claims."
                )
                info_requests.append(
                    "Request valid Order ID / invoice number from customer before initiating physical logistics."
                )
                review_reasons.append("Missing Order ID on post-purchase return/warranty claim.")

        # Check B: Dual-Disbursement Risk (Policy §5)
        # Only flag when supported by concrete evidence (replacement requested/issued + refund active)
        replacement_indicated = (request.replacement_issued == "Y") or any("replacement" in e.lower() for e in raw_evidence)
        refund_indicated = bool(request.refund_reason_code) or (request.refund_amount is not None and request.refund_amount > 0) or any("refund" in e.lower() for e in raw_evidence)

        if replacement_indicated and refund_indicated:
            policy_warnings.append(
                "Dual-Disbursement Risk (Policy §5): Available evidence indicates both refund and replacement activity for the same inquiry."
            )
            review_reasons.append("Policy §5 Audit: Potential dual-disbursement risk requires supervisor review before authorizing financial or hardware dispatch.")

        trace.append(ExecutionTraceStep(
            stage=8,
            name="Policy & Consistency Checks",
            details=f"Policy checks complete. Warnings: {len(policy_warnings)}; Info requests: {len(info_requests)}.",
            passed=(len(policy_warnings) == 0 and len(info_requests) == 0)
        ))

        # -------------------------------------------------------------
        # STAGE 9: Explainability and Execution Trace
        # -------------------------------------------------------------
        trace.append(ExecutionTraceStep(
            stage=9,
            name="Explainability Synthesis",
            details="Trace and evidence synthesized into auditable human-readable decision log.",
            passed=True
        ))

        # -------------------------------------------------------------
        # STAGE 10: Final Human-Review Decision
        # -------------------------------------------------------------
        must_review = bool(
            injection_found
            or (conf_score < ConfidenceCalibrator.REVIEW_REQUIRED_THRESHOLD)
            or is_ambiguous
            or policy_warnings
            or (order_missing and rec_category in [TaxonomyCategory.RETURNS_REFUNDS.value, TaxonomyCategory.HARDWARE_WARRANTY.value])
        )

        if must_review:
            outcome = TriageOutcome.REVIEW_REQUIRED
            primary_reason = review_reasons[0] if review_reasons else "Supervisory review required."
            action_prompt = f"Human Review Required: {primary_reason}. Proposed Queue: {rec_team} ({rec_category})."
        else:
            outcome = TriageOutcome.RECOMMEND
            action_prompt = f"Confident Advisory Recommendation: Operator may approve routing to {rec_team} ({rec_category})."

        trace.append(ExecutionTraceStep(
            stage=10,
            name="Decision Gate",
            details=f"Final Outcome: {outcome.value}. Human review required: {must_review}.",
            passed=True
        ))

        return TriageAgentResponse(
            ticket_id=request.ticket_id,
            outcome=outcome,
            recommended_category=rec_category,
            recommended_team=rec_team,
            confidence_score=conf_score,
            review_required=must_review,
            review_reasons=review_reasons,
            matched_evidence=cleaned_evidence,
            policy_warnings=policy_warnings,
            security_flags=security_flags,
            information_requests=info_requests,
            execution_trace=trace,
            human_action_prompt=action_prompt
        )

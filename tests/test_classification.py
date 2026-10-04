"""Unit tests for the AI-assisted classification engine and taxonomy.

Covers:
- All 7 taxonomy categories
- Unknown, ambiguous, and empty text
- Missing optional attributes
- Confidence boundaries [0.0, 1.0]
- Pydantic schema validation
- Target leakage verification
- Ticket ID preservation
- Deterministic reproducibility
"""

import pytest
import pandas as pd
from src.classification.taxonomy import (
    TaxonomyCategory,
    ClassificationOutput,
    TAXONOMY_REGISTRY,
    get_responsible_team,
)
from src.classification.rules import RuleMatcher
from src.classification.confidence import ConfidenceCalibrator
from src.classification.classifier import TicketClassifier


@pytest.fixture
def classifier():
    """Create a standard deterministic TicketClassifier instance."""
    return TicketClassifier()


def test_taxonomy_registry_complete():
    """Verify all 7 categories are registered with complete specifications."""
    assert len(TAXONOMY_REGISTRY) == 7
    for cat in TaxonomyCategory:
        assert cat in TAXONOMY_REGISTRY
        defn = TAXONOMY_REGISTRY[cat]
        assert defn.name == cat.value
        assert len(defn.inclusion_criteria) > 0
        assert len(defn.exclusion_criteria) > 0
        assert len(defn.representative_examples) > 0
        assert len(defn.responsible_team) > 0


@pytest.mark.parametrize("message,notes,expected_cat", [
    ("Where is my order? Tracking has not updated for 5 days.", "cx asks for awb status. dlvry delayed.", TaxonomyCategory.ORDER_LOGISTICS),
    ("Nobody came for the return pickup of my earbuds.", "reverse pkp rescheduled with courier.", TaxonomyCategory.RETURNS_REFUNDS),
    ("I was charged twice on my card for this order.", "checked pg logs. duplicate txn confirmed. refund approved.", TaxonomyCategory.BILLING_INVOICING),
    ("Bluetooth pairing fails every time I turn it on.", "walked cx through reset. re-pair successful.", TaxonomyCategory.TECHNICAL_FIRMWARE),
    ("Earbud is completely dead after water exposure, claim rma82419.", "rma shared with cx. replacement raised.", TaxonomyCategory.HARDWARE_WARRANTY),
    ("OTP is not arriving on my phone, locked out of account.", "otp resent. account unlocked.", TaxonomyCategory.ACCOUNT_ACCESS),
    ("Can I swim with the Pulse 2? Is it waterproof?", "shared spec sheet with cx. confirmed ipx7 rating.", TaxonomyCategory.PRE_SALES_INFO),
])
def test_all_seven_categories_classified(classifier, message, notes, expected_cat):
    """Verify each taxonomy category is accurately identified with clear signals."""
    result = classifier.classify_single(
        ticket_id="TEST-001",
        customer_message=message,
        agent_notes=notes,
        original_category="Other"
    )
    assert result.predicted_category == expected_cat.value
    assert result.confidence_score >= 0.70
    assert not result.review_required


def test_empty_and_null_messages(classifier):
    """Verify graceful handling and review flag for empty or null messages."""
    res_empty = classifier.classify_single(
        ticket_id="TEST-EMPTY",
        customer_message="",
        agent_notes="",
        original_category="Billing & Payments"
    )
    assert isinstance(res_empty, ClassificationOutput)
    assert res_empty.review_required is True
    assert res_empty.confidence_score <= 0.65

    res_none = classifier.classify_single(
        ticket_id="TEST-NONE",
        customer_message=None,
        agent_notes=None,
        original_category="Delivery & Shipping"
    )
    assert isinstance(res_none, ClassificationOutput)
    assert res_none.review_required is True


def test_ambiguous_and_unknown_text(classifier):
    """Verify that ambiguous gibberish text triggers the review_required flag."""
    res = classifier.classify_single(
        ticket_id="TEST-GIBBERISH",
        customer_message="asldkfj asdf qwer zxcvbnm",
        agent_notes="no notes",
        original_category="Other"
    )
    assert res.review_required is True
    assert res.confidence_score <= 0.65


def test_missing_optional_fields(classifier):
    """Verify classifier executes seamlessly when optional metadata fields are missing."""
    res = classifier.classify_single(
        ticket_id="TEST-OPTIONAL",
        customer_message="My package has not been delivered.",
        agent_notes="ord not delivered",
        original_category="Delivery & Shipping",
        channel=None,
        refund_reason_code=None,
        replacement_issued=None,
        product_sku=None
    )
    assert res.predicted_category == "Order & Logistics"
    assert res.predicted_team == "Logistics"


def test_confidence_boundaries(classifier):
    """Verify confidence score is strictly bounded between 0.0 and 1.0."""
    test_cases = [
        ("order not delivered courier lost awb", "dlvry delayed re-shipped"),
        ("hello", "ok"),
        ("", "")
    ]
    for msg, notes in test_cases:
        res = classifier.classify_single(
            ticket_id="T-CONF",
            customer_message=msg,
            agent_notes=notes,
            original_category="Other"
        )
        assert 0.0 <= res.confidence_score <= 1.0


def test_no_target_leakage():
    """Verify that classifier function signature contains no resolver team or agent parameters."""
    import inspect
    sig = inspect.signature(TicketClassifier.classify_single)
    params = sig.parameters.keys()
    assert "agent_id" not in params
    assert "assigned_team" not in params
    assert "resolving_team" not in params
    assert "team" not in params


def test_deterministic_repeated_runs(classifier):
    """Verify identical results on repeated runs for reproducibility."""
    msg = "paid on 19 jun, still waiting for order to arrive. money deducted."
    notes = "cx says ord not delivered. awb checked with crr."

    res1 = classifier.classify_single("T-REPEAT", msg, notes, "Billing & Payments")
    res2 = classifier.classify_single("T-REPEAT", msg, notes, "Billing & Payments")

    assert res1.predicted_category == res2.predicted_category
    assert res1.predicted_team == res2.predicted_team
    assert res1.confidence_score == res2.confidence_score
    assert res1.review_required == res2.review_required
    assert res1.evidence == res2.evidence


def test_dataframe_batch_classification(classifier):
    """Verify batch DataFrame processing preserves ticket IDs and columns."""
    sample_df = pd.DataFrame([
        {"ticket_id": "TK-1", "customer_message": "where is my package", "agent_notes": "awb checked", "category": "Delivery & Shipping", "channel": "chat"},
        {"ticket_id": "TK-2", "customer_message": "charged twice", "agent_notes": "duplicate txn", "category": "Billing & Payments", "channel": "email"}
    ])
    result_df = classifier.classify_dataframe(sample_df)

    assert len(result_df) == 2
    assert list(result_df["ticket_id"]) == ["TK-1", "TK-2"]
    assert "predicted_category" in result_df.columns
    assert "predicted_team" in result_df.columns
    assert "confidence_score" in result_df.columns
    assert "review_required" in result_df.columns
    assert result_df.loc[0, "predicted_category"] == "Order & Logistics"
    assert result_df.loc[1, "predicted_category"] == "Billing & Invoicing"

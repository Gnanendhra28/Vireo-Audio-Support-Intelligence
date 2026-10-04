"""Rule-based pattern matching and feature extraction engine for support ticket classification.

Extracts text signals from customer messages and agent notes, evaluates
metadata indicators (refund reason codes, replacement flags), and calculates
category scores with zero target leakage.
"""

import re
from typing import Dict, List, Tuple, Any, Optional
from src.classification.taxonomy import TaxonomyCategory


class RuleMatcher:
    """Deterministic pattern matching engine across the Seven-Pillar taxonomy."""

    # Weighted regex patterns for customer message signals
    CUSTOMER_PATTERNS = {
        TaxonomyCategory.ORDER_LOGISTICS: [
            (r"\b(?:not\s+delivered|hasn't\s+been\s+delivered|never\s+delivered|haven't\s+received\s+my\s+order)\b", 3.5),
            (r"\b(?:out\s+for\s+delivery|order\s+not\s+delivered|waiting\s+for\s+(?:something\s+to\s+show\s+up|order|parcel|delivery))\b", 3.0),
            (r"\b(?:tracking\s+not\s+updating|tracking\s+stuck|awb|courier\s+will\s+never\s+find|wrong\s+pincode|typo\s+in\s+the\s+flat|change\s+address)\b", 2.5),
            (r"\b(?:where\s+is\s+my\s+(?:order|package|parcel|shipment|delivery|earbuds|watch)|shipment\s+delayed|dispatch\s+delayed)\b", 2.5),
            (r"\b(?:money\s+gone.*item\s+not\s+with\s+me|amount\s+deducted.*nothing\s+at\s+my\s+door|nothing\s+in\s+hand)\b", 2.5),
            (r"\b(?:wrong\s+item|wrong\s+product|received\s+the\s+wrong|box\s+was\s+empty|missing\s+accessory)\b", 2.0),
            (r"\b(?:courier|shipping|transit|dispatch|delayed|delivery|pincode)\b", 1.0),
        ],

        TaxonomyCategory.RETURNS_REFUNDS: [
            (r"\b(?:return\s+pickup|reverse\s+pickup|nobody\s+came\s+for\s+(?:the\s+)?pickup|pickup\s+has\s+not\s+happened|pick-up\s+pending)\b", 3.5),
            (r"\b(?:want\s+to\s+return|send\s+it\s+back|return\s+my\s+money|want\s+(?:a\s+)?full\s+refund|money\s+back|refund\s+not\s+credited)\b", 3.0),
            (r"\b(?:return\s+qc|returned\s+the\s+(?:item|unit|product)|pickup\s+rescheduled|qc\s+pass)\b", 2.5),
            (r"\b(?:refund\s+status|when\s+will\s+i\s+get\s+my\s+refund|refund\s+pending|initiate\s+refund)\b", 2.5),
            (r"\b(?:return|returns|refund|refunds|pickup|reverse)\b", 1.0),
        ],

        TaxonomyCategory.BILLING_INVOICING: [
            (r"\b(?:charged\s+twice|double\s+charge|charged\s+two\s+times|deducted\s+twice|paid\s+twice|duplicate\s+payment|duplicate\s+txn)\b", 3.5),
            (r"\b(?:tax\s+invoice|gst\s+invoice|gstin|firm'?s\s+gstin|need\s+the\s+bill|invoice\s+with\s+gst|send\s+(?:the\s+)?invoice)\b", 3.0),
            (r"\b(?:gateway\s+failed|payment\s+failed\s+but\s+debited|payment\s+error|pg\s+error|debited\s+from\s+bank\s+no\s+order)\b", 2.5),
            (r"\b(?:festive\s+offer\s+vanished|coupon\s+not\s+applied|discount\s+not\s+working|price\s+adjustment|promo\s+code\s+failed)\b", 2.5),
            (r"\b(?:invoice|receipt|gst|bill|coupon|discount|payment\s+gateway)\b", 1.0),
        ],

        TaxonomyCategory.TECHNICAL_FIRMWARE: [
            (r"\b(?:bluetooth\s+pairing|pairing\s+fails|cannot\s+pair|phone\s+doesn't\s+see\s+it|pairing\s+light\s+blinks|disconnects\s+randomly)\b", 3.0),
            (r"\b(?:firmware\s+update\s+stuck|fw\s+update|app\s+crashes|app\s+keeps\s+crashing|companion\s+app\s+fails|update\s+loop)\b", 3.0),
            (r"\b(?:static\s+noise|crackling|distorted\s+sound|mic\s+volume|microphone\s+is\s+very\s+low|single\s+side\s+silent|channel\s+imbalance)\b", 2.5),
            (r"\b(?:won'?t\s+charge\s+in\s+(?:the\s+)?case|battery\s+draining\s+fast|goes\s+from\s+full\s+to\s+empty|rapid\s+battery\s+drain|case\s+does\s+not\s+charge)\b", 2.5),
            (r"\b(?:soft\s+reset|factory\s+reset|reset\s+procedure|pairing|bluetooth|equalizer|audio\s+lag)\b", 1.5),
        ],

        TaxonomyCategory.HARDWARE_WARRANTY: [
            (r"\b(?:warranty\s+claim|rma\s+number|rma\d+|service\s+cent(?:er|re)|claim\s+pending|service\s+center\s+took\s+it)\b", 3.5),
            (r"\b(?:bricked\s+completely|device\s+is\s+dead|zero\s+light\s+at\s+all|completely\s+unresponsive|screen\s+is\s+dead)\b", 3.0),
            (r"\b(?:dead\s+on\s+arrival|doa|swollen\s+battery|physical\s+damage|broken\s+hinge|water\s+damage|burnt\s+smell)\b", 2.5),
            (r"\b(?:replacement\s+unit\s+dispatched|warranty\s+replacement|rma\s+status|in-warranty\s+repair)\b", 2.5),
            (r"\b(?:rma|warranty|depot|defect|hardware|repaired)\b", 1.0),
        ],

        TaxonomyCategory.ACCOUNT_ACCESS: [
            (r"\b(?:otp\s+not\s+coming|not\s+receiving\s+otp|otp\s+never\s+arrives|login\s+code\s+never\s+arrives|sms\s+code\s+not\s+received)\b", 3.5),
            (r"\b(?:locked\s+out\s+of\s+my\s+(?:own\s+)?account|account\s+locked|unable\s+to\s+login|cannot\s+log\s+in|login\s+failed)\b", 3.0),
            (r"\b(?:change\s+(?:registered\s+)?(?:mobile|phone|number|email)|update\s+my\s+phone\s+number|forgot\s+password)\b", 2.5),
            (r"\b(?:otp|login|credentials|unlock\s+account|password\s+reset)\b", 1.0),
        ],

        TaxonomyCategory.PRE_SALES_INFO: [
            (r"\b(?:compatible\s+with|work\s+with\s+(?:my\s+)?(?:iphone|android|tv|laptop|mac|pc|playstation))\b", 3.0),
            (r"\b(?:survive\s+a\s+shower|waterproof|water\s+resistant|can\s+i\s+swim|ipx[4578]\s+rating)\b", 3.0),
            (r"\b(?:can\s+i\s+connect\s+two\s+(?:speakers|orbit|pulse)|difference\s+between|spec\s+sheet|battery\s+specs)\b", 2.5),
            (r"\b(?:pre-sales|specifications|features|before\s+i\s+buy|will\s+this\s+work)\b", 1.5),
        ]
    }

    # Agent closing note corroborating keywords
    AGENT_NOTE_PATTERNS = {
        TaxonomyCategory.ORDER_LOGISTICS: [
            (r"\b(?:dlvry\s+delayed|shipment\s+not\s+rcvd|ord\s+not\s+delivered|awb|crr\s+partner|rto\s+confirmed|re-shipped|lost\s+in\s+transit|xfer\s+to\s+logistics|via\s+logistics|pincode|address\s+updated)\b", 2.5),
        ],
        TaxonomyCategory.RETURNS_REFUNDS: [
            (r"\b(?:reverse\s+pkp|return\s+received|qc\s+ok|return-qc-ok|rfnd\s+initiated|refund\s+approved|pkp\s+rescheduled|xfer\s+to\s+returns\s+desk|via\s+returns\s+desk)\b", 2.5),
        ],
        TaxonomyCategory.BILLING_INVOICING: [
            (r"\b(?:doble\s+charge|duplicate\s+txn|gst\s+invoice|regenerated\s+invoice|pg\s+error|price\s+adjustment|xfer\s+billing|via\s+billing)\b", 2.5),
        ],
        TaxonomyCategory.TECHNICAL_FIRMWARE: [
            (r"\b(?:walked\s+through\s+reset|re-pair\s+successful|permissions\s+fixed|fw\s+\d+\.\d+|app\s+update|sound\s+test|soft\s+reset)\b", 2.5),
        ],
        TaxonomyCategory.HARDWARE_WARRANTY: [
            (r"\b(?:escalated\s+to\s+wty|rma\s+shared|replacement\s+raised|hardware\s+failure|bricked|service\s+center|doa\s+replacement)\b", 2.5),
        ],
        TaxonomyCategory.ACCOUNT_ACCESS: [
            (r"\b(?:otp\s+resent|account\s+unlocked|checked\s+otp\s+logs|number\s+updated|login\s+issue\s+resolved)\b", 2.5),
        ],
        TaxonomyCategory.PRE_SALES_INFO: [
            (r"\b(?:shared\s+spec\s+sheet|pre-sales\s+query|cx\s+satisfied\s+with\s+specs|compatibility\s+confirmed)\b", 2.5),
        ]
    }

    # Metadata signal bonus weights
    REFUND_REASON_SIGNALS = {
        "LOST-TRANSIT": (TaxonomyCategory.ORDER_LOGISTICS, 3.0),
        "RETURN-QC-OK": (TaxonomyCategory.RETURNS_REFUNDS, 3.5),
        "DUP-PAYMENT": (TaxonomyCategory.BILLING_INVOICING, 4.0),
        "PRICE-ADJ": (TaxonomyCategory.BILLING_INVOICING, 3.5),
        "CANCEL": (TaxonomyCategory.ORDER_LOGISTICS, 2.0),
        "DOA-REPL": (TaxonomyCategory.HARDWARE_WARRANTY, 3.5),
        "WTY-BUYBACK": (TaxonomyCategory.HARDWARE_WARRANTY, 3.5),
        "GW-OTHER": (TaxonomyCategory.RETURNS_REFUNDS, 1.0)
    }

    @classmethod
    def evaluate_ticket(
        cls,
        customer_message: str,
        agent_notes: str,
        refund_reason_code: Optional[str] = None,
        replacement_issued: Optional[str] = None,
        original_category: Optional[str] = None
    ) -> Tuple[TaxonomyCategory, float, List[str], Dict[str, float]]:
        """Evaluate a ticket and compute scores across all Seven Pillars.

        Strictly enforces NO target leakage: does NOT inspect agent_id or assigned_team.

        Args:
            customer_message: Opening customer message or IVR transcript.
            agent_notes: Closing agent notes.
            refund_reason_code: Selected refund reason dropdown code.
            replacement_issued: Hardware replacement flag ('Y'/'N').
            original_category: Helpdesk intake bot tag (used only as light tie-break).

        Returns:
            Tuple of (Top Category, Confidence Score, Matched Evidence List, Raw Score Dict).
        """
        scores: Dict[TaxonomyCategory, float] = {cat: 0.0 for cat in TaxonomyCategory}
        evidence_map: Dict[TaxonomyCategory, List[str]] = {cat: [] for cat in TaxonomyCategory}

        msg_clean = str(customer_message).lower() if customer_message else ""
        notes_clean = str(agent_notes).lower() if agent_notes else ""

        # 1. Evaluate customer message patterns
        for cat, pattern_list in cls.CUSTOMER_PATTERNS.items():
            for pat, weight in pattern_list:
                matches = re.findall(pat, msg_clean)
                if matches:
                    scores[cat] += weight * len(matches)
                    evidence_map[cat].append(f"message: '{matches[0]}'")

        # 2. Evaluate agent notes patterns
        for cat, pattern_list in cls.AGENT_NOTE_PATTERNS.items():
            for pat, weight in pattern_list:
                matches = re.findall(pat, notes_clean)
                if matches:
                    scores[cat] += weight * len(matches)
                    evidence_map[cat].append(f"notes: '{matches[0]}'")

        # 3. Evaluate refund reason code
        if refund_reason_code and str(refund_reason_code).strip() in cls.REFUND_REASON_SIGNALS:
            mapped_cat, bonus = cls.REFUND_REASON_SIGNALS[str(refund_reason_code).strip()]
            scores[mapped_cat] += bonus
            evidence_map[mapped_cat].append(f"refund_code: {refund_reason_code}")

        # 4. Evaluate replacement flag
        if str(replacement_issued).strip().upper() == "Y":
            # If notes or message indicate hardware defect/RMA, bonus goes to Hardware
            if scores[TaxonomyCategory.HARDWARE_WARRANTY] > 0 or "rma" in notes_clean or "defect" in notes_clean:
                scores[TaxonomyCategory.HARDWARE_WARRANTY] += 2.0
                evidence_map[TaxonomyCategory.HARDWARE_WARRANTY].append("replacement_issued: Y (hardware)")
            elif "wrong item" in msg_clean or "re-ship" in notes_clean:
                scores[TaxonomyCategory.ORDER_LOGISTICS] += 2.0
                evidence_map[TaxonomyCategory.ORDER_LOGISTICS].append("replacement_issued: Y (reship)")

        # 5. Prior Category tie-breaker (only used if scores are identical or zero)
        max_score = max(scores.values())
        if max_score == 0.0 and original_category:
            # Map legacy bot categories gracefully
            orig_lower = str(original_category).lower()
            if "delivery" in orig_lower or "shipping" in orig_lower:
                scores[TaxonomyCategory.ORDER_LOGISTICS] += 1.0
                evidence_map[TaxonomyCategory.ORDER_LOGISTICS].append("bot_prior: Delivery & Shipping")
            elif "return" in orig_lower or "refund" in orig_lower:
                scores[TaxonomyCategory.RETURNS_REFUNDS] += 1.0
                evidence_map[TaxonomyCategory.RETURNS_REFUNDS].append("bot_prior: Returns & Refunds")
            elif "billing" in orig_lower or "payment" in orig_lower:
                scores[TaxonomyCategory.BILLING_INVOICING] += 1.0
                evidence_map[TaxonomyCategory.BILLING_INVOICING].append("bot_prior: Billing & Payments")
            elif "warranty" in orig_lower or "repair" in orig_lower:
                scores[TaxonomyCategory.HARDWARE_WARRANTY] += 1.0
                evidence_map[TaxonomyCategory.HARDWARE_WARRANTY].append("bot_prior: Warranty & Repair")
            elif "account" in orig_lower or "login" in orig_lower:
                scores[TaxonomyCategory.ACCOUNT_ACCESS] += 1.0
                evidence_map[TaxonomyCategory.ACCOUNT_ACCESS].append("bot_prior: Account & Login")
            elif "enquiry" in orig_lower or "presales" in orig_lower:
                scores[TaxonomyCategory.PRE_SALES_INFO] += 1.0
                evidence_map[TaxonomyCategory.PRE_SALES_INFO].append("bot_prior: Product Enquiry")
            else:
                scores[TaxonomyCategory.TECHNICAL_FIRMWARE] += 0.5
                evidence_map[TaxonomyCategory.TECHNICAL_FIRMWARE].append(f"bot_prior_fallback: {original_category}")

        # Determine winner
        sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_cat, top_score = sorted_cats[0]
        second_score = sorted_cats[1][1] if len(sorted_cats) > 1 else 0.0

        top_evidence = evidence_map[top_cat]
        raw_scores = {k.value: round(v, 2) for k, v in scores.items()}

        return top_cat, top_score, top_evidence, raw_scores

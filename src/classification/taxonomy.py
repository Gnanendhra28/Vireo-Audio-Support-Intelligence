"""Centralized Taxonomy Definition for Vireo Audio Support Intelligence.

Defines the Seven-Pillar Support Issue Taxonomy, category specifications,
inclusion/exclusion criteria, representative examples, responsible teams,
and Pydantic output schemas.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TaxonomyCategory(str, Enum):
    """The Seven Core Pillars of Vireo Audio Support Intent."""
    ORDER_LOGISTICS = "Order & Logistics"
    RETURNS_REFUNDS = "Returns & Refunds"
    BILLING_INVOICING = "Billing & Invoicing"
    TECHNICAL_FIRMWARE = "Technical & Firmware"
    HARDWARE_WARRANTY = "Hardware & Warranty"
    ACCOUNT_ACCESS = "Account & Access"
    PRE_SALES_INFO = "Pre-Sales & Info"


class CategoryDefinition(BaseModel):
    """Detailed specifications and boundary definitions for a taxonomy category."""
    name: str
    description: str
    responsible_team: str
    inclusion_criteria: List[str]
    exclusion_criteria: List[str]
    representative_examples: List[str]
    ambiguous_cases: List[str]


# Centralized Seven-Pillar Taxonomy Configuration
TAXONOMY_REGISTRY: Dict[TaxonomyCategory, CategoryDefinition] = {
    TaxonomyCategory.ORDER_LOGISTICS: CategoryDefinition(
        name="Order & Logistics",
        description="Fulfillment, shipping, courier handover, transit tracking, and physical delivery of orders.",
        responsible_team="Logistics",
        inclusion_criteria=[
            "Order tracking and live status inquiries (AWB, courier partner delays)",
            "Delayed shipment or delivery past estimated arrival date",
            "Out-of-delivery or RTO (Return to Origin) notices",
            "Shipment lost or damaged in transit before initial customer receipt",
            "Delivery address correction, apartment typo, or incorrect pincode",
            "Incorrect item or missing accessories inside the dispatched package"
        ],
        exclusion_criteria=[
            "Customer requesting return pickup after taking successful delivery (use Returns & Refunds)",
            "Duplicate payment or billing dispute with no delivery delay (use Billing & Invoicing)",
            "Hardware defect occurring days after successful unboxing (use Hardware & Warranty)"
        ],
        representative_examples=[
            "Paid on 19 Jun, still waiting for something to show up. Tracking says pending.",
            "My package has been out for delivery for 4 days now. Where is my courier?",
            "Ordered Pulse 2 earbuds, but received a neckband inside the box.",
            "Courier says address incomplete. Need to update my pincode."
        ],
        ambiguous_cases=[
            "Customer claims payment deducted and nothing received: classify as Order & Logistics if payment is confirmed and order was dispatched; classify as Billing & Invoicing if payment failed at gateway.",
            "Package arrived physically crushed: classify as Order & Logistics if reported on delivery day as transit damage; classify as Returns & Refunds if customer requests return pickup."
        ]
    ),

    TaxonomyCategory.RETURNS_REFUNDS: CategoryDefinition(
        name="Returns & Refunds",
        description="Post-delivery customer returns, reverse pickup logistics, warehouse QC inspection, and refund issuance.",
        responsible_team="Returns Desk",
        inclusion_criteria=[
            "Customer-initiated return requests within the return window",
            "Reverse pickup scheduling, delays, or missed courier appointments",
            "Warehouse return receipt and Quality Check (QC) status checks",
            "Refund status, approval, or credit timeline inquiries following a return",
            "Goodwill return authorizations approved by team leads"
        ],
        exclusion_criteria=[
            "Transit loss before first delivery (use Order & Logistics)",
            "Duplicate or gateway payment deduction with no return initiated (use Billing & Invoicing)",
            "Warranty replacement or RMA claim for in-warranty malfunction (use Hardware & Warranty)"
        ],
        representative_examples=[
            "Courier has not arrived for the reverse pickup of my Strata 2 headphones.",
            "Returned the earbuds 5 days ago. When will my refund be credited?",
            "Return pickup completed, but helpdesk shows QC inspection pending.",
            "I want to return this product and get my money back."
        ],
        ambiguous_cases=[
            "Dead on Arrival (DOA) within 7 days: customer chooses full refund -> Returns & Refunds; customer chooses replacement unit -> Hardware & Warranty."
        ]
    ),

    TaxonomyCategory.BILLING_INVOICING: CategoryDefinition(
        name="Billing & Invoicing",
        description="Financial transactions, payment gateway errors, duplicate debits, invoice requests, and tax documentation.",
        responsible_team="Billing",
        inclusion_criteria=[
            "Duplicate transaction charges or double deduction for a single order",
            "Payment gateway failures, timeouts, or debited amounts without order confirmation",
            "Invoice generation, tax invoice download, or GSTIN updates on receipts",
            "Price adjustments, coupon application failures, or discount discrepancies",
            "Direct refund requests due to payment errors"
        ],
        exclusion_criteria=[
            "Confirmed paid orders that are delayed in transit (use Order & Logistics)",
            "Refunds arising from return of physical goods (use Returns & Refunds)",
            "Store credit issues resulting from SLA breaches (use Frontline / Operations)"
        ],
        representative_examples=[
            "I was charged twice on my credit card for order VR906763.",
            "Amount deducted from UPI but website gave an error and no order number was generated.",
            "Please provide a tax invoice with our company GSTIN number.",
            "The festive 15% discount code was not applied during checkout."
        ],
        ambiguous_cases=[
            "Customer says 'money gone, no order': classify as Billing & Invoicing if no order exists in system; classify as Order & Logistics if order exists and is in fulfillment."
        ]
    ),

    TaxonomyCategory.TECHNICAL_FIRMWARE: CategoryDefinition(
        name="Technical & Firmware",
        description="Non-destructive troubleshooting, connectivity, Bluetooth pairing, companion app, and firmware.",
        responsible_team="Chat/Email/Voice Frontline",
        inclusion_criteria=[
            "Bluetooth pairing failures, device discovery issues, or frequent disconnects",
            "Companion mobile app crashing, failing to sync, or feature toggles unresponsive",
            "Firmware update failures, frozen progress bar, or update loops",
            "Audio tuning, static noise, channel balance, latency, or microphone volume",
            "Battery optimization, charging case indicator troubleshooting, or soft resets"
        ],
        exclusion_criteria=[
            "Permanent physical hardware failure or dead components (use Hardware & Warranty)",
            "Account login OTP failures within the app (use Account & Access)",
            "Return requests due to dissatisfaction (use Returns & Refunds)"
        ],
        representative_examples=[
            "Left earbud connects but right earbud keeps dropping out.",
            "The Vireo app crashes immediately when I open equalizer settings.",
            "Firmware update is stuck at 42% for over an hour.",
            "Microphone volume is very muffled during calls."
        ],
        ambiguous_cases=[
            "Device unresponsive: classify as Technical & Firmware if resolvable via soft reset SOP; classify as Hardware & Warranty if device is completely bricked or will not take a charge."
        ]
    ),

    TaxonomyCategory.HARDWARE_WARRANTY: CategoryDefinition(
        name="Hardware & Warranty",
        description="Physical component failures, RMA claims, certified warranty repairs, and multi-touch hardware replacement.",
        responsible_team="Escalations & Warranty",
        inclusion_criteria=[
            "Permanent hardware failure (no power, bricked after firmware, blown driver)",
            "Single earbud completely silent despite factory reset",
            "Battery physical defects, swelling, or failure to charge past 0%",
            "Warranty claim status, RMA registration, or service center depot escalations",
            "Dead on Arrival (DOA) replacement unit dispatch under warranty"
        ],
        exclusion_criteria=[
            "Transient software or Bluetooth pairing glitches (use Technical & Firmware)",
            "Shipment transit damage reported at delivery (use Order & Logistics)",
            "Refund requests for returned goods (use Returns & Refunds)"
        ],
        representative_examples=[
            "Earbuds case does not power on at all, zero LED light with multiple cables.",
            "Warranty claim RMA82419 has been pending at the service center for 10 days.",
            "Right earbud is completely dead after water exposure despite IPX4 rating.",
            "Device bricked permanently during update. Need warranty replacement."
        ],
        ambiguous_cases=[
            "Earbud silent: classify as Technical & Firmware if reset steps have not been attempted; classify as Hardware & Warranty if reset was verified and hardware failure confirmed."
        ]
    ),

    TaxonomyCategory.ACCOUNT_ACCESS: CategoryDefinition(
        name="Account & Access",
        description="Customer account management, authentication, credential recovery, and profile settings.",
        responsible_team="Chat/Email/Voice Frontline",
        inclusion_criteria=[
            "One-Time Password (OTP) not received on registered mobile number or email",
            "Customer account lockout or blocked access",
            "Updating registered phone number, email address, or shipping profile",
            "Password reset failures or session expiration loops"
        ],
        exclusion_criteria=[
            "Companion app crashing on device (use Technical & Firmware)",
            "Payment gateway OTP failures during checkout (use Billing & Invoicing)"
        ],
        representative_examples=[
            "I am locked out of my Vireo account and OTP is not arriving.",
            "Changed my phone number, need to update my registered account mobile.",
            "Login code never arrives on SMS. Tried 5 times."
        ],
        ambiguous_cases=[
            "Customer mentions 'cannot login to buy': classify as Account & Access if the failure is credentials/OTP; classify as Pre-Sales & Info if inquiry is about purchase availability."
        ]
    ),

    TaxonomyCategory.PRE_SALES_INFO: CategoryDefinition(
        name="Pre-Sales & Info",
        description="Pre-purchase inquiries, device specifications, compatibility, warranty policies, and product guidance.",
        responsible_team="Chat/Email/Voice Frontline",
        inclusion_criteria=[
            "Product specifications, dimensions, battery runtime, and codec support",
            "Compatibility inquiries (iPhone, Android, Mac, Windows, Gaming consoles)",
            "Water resistance, gym suitability, and IP rating explanations",
            "Product release dates, stock availability, and accessory compatibility"
        ],
        exclusion_criteria=[
            "Active troubleshooting of an already delivered item (use Technical & Firmware)",
            "Price disputes or coupon failures at checkout (use Billing & Invoicing)"
        ],
        representative_examples=[
            "Will the Strata 3 headphones work with an iPhone 15 over USB-C?",
            "Can I swim or take a shower with the Pulse 2 earbuds?",
            "Can I connect two Orbit smart speakers together for stereo sound?",
            "What is the difference in battery life between Pulse and Pulse 2?"
        ],
        ambiguous_cases=[
            "Customer asks 'can I exchange my old earbuds for new one': classify as Pre-Sales & Info if asking about trade-in policy; classify as Returns & Refunds if requesting return of purchased order."
        ]
    )
}


class ClassificationOutput(BaseModel):
    """Standardized schema for ticket classification output."""
    ticket_id: str = Field(description="Unique ticket identifier")
    original_category: str = Field(description="Intake bot category from source helpdesk")
    predicted_category: str = Field(description="Predicted Seven-Pillar issue category")
    predicted_team: str = Field(description="Predicted responsible department")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Calibrated heuristic confidence score")
    classification_method: str = Field(description="Method used for classification (e.g., rule_based_deterministic)")
    evidence: str = Field(description="Traceable text signals or metadata triggering the classification")
    review_required: bool = Field(description="Flag indicating ambiguity, conflict, or low confidence requiring human review")


def get_responsible_team(category: str, channel: Optional[str] = None) -> str:
    """Map a predicted taxonomy category to its primary responsible department.

    Maintains separation between issue intent and team routing.

    Args:
        category: Predicted Seven-Pillar category name.
        channel: Intake channel ('chat', 'email', 'voice', 'social') for frontline routing.

    Returns:
        Designated department name.
    """
    clean_cat = category.strip()
    if clean_cat == TaxonomyCategory.ORDER_LOGISTICS.value:
        return "Logistics"
    elif clean_cat == TaxonomyCategory.RETURNS_REFUNDS.value:
        return "Returns Desk"
    elif clean_cat == TaxonomyCategory.BILLING_INVOICING.value:
        return "Billing"
    elif clean_cat == TaxonomyCategory.HARDWARE_WARRANTY.value:
        return "Escalations & Warranty"
    elif clean_cat in [
        TaxonomyCategory.TECHNICAL_FIRMWARE.value,
        TaxonomyCategory.ACCOUNT_ACCESS.value,
        TaxonomyCategory.PRE_SALES_INFO.value
    ]:
        # Route to frontline team based on channel per Operating Policy §2 & §6
        ch = str(channel).lower() if channel else "chat"
        if ch in ["chat", "social"]:
            return "Chat Frontline"
        elif ch == "email":
            return "Email Frontline"
        elif ch == "voice":
            return "Voice Frontline"
        return "Chat Frontline"

    return "Chat Frontline"

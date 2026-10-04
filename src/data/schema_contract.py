"""Canonical schema contracts and field definitions for dynamic support dataset ingestion.

Defines standard ticket, roster, and catalog schemas, required vs optional statuses,
supported data types, and downstream analytical dependencies.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class FieldRequirement(str, Enum):
    """Requirement level for a dataset column."""
    REQUIRED = "REQUIRED"          # Mandatory for minimal pipeline execution
    RECOMMENDED = "RECOMMENDED"    # Strongly recommended for core SLAs / KPIs
    OPTIONAL = "OPTIONAL"          # Optional metadata; degrades gracefully if absent


class FieldDataType(str, Enum):
    """Permitted logical data type for canonical fields."""
    STRING = "string"
    DATETIME = "datetime"
    NUMERIC = "numeric"
    INTEGER = "integer"
    BOOLEAN = "boolean"


class CanonicalFieldDefinition(BaseModel):
    """Metadata contract for an individual canonical field."""
    name: str = Field(description="Canonical field name")
    requirement: FieldRequirement = Field(description="Requirement level")
    data_type: FieldDataType = Field(description="Expected data type")
    description: str = Field(description="Business and operational definition")
    analytics_dependencies: List[str] = Field(
        default_factory=list,
        description="Analytics modules requiring this field (e.g., 'executive', 'sla', 'workload', 'financial')"
    )
    allowed_values: Optional[List[str]] = Field(
        default=None,
        description="Permitted categorical domain values if strictly constrained"
    )
    synonyms: List[str] = Field(
        default_factory=list,
        description="Common alternative column headers across helpdesk systems"
    )


class DatasetType(str, Enum):
    """Supported dataset categories for support intelligence ingestion."""
    TICKETS = "tickets"
    AGENTS = "agents"
    ORDERS = "orders"
    PRODUCTS = "products"
    CUSTOMERS = "customers"


# -----------------------------------------------------------------------------
# CANONICAL TICKET SCHEMA REGISTRY (20 Core Fields)
# -----------------------------------------------------------------------------

CANONICAL_TICKET_FIELDS: Dict[str, CanonicalFieldDefinition] = {
    "ticket_id": CanonicalFieldDefinition(
        name="ticket_id",
        requirement=FieldRequirement.REQUIRED,
        data_type=FieldDataType.STRING,
        description="Unique identifier for the support ticket / case / incident",
        analytics_dependencies=["executive", "monthly", "workload", "staffing", "audit", "triage"],
        synonyms=["ticketid", "ticket", "caseid", "case", "incidentid", "id", "ticketnumber", "ticket_no", "issue_id"]
    ),
    "created_at": CanonicalFieldDefinition(
        name="created_at",
        requirement=FieldRequirement.REQUIRED,
        data_type=FieldDataType.DATETIME,
        description="Intake timestamp when the customer inquiry was registered",
        analytics_dependencies=["executive", "monthly", "workload", "sla", "staffing", "audit"],
        synonyms=["createdat", "createdtime", "datecreated", "creationdate", "openedat", "created_date", "timestamp"]
    ),
    "first_response_at": CanonicalFieldDefinition(
        name="first_response_at",
        requirement=FieldRequirement.RECOMMENDED,
        data_type=FieldDataType.DATETIME,
        description="Timestamp of the first human agent reply for SLA calculation",
        analytics_dependencies=["sla", "monthly", "staffing", "audit"],
        synonyms=["firstresponseat", "firstresponsetime", "initialresponse", "firstreplytime", "frtime", "first_response_time"]
    ),
    "resolved_at": CanonicalFieldDefinition(
        name="resolved_at",
        requirement=FieldRequirement.OPTIONAL,
        data_type=FieldDataType.DATETIME,
        description="Timestamp of ticket resolution; null for open or pending backlogs",
        analytics_dependencies=["monthly", "workload", "staffing", "audit"],
        synonyms=["resolvedat", "resolutiontime", "dateresolved", "closedat", "resolvedtime", "closingtime", "resolved_date"]
    ),
    "status": CanonicalFieldDefinition(
        name="status",
        requirement=FieldRequirement.REQUIRED,
        data_type=FieldDataType.STRING,
        description="Current ticket lifecycle status (resolved, closed, open, pending)",
        analytics_dependencies=["executive", "monthly", "workload", "staffing", "audit"],
        allowed_values=["resolved", "closed", "open", "pending"],
        synonyms=["status", "ticketstatus", "state", "ticketstate", "currentstatus", "ticket_status"]
    ),
    "channel": CanonicalFieldDefinition(
        name="channel",
        requirement=FieldRequirement.REQUIRED,
        data_type=FieldDataType.STRING,
        description="Inbound communication medium (chat, email, voice, social)",
        analytics_dependencies=["sla", "financial", "executive", "monthly", "triage"],
        allowed_values=["chat", "email", "voice", "social"],
        synonyms=["channel", "source", "medium", "inboundchannel", "origin", "contactchannel", "ticket_channel"]
    ),
    "customer_id": CanonicalFieldDefinition(
        name="customer_id",
        requirement=FieldRequirement.REQUIRED,
        data_type=FieldDataType.STRING,
        description="Unique customer identifier for repeat-contact and profile analysis",
        analytics_dependencies=["monthly", "financial", "triage"],
        synonyms=["customerid", "custid", "clientid", "userid", "cxid", "customer_number"]
    ),
    "order_id": CanonicalFieldDefinition(
        name="order_id",
        requirement=FieldRequirement.OPTIONAL,
        data_type=FieldDataType.STRING,
        description="Associated ecommerce order reference for purchase validation",
        analytics_dependencies=["financial", "triage"],
        synonyms=["orderid", "ordernum", "ordernumber", "purchaseid", "transactionid", "order_no"]
    ),
    "product_sku": CanonicalFieldDefinition(
        name="product_sku",
        requirement=FieldRequirement.OPTIONAL,
        data_type=FieldDataType.STRING,
        description="Product SKU associated with the ticket inquiry",
        analytics_dependencies=["financial", "triage"],
        synonyms=["productsku", "sku", "itemcode", "productcode", "partnumber", "model_number"]
    ),
    "category": CanonicalFieldDefinition(
        name="category",
        requirement=FieldRequirement.OPTIONAL,
        data_type=FieldDataType.STRING,
        description="Helpdesk intake bot category tag or initial ticket classification",
        analytics_dependencies=["category_analytics", "triage"],
        synonyms=["category", "ticketcategory", "issuecategory", "bottag", "legacycategory", "type"]
    ),
    "priority": CanonicalFieldDefinition(
        name="priority",
        requirement=FieldRequirement.OPTIONAL,
        data_type=FieldDataType.STRING,
        description="Ticket urgency level (low, normal, high, urgent)",
        analytics_dependencies=["operational_triage"],
        allowed_values=["low", "normal", "high", "urgent"],
        synonyms=["priority", "severity", "urgency", "ticketpriority"]
    ),
    "assigned_team": CanonicalFieldDefinition(
        name="assigned_team",
        requirement=FieldRequirement.REQUIRED,
        data_type=FieldDataType.STRING,
        description="Department or queue the intake bot initially routed the ticket to",
        analytics_dependencies=["workload", "staffing", "financial", "audit"],
        synonyms=["assignedteam", "assignedgroup", "department", "team", "queue", "assignedqueue", "intaketeam", "group"]
    ),
    "agent_id": CanonicalFieldDefinition(
        name="agent_id",
        requirement=FieldRequirement.OPTIONAL,
        data_type=FieldDataType.STRING,
        description="Roster identifier of the agent who resolved or owns the ticket",
        analytics_dependencies=["workload", "staffing", "audit"],
        synonyms=["agentid", "assigneeid", "resolverid", "staffid", "rep_id", "representativeid", "owner_id"]
    ),
    "transfers": CanonicalFieldDefinition(
        name="transfers",
        requirement=FieldRequirement.OPTIONAL,
        data_type=FieldDataType.NUMERIC,
        description="Number of inter-team hand-offs; blank for unobservable pre-migration tickets",
        analytics_dependencies=["financial", "monthly"],
        synonyms=["transfers", "handoffs", "reassignments", "transfercount", "teamtransfers", "escalations"]
    ),
    "csat_score": CanonicalFieldDefinition(
        name="csat_score",
        requirement=FieldRequirement.OPTIONAL,
        data_type=FieldDataType.NUMERIC,
        description="Customer satisfaction survey score (1.0 to 5.0); blank indicates no response",
        analytics_dependencies=["monthly", "staffing"],
        synonyms=["csatscore", "csat", "customersatisfaction", "satisfactionscore", "rating", "survey_score"]
    ),
    "refund_amount_inr": CanonicalFieldDefinition(
        name="refund_amount_inr",
        requirement=FieldRequirement.OPTIONAL,
        data_type=FieldDataType.NUMERIC,
        description="Financial refund disbursed on the ticket in INR",
        analytics_dependencies=["financial", "triage"],
        synonyms=["refundamountinr", "refundamount", "refundvalue", "refundinr", "refund", "amount_refunded"]
    ),
    "refund_reason_code": CanonicalFieldDefinition(
        name="refund_reason_code",
        requirement=FieldRequirement.OPTIONAL,
        data_type=FieldDataType.STRING,
        description="Operating Policy §5 dropdown reason code selected during refund processing",
        analytics_dependencies=["financial", "triage"],
        synonyms=["refundreasoncode", "refundreason", "reasoncode", "refundcode", "disbursement_reason"]
    ),
    "replacement_issued": CanonicalFieldDefinition(
        name="replacement_issued",
        requirement=FieldRequirement.OPTIONAL,
        data_type=FieldDataType.STRING,
        description="Policy §5 replacement flag ('Y' or 'N')",
        analytics_dependencies=["financial", "triage"],
        allowed_values=["y", "n", "yes", "no"],
        synonyms=["replacementissued", "replacementflag", "replacement", "replaced", "rmaissued", "replacement_done"]
    ),
    "customer_message": CanonicalFieldDefinition(
        name="customer_message",
        requirement=FieldRequirement.RECOMMENDED,
        data_type=FieldDataType.STRING,
        description="Customer opening inquiry text or IVR transcript used for NLP/intent classification",
        analytics_dependencies=["classification", "category_analytics", "triage"],
        synonyms=["customermessage", "message", "description", "subject", "body", "inquiry", "issue", "cxmessage", "details"]
    ),
    "agent_notes": CanonicalFieldDefinition(
        name="agent_notes",
        requirement=FieldRequirement.OPTIONAL,
        data_type=FieldDataType.STRING,
        description="Closing summary notes or resolution commentary entered by support agent",
        analytics_dependencies=["classification", "category_analytics", "triage"],
        synonyms=["agentnotes", "notes", "agentnote", "resolutionnotes", "closingsummary", "agentcomment", "internal_notes"]
    ),
    "source_system": CanonicalFieldDefinition(
        name="source_system",
        requirement=FieldRequirement.OPTIONAL,
        data_type=FieldDataType.STRING,
        description="Helpdesk source system identifier ('helpdesk', 'legacy_fd', etc.)",
        analytics_dependencies=["audit", "preprocessing"],
        synonyms=["sourcesystem", "sourcehelpdesk", "system", "platform", "crm_source"]
    ),
}


def get_canonical_fields(dataset_type: DatasetType = DatasetType.TICKETS) -> Dict[str, CanonicalFieldDefinition]:
    """Retrieve canonical field definitions for a dataset type.

    Args:
        dataset_type: Type of dataset (defaults to DatasetType.TICKETS).

    Returns:
        Dictionary mapping canonical field names to CanonicalFieldDefinition instances.
    """
    if dataset_type == DatasetType.TICKETS:
        return CANONICAL_TICKET_FIELDS
    raise NotImplementedError(f"Dataset type '{dataset_type.value}' is reserved for future extensions.")


def get_required_fields(dataset_type: DatasetType = DatasetType.TICKETS) -> List[str]:
    """Retrieve list of mandatory field names for a dataset type.

    Args:
        dataset_type: Type of dataset (defaults to DatasetType.TICKETS).

    Returns:
        List of required field names.
    """
    fields = get_canonical_fields(dataset_type)
    return [name for name, field in fields.items() if field.requirement == FieldRequirement.REQUIRED]

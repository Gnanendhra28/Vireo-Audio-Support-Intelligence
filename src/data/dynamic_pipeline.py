"""Dynamic analytics pipeline and report capability evaluation engine.

Evaluates arbitrary in-memory support ticket DataFrames against analytical report
contracts, executes safe transformations without filesystem writes, and guarantees
strict non-mutation of input DataFrames.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, ConfigDict

from src.data.schema_contract import (
    CANONICAL_TICKET_FIELDS,
    CanonicalFieldDefinition,
    FieldRequirement,
    get_canonical_fields,
    get_required_fields,
    DatasetType,
)
from src.data.dynamic_validator import (
    DynamicValidator,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
)
from src.classification.classifier import TicketClassifier


class CapabilityStatus(str, Enum):
    """Availability status of an analytical report capability."""
    AVAILABLE = "AVAILABLE"        # All required fields and datasets present
    PARTIAL = "PARTIAL"            # Partially available with documented limitations
    UNAVAILABLE = "UNAVAILABLE"    # Mandatory fields or datasets absent; report blocked


class ReportCapability(BaseModel):
    """Contract evaluating whether a specific analytical report can safely run."""
    capability_id: str = Field(description="Unique capability key")
    name: str = Field(description="Human-readable report capability title")
    status: CapabilityStatus = Field(description="Availability status")
    required_fields: List[str] = Field(description="Canonical fields required for full calculation")
    missing_fields: List[str] = Field(default_factory=list, description="Required fields absent from dataset")
    supporting_datasets_required: List[str] = Field(
        default_factory=list,
        description="External auxiliary datasets needed (e.g., 'agents', 'products')"
    )
    supporting_datasets_missing: List[str] = Field(
        default_factory=list,
        description="Auxiliary datasets not supplied"
    )
    warnings: List[str] = Field(default_factory=list, description="Capability-specific operational cautions")
    explanation: str = Field(description="Clear justification of capability status")


class DynamicPipelineResult(BaseModel):
    """Structured output emitted by the dynamic analytics pipeline."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dataset_summary: Dict[str, Any] = Field(description="High-level volume and date scope summary")
    validation_result: ValidationResult = Field(description="Schema validation report")
    capabilities: Dict[str, ReportCapability] = Field(description="Capability evaluations across all reports")
    available_capabilities: List[str] = Field(default_factory=list, description="Report IDs ready for execution")
    unavailable_capabilities: List[str] = Field(default_factory=list, description="Report IDs that cannot run")
    preprocessed_df: pd.DataFrame = Field(description="Safely enriched and derived in-memory DataFrame")
    data_quality_warnings: List[str] = Field(default_factory=list, description="General data quality notices")
    explicit_assumptions: List[str] = Field(default_factory=list, description="Documented operational assumptions")


class DynamicPipeline:
    """Production-grade dynamic support analytics pipeline."""

    # Default first-response SLA targets in hours (Support Policy §3)
    DEFAULT_SLA_TARGETS: Dict[str, float] = {
        "chat": 0.25,    # 15 minutes
        "voice": 2.0,    # 2 hours
        "social": 4.0,   # 4 hours
        "email": 8.0,    # 8 hours
    }

    # Policy §3 store credit fee for breach
    DEFAULT_SLA_PENALTY_INR: float = 350.0

    @classmethod
    def evaluate_capabilities(
        cls,
        df: pd.DataFrame,
        has_agents: bool = False,
        has_products: bool = False,
        has_orders: bool = False
    ) -> Dict[str, ReportCapability]:
        """Evaluate report capabilities independently based on available fields and datasets.

        Args:
            df: Validated ticket DataFrame with canonical column names.
            has_agents: Whether a valid agents roster DataFrame is supplied.
            has_products: Whether a valid product catalog DataFrame is supplied.
            has_orders: Whether a valid orders DataFrame is supplied.

        Returns:
            Dictionary mapping capability IDs to ReportCapability evaluation contracts.
        """
        cols = set(df.columns)
        capabilities: Dict[str, ReportCapability] = {}

        # -------------------------------------------------------------
        # 1. Executive Ticket Volume
        # -------------------------------------------------------------
        exec_req = ["ticket_id", "created_at", "status"]
        exec_missing = [f for f in exec_req if f not in cols]
        if not exec_missing:
            capabilities["executive_volume"] = ReportCapability(
                capability_id="executive_volume",
                name="Executive Ticket Volume",
                status=CapabilityStatus.AVAILABLE,
                required_fields=exec_req,
                missing_fields=[],
                explanation="All core volume identifiers, timestamps, and status fields are present."
            )
        else:
            capabilities["executive_volume"] = ReportCapability(
                capability_id="executive_volume",
                name="Executive Ticket Volume",
                status=CapabilityStatus.UNAVAILABLE,
                required_fields=exec_req,
                missing_fields=exec_missing,
                explanation=f"Missing core volume fields: {', '.join(exec_missing)}."
            )

        # -------------------------------------------------------------
        # 2. Category Analytics
        # -------------------------------------------------------------
        cat_req = ["created_at"]
        has_created = "created_at" in cols
        has_cat = "category" in cols or "predicted_category" in cols
        has_msg = "customer_message" in cols

        if has_created and (has_cat or has_msg):
            explanation = (
                "Direct category field available for breakdown."
                if has_cat else
                "Customer message text available; deterministic Seven-Pillar classifier can generate categories."
            )
            capabilities["category_analytics"] = ReportCapability(
                capability_id="category_analytics",
                name="Category Analytics",
                status=CapabilityStatus.AVAILABLE,
                required_fields=["created_at", "category_or_customer_message"],
                missing_fields=[],
                explanation=explanation
            )
        else:
            missing = []
            if not has_created:
                missing.append("created_at")
            if not (has_cat or has_msg):
                missing.append("category or customer_message")
            capabilities["category_analytics"] = ReportCapability(
                capability_id="category_analytics",
                name="Category Analytics",
                status=CapabilityStatus.UNAVAILABLE,
                required_fields=["created_at", "category_or_customer_message"],
                missing_fields=missing,
                explanation="Requires created_at and either pre-existing category tags or customer message text."
            )

        # -------------------------------------------------------------
        # 3. SLA Analysis
        # -------------------------------------------------------------
        sla_req = ["created_at", "first_response_at", "channel"]
        sla_missing = [f for f in sla_req if f not in cols]
        if not sla_missing:
            capabilities["sla_analysis"] = ReportCapability(
                capability_id="sla_analysis",
                name="SLA Compliance & Response Time Analysis",
                status=CapabilityStatus.AVAILABLE,
                required_fields=sla_req,
                missing_fields=[],
                explanation="Timestamps and channels available; can calculate first-response duration and breach rates."
            )
        else:
            capabilities["sla_analysis"] = ReportCapability(
                capability_id="sla_analysis",
                name="SLA Compliance & Response Time Analysis",
                status=CapabilityStatus.UNAVAILABLE,
                required_fields=sla_req,
                missing_fields=sla_missing,
                explanation=f"Cannot evaluate first-response SLA breaches without: {', '.join(sla_missing)}."
            )

        # -------------------------------------------------------------
        # 4. Team Workload
        # -------------------------------------------------------------
        workload_req = ["ticket_id", "created_at", "assigned_team", "agent_id"]
        workload_missing = [f for f in workload_req if f not in cols]

        if not workload_missing and has_agents:
            capabilities["team_workload"] = ReportCapability(
                capability_id="team_workload",
                name="Team Workload & Queue Balancing",
                status=CapabilityStatus.AVAILABLE,
                required_fields=workload_req,
                missing_fields=[],
                supporting_datasets_required=["agents"],
                supporting_datasets_missing=[],
                explanation="Ticket queue assignments and verified agent roster available for assigned vs resolved metrics."
            )
        elif "assigned_team" in cols and not has_agents:
            capabilities["team_workload"] = ReportCapability(
                capability_id="team_workload",
                name="Team Workload & Queue Balancing",
                status=CapabilityStatus.PARTIAL,
                required_fields=workload_req,
                missing_fields=["agent_id"] if "agent_id" not in cols else [],
                supporting_datasets_required=["agents"],
                supporting_datasets_missing=["agents"],
                warnings=["Resolving team metrics unavailable without agent roster; limited to assigned intake queues."],
                explanation="Assigned bot queues can be analyzed, but actual resolved volume requires agent roster."
            )
        else:
            capabilities["team_workload"] = ReportCapability(
                capability_id="team_workload",
                name="Team Workload & Queue Balancing",
                status=CapabilityStatus.UNAVAILABLE,
                required_fields=workload_req,
                missing_fields=workload_missing,
                supporting_datasets_required=["agents"],
                supporting_datasets_missing=["agents"] if not has_agents else [],
                explanation="Requires assigned_team and agents roster to measure departmental workload."
            )

        # -------------------------------------------------------------
        # 5. Staffing Decision Analysis
        # -------------------------------------------------------------
        staffing_req = ["ticket_id", "created_at", "assigned_team", "agent_id"]
        staffing_missing = [f for f in staffing_req if f not in cols]

        if not staffing_missing and has_agents:
            capabilities["staffing_analysis"] = ReportCapability(
                capability_id="staffing_analysis",
                name="Staffing Decision & Capacity Modeling",
                status=CapabilityStatus.AVAILABLE,
                required_fields=staffing_req,
                missing_fields=[],
                supporting_datasets_required=["agents"],
                supporting_datasets_missing=[],
                warnings=["Tier 2 Escalations & Warranty agents must not be compared directly with Tier 1 frontline."],
                explanation="Agent roster provides verified headcounts and tier demarcation required for capacity modeling."
            )
        else:
            missing_datasets = ["agents"] if not has_agents else []
            capabilities["staffing_analysis"] = ReportCapability(
                capability_id="staffing_analysis",
                name="Staffing Decision & Capacity Modeling",
                status=CapabilityStatus.UNAVAILABLE,
                required_fields=staffing_req,
                missing_fields=staffing_missing,
                supporting_datasets_required=["agents"],
                supporting_datasets_missing=missing_datasets,
                explanation="Verified staffing decisions strictly require the agents roster to prevent unverified headcount assumptions."
            )

        # -------------------------------------------------------------
        # 6. Financial Operations & Impact
        # -------------------------------------------------------------
        fin_req = ["channel"]
        has_channel = "channel" in cols

        if has_channel and has_products:
            capabilities["financial_impact"] = ReportCapability(
                capability_id="financial_impact",
                name="Financial Impact & Operational Cost Modeling",
                status=CapabilityStatus.AVAILABLE,
                required_fields=["channel", "is_sla_breach", "transfers", "refund_amount_inr"],
                missing_fields=[],
                supporting_datasets_required=["products"],
                supporting_datasets_missing=[],
                explanation="Inbound channel costs, SLA penalty liabilities, and replacement catalog unit costs available."
            )
        elif has_channel and not has_products:
            capabilities["financial_impact"] = ReportCapability(
                capability_id="financial_impact",
                name="Financial Impact & Operational Cost Modeling",
                status=CapabilityStatus.PARTIAL,
                required_fields=["channel", "is_sla_breach", "transfers"],
                missing_fields=[],
                supporting_datasets_required=["products"],
                supporting_datasets_missing=["products"],
                warnings=["Replacement hardware COGS unavailable without product catalog; dual-disbursement leakage limited."],
                explanation="Channel handling costs and SLA penalties are available, but replacement COGS requires products catalog."
            )
        else:
            capabilities["financial_impact"] = ReportCapability(
                capability_id="financial_impact",
                name="Financial Impact & Operational Cost Modeling",
                status=CapabilityStatus.UNAVAILABLE,
                required_fields=["channel"],
                missing_fields=["channel"],
                supporting_datasets_required=["products"],
                supporting_datasets_missing=["products"] if not has_products else [],
                explanation="Inbound contact channel is required to calculate historical support handling expenditure."
            )

        # -------------------------------------------------------------
        # 7. Master Audit Reconciliation
        # -------------------------------------------------------------
        capabilities["audit_reconciliation"] = ReportCapability(
            capability_id="audit_reconciliation",
            name="Master Audit Reconciliation",
            status=CapabilityStatus.UNAVAILABLE,
            required_fields=["certified_18m_baseline_scope"],
            missing_fields=["certified_18m_baseline_scope"],
            explanation="Master Audit Reconciliation applies strictly to the audited 18-month baseline (Jan 2025 – Jun 2026)."
        )

        return capabilities

    @classmethod
    def process(
        cls,
        tickets_df: pd.DataFrame,
        agents_df: Optional[pd.DataFrame] = None,
        products_df: Optional[pd.DataFrame] = None,
        orders_df: Optional[pd.DataFrame] = None,
        sla_targets: Optional[Dict[str, float]] = None,
        sla_penalty_inr: Optional[float] = None
    ) -> DynamicPipelineResult:
        """Execute the dynamic support analytics pipeline.

        Guarantees:
        - Non-mutation of input DataFrames (deep copy).
        - Zero writes to disk or external databases.
        - Semantic preservation of missing transfers and CSAT.
        - Strict avoidance of negative durations or fabricated metrics.

        Args:
            tickets_df: Candidate support tickets DataFrame.
            agents_df: Optional agents roster DataFrame.
            products_df: Optional product catalog DataFrame.
            orders_df: Optional orders DataFrame.
            sla_targets: Optional channel SLA target overrides in hours.
            sla_penalty_inr: Optional store credit breach penalty in INR.

        Returns:
            DynamicPipelineResult containing validation, capabilities, and preprocessed data.
        """
        # Enforce input DataFrame immutability via deep copy
        df = tickets_df.copy()

        # Step 1: In-memory schema validation
        val_result = DynamicValidator.validate_ticket_dataframe(df)

        has_agents = agents_df is not None and len(agents_df) > 0 and "agent_id" in agents_df.columns
        has_products = products_df is not None and len(products_df) > 0 and "sku" in products_df.columns
        has_orders = orders_df is not None and len(orders_df) > 0 and "order_id" in orders_df.columns

        # Step 2: Capability Evaluation
        capabilities = cls.evaluate_capabilities(
            df=df,
            has_agents=has_agents,
            has_products=has_products,
            has_orders=has_orders
        )

        available_caps = [k for k, v in capabilities.items() if v.status == CapabilityStatus.AVAILABLE]
        unavailable_caps = [k for k, v in capabilities.items() if v.status == CapabilityStatus.UNAVAILABLE]

        warnings: List[str] = [w.issue for w in val_result.warnings]
        assumptions: List[str] = [
            "Missing transfers are preserved as null and not imputed as zero.",
            "Missing CSAT scores represent non-responses and are excluded from customer satisfaction averages.",
            "Unresolved tickets (open/pending) do not receive resolution durations.",
            "Timestamps parsed in native ISO/mixed formats without unverified timezone shifts."
        ]

        # Step 3: Dynamic Preprocessing (Only if basic volume is viable)
        if "created_at" in df.columns:
            df["created_dt"] = pd.to_datetime(df["created_at"], format="mixed", errors="coerce")
            df["year_month"] = df["created_dt"].dt.to_period("M").astype(str)

        if "first_response_at" in df.columns:
            df["first_response_dt"] = pd.to_datetime(df["first_response_at"], format="mixed", errors="coerce")

        if "resolved_at" in df.columns:
            df["resolved_dt"] = pd.to_datetime(df["resolved_at"], format="mixed", errors="coerce")

        # Step 4: Derive Durations Safely
        if "created_dt" in df.columns and "first_response_dt" in df.columns:
            # Response duration only when both timestamps are valid and first_response >= created
            valid_resp_mask = df["created_dt"].notna() & df["first_response_dt"].notna()
            resp_diff = (df["first_response_dt"] - df["created_dt"]).dt.total_seconds() / 3600.0
            # Set negative response times to NaN (do not fabricate negative durations)
            df["resp_time_hrs"] = np.where(valid_resp_mask & (resp_diff >= 0.0), resp_diff, np.nan)
        else:
            df["resp_time_hrs"] = np.nan

        if "created_dt" in df.columns and "resolved_dt" in df.columns:
            # Resolution duration only for resolved/closed status with valid timestamps
            is_resolved_status = df["status"].astype(str).str.lower().isin(["resolved", "closed"]) if "status" in df.columns else True
            valid_res_mask = df["created_dt"].notna() & df["resolved_dt"].notna() & is_resolved_status
            res_diff = (df["resolved_dt"] - df["created_dt"]).dt.total_seconds() / 3600.0
            df["total_res_time_hrs"] = np.where(valid_res_mask & (res_diff >= 0.0), res_diff, np.nan)
        else:
            df["total_res_time_hrs"] = np.nan

        if "first_response_dt" in df.columns and "resolved_dt" in df.columns:
            is_resolved_status = df["status"].astype(str).str.lower().isin(["resolved", "closed"]) if "status" in df.columns else True
            valid_hdl_mask = df["first_response_dt"].notna() & df["resolved_dt"].notna() & is_resolved_status
            hdl_diff = (df["resolved_dt"] - df["first_response_dt"]).dt.total_seconds() / 3600.0
            df["handle_time_hrs"] = np.where(valid_hdl_mask & (hdl_diff >= 0.0), hdl_diff, np.nan)
        else:
            df["handle_time_hrs"] = np.nan

        # Step 5: SLA Breaches
        targets = sla_targets or cls.DEFAULT_SLA_TARGETS
        penalty = sla_penalty_inr or cls.DEFAULT_SLA_PENALTY_INR

        if "channel" in df.columns and "resp_time_hrs" in df.columns:
            df["sla_target_hrs"] = df["channel"].astype(str).str.lower().map(targets)
            valid_sla_mask = df["resp_time_hrs"].notna() & df["sla_target_hrs"].notna()
            df["is_sla_breach"] = np.where(valid_sla_mask, df["resp_time_hrs"] > df["sla_target_hrs"], False)
            df["sla_penalty_inr"] = np.where(df["is_sla_breach"], penalty, 0.0)
        else:
            df["sla_target_hrs"] = np.nan
            df["is_sla_breach"] = False
            df["sla_penalty_inr"] = 0.0

        # Step 6: Category Classification Enrichment
        if "predicted_category" not in df.columns:
            if "customer_message" in df.columns and df["customer_message"].dropna().astype(str).str.strip().ne("").any():
                classifier = TicketClassifier()
                df = classifier.classify_dataframe(df)
                assumptions.append("Predicted categories derived via deterministic Seven-Pillar rule classifier.")
            elif "category" in df.columns:
                df["predicted_category"] = df["category"]
                df["confidence_score"] = np.nan
                df["review_required"] = False
                assumptions.append("Used pre-existing category tags directly without ML/rule classification.")
            else:
                df["predicted_category"] = np.nan
                df["confidence_score"] = np.nan
                df["review_required"] = False

        # Step 7: Roster Enrichment (Strictly via agent_id, never name)
        if has_agents and "agent_id" in df.columns:
            roster_subset = agents_df[["agent_id", "team", "tier", "site", "shift", "name"]].rename(
                columns={
                    "team": "resolving_team",
                    "tier": "resolving_tier",
                    "site": "resolving_site",
                    "shift": "resolving_shift",
                    "name": "resolving_agent_name"
                }
            )
            df = df.merge(roster_subset, on="agent_id", how="left")
            assumptions.append("Agent roster merged strictly on agent_id to avoid display-name collisions.")
        else:
            if "resolving_team" not in df.columns:
                df["resolving_team"] = np.nan
                df["resolving_tier"] = np.nan

        # Step 8: Repeat Contact Detection (30-day window proxy)
        if "customer_id" in df.columns and "created_dt" in df.columns and "resolved_dt" in df.columns:
            df["is_repeat_contact_30d"] = False
            # Compute within customers
            sorted_idx = df.sort_values(["customer_id", "created_dt"]).index
            sub = df.loc[sorted_idx].copy()
            sub["prev_res_dt"] = sub.groupby("customer_id")["resolved_dt"].shift(1)
            days_delta = (sub["created_dt"] - sub["prev_res_dt"]).dt.total_seconds() / (24 * 3600.0)
            is_rep = (days_delta >= 0.0) & (days_delta <= 30.0)
            df.loc[sub.index, "is_repeat_contact_30d"] = is_rep
        else:
            df["is_repeat_contact_30d"] = False

        # Dataset Summary
        date_start = str(df["created_dt"].min()) if "created_dt" in df.columns and df["created_dt"].notna().any() else "N/A"
        date_end = str(df["created_dt"].max()) if "created_dt" in df.columns and df["created_dt"].notna().any() else "N/A"
        channel_dist = df["channel"].value_counts().to_dict() if "channel" in df.columns else {}
        status_dist = df["status"].value_counts().to_dict() if "status" in df.columns else {}

        summary = {
            "total_tickets": len(df),
            "date_range_start": date_start,
            "date_range_end": date_end,
            "channel_distribution": channel_dist,
            "status_distribution": status_dist,
            "has_roster_linked": has_agents,
            "has_catalog_linked": has_products,
            "has_orders_linked": has_orders
        }

        return DynamicPipelineResult(
            dataset_summary=summary,
            validation_result=val_result,
            capabilities=capabilities,
            available_capabilities=available_caps,
            unavailable_capabilities=unavailable_caps,
            preprocessed_df=df,
            data_quality_warnings=warnings,
            explicit_assumptions=assumptions
        )

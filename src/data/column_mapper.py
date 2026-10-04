"""Deterministic column detection and canonical mapping module for support datasets.

Provides rule-based header normalization, synonym matching, ambiguity detection,
and collision safeguards without relying on external APIs or LLMs.
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any
from pydantic import BaseModel, Field
import pandas as pd

from src.data.schema_contract import (
    CANONICAL_TICKET_FIELDS,
    CanonicalFieldDefinition,
    FieldRequirement,
    get_canonical_fields,
    get_required_fields,
    DatasetType,
)


class MappingReport(BaseModel):
    """Structured audit report detailing column mapping results and issues."""
    mapped_columns: Dict[str, str] = Field(
        default_factory=dict,
        description="Canonical field name -> Matched source column name"
    )
    unmapped_source_columns: List[str] = Field(
        default_factory=list,
        description="Columns present in source data not mapped to any canonical field"
    )
    missing_required_fields: List[str] = Field(
        default_factory=list,
        description="Mandatory canonical fields not mapped in the source dataset"
    )
    missing_optional_fields: List[str] = Field(
        default_factory=list,
        description="Optional or recommended canonical fields absent from the source dataset"
    )
    ambiguous_columns: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Source columns that matched multiple canonical field candidates"
    )
    collision_errors: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Canonical fields claimed by multiple distinct source columns"
    )
    is_valid: bool = Field(
        description="Whether the mapping satisfies all required fields with zero unresolved collisions"
    )


class ColumnMapper:
    """Deterministic mapper matching source headers to canonical field contracts."""

    @staticmethod
    def normalize_header(header: str) -> str:
        """Normalize column header: lowercase, strip, and remove all non-alphanumeric characters.

        Examples:
            'Ticket #' -> 'ticket'
            'Created Time' -> 'createdtime'
            'Assigned_Group' -> 'assignedgroup'
        """
        if not header:
            return ""
        s = str(header).strip().lower()
        return re.sub(r"[^a-z0-9]", "", s)

    @classmethod
    def detect_mapping(
        cls,
        source_columns: List[str],
        manual_mapping: Optional[Dict[str, str]] = None,
        dataset_type: DatasetType = DatasetType.TICKETS
    ) -> MappingReport:
        """Deterministically map source column names to canonical schema fields.

        Enforces:
        - Exact and synonym-based matching.
        - Manual mapping precedence.
        - Detection of multi-candidate ambiguous source columns.
        - Strict prevention of multiple source columns silently mapping to one canonical field.

        Args:
            source_columns: List of raw header strings from uploaded CSV.
            manual_mapping: Explicit overrides. Can be provided as {canonical_field: source_column}
                           or {source_column: canonical_field}.
            dataset_type: Target schema contract (defaults to DatasetType.TICKETS).

        Returns:
            MappingReport containing mapped, unmapped, missing, and ambiguous fields.
        """
        canonical_fields = get_canonical_fields(dataset_type)
        required_fields = get_required_fields(dataset_type)

        # Build reverse lookup map: normalized_synonym -> set of canonical_field_names
        synonym_lookup: Dict[str, Set[str]] = {}
        for canon_name, field_def in canonical_fields.items():
            # Add canonical name itself
            norm_canon = cls.normalize_header(canon_name)
            synonym_lookup.setdefault(norm_canon, set()).add(canon_name)

            # Add all registered synonyms
            for syn in field_def.synonyms:
                norm_syn = cls.normalize_header(syn)
                if norm_syn:
                    synonym_lookup.setdefault(norm_syn, set()).add(canon_name)

        # Normalize manual overrides if provided
        # Standardize manual_overrides internally as: canonical_name -> source_col_name
        resolved_manual: Dict[str, str] = {}
        if manual_mapping:
            source_col_map = {cls.normalize_header(c): c for c in source_columns}
            for k, v in manual_mapping.items():
                # Check if k is canonical name and v is in source_columns
                if k in canonical_fields and v in source_columns:
                    resolved_manual[k] = v
                # Or if v is canonical name and k is in source_columns
                elif v in canonical_fields and k in source_columns:
                    resolved_manual[v] = k
                else:
                    # Try normalized matching
                    norm_k = cls.normalize_header(k)
                    norm_v = cls.normalize_header(v)
                    if norm_k in canonical_fields and norm_v in source_col_map:
                        resolved_manual[norm_k] = source_col_map[norm_v]
                    elif norm_v in canonical_fields and norm_k in source_col_map:
                        resolved_manual[norm_v] = source_col_map[norm_k]

        auto_candidates: Dict[str, List[str]] = {}  # source_col -> list of canonical_names
        ambiguous_cols: Dict[str, List[str]] = {}

        # 1. Evaluate auto-detection for non-manually mapped columns
        manually_claimed_sources = set(resolved_manual.values())
        manually_claimed_canonicals = set(resolved_manual.keys())

        for col in source_columns:
            if col in manually_claimed_sources:
                continue

            norm_col = cls.normalize_header(col)
            matches = synonym_lookup.get(norm_col, set())

            if len(matches) == 1:
                canon_target = next(iter(matches))
                auto_candidates.setdefault(col, []).append(canon_target)
            elif len(matches) > 1:
                ambiguous_cols[col] = sorted(list(matches))

        # 2. Check for canonical collision errors (multiple source columns mapped to same canonical field)
        reverse_canon_claims: Dict[str, List[str]] = {}

        # First add manual claims
        for canon, src in resolved_manual.items():
            reverse_canon_claims.setdefault(canon, []).append(src)

        # Next add auto claims
        for src, canon_list in auto_candidates.items():
            for canon in canon_list:
                reverse_canon_claims.setdefault(canon, []).append(src)

        collision_errors: Dict[str, List[str]] = {}
        final_mapped: Dict[str, str] = {}

        for canon, src_list in reverse_canon_claims.items():
            if len(src_list) > 1:
                # If manual override specified one of them, prioritize manual override
                if canon in resolved_manual:
                    final_mapped[canon] = resolved_manual[canon]
                else:
                    collision_errors[canon] = sorted(src_list)
            else:
                final_mapped[canon] = src_list[0]

        # 3. Compile unmapped, missing required, and missing optional fields
        mapped_sources = set(final_mapped.values())
        unmapped_sources = [c for c in source_columns if c not in mapped_sources and c not in ambiguous_cols]

        missing_required = [f for f in required_fields if f not in final_mapped]
        missing_optional = [
            f for f, d in canonical_fields.items()
            if f not in final_mapped and d.requirement != FieldRequirement.REQUIRED
        ]

        # Validation status: all required fields present, no collision errors, and no ambiguous matches
        is_valid = (
            len(missing_required) == 0 and
            len(collision_errors) == 0 and
            len(ambiguous_cols) == 0
        )

        return MappingReport(
            mapped_columns=final_mapped,
            unmapped_source_columns=unmapped_sources,
            missing_required_fields=missing_required,
            missing_optional_fields=missing_optional,
            ambiguous_columns=ambiguous_cols,
            collision_errors=collision_errors,
            is_valid=is_valid
        )

    @staticmethod
    def apply_mapping(
        df: pd.DataFrame,
        mapping: Dict[str, str]
    ) -> pd.DataFrame:
        """Apply canonical mapping to rename DataFrame columns without mutating the input.

        Args:
            df: Input DataFrame.
            mapping: Dictionary of {canonical_field_name: source_column_name}.

        Returns:
            New DataFrame with renamed canonical column names.
        """
        # Create a deep copy to guarantee immutability of the source DataFrame
        df_copy = df.copy()

        # Invert mapping to {source_col: canonical_name} for pandas rename
        rename_map = {src: canon for canon, src in mapping.items() if src in df_copy.columns}
        return df_copy.rename(columns=rename_map)

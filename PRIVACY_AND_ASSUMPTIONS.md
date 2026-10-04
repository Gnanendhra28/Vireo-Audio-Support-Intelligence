# PRIVACY & BUSINESS ASSUMPTIONS MANIFESTO
**Project:** Vireo Audio Support Intelligence  
**Author:** Senior Python Engineer & Lead Data Analyst  
**Version:** 1.0 (Step 1 Deliverable)  
**Date:** October 2026  

---

## 1. PRIVACY SAFEGUARDS & DATA HANDLING PRINCIPLES

Customer privacy and data security are foundational constraints for this project.

1. **Strict Masking of Personally Identifiable Information (PII):**
   - Customer full names, email addresses, phone numbers, complete shipping addresses, and personal notes present in `customers.csv`, `tickets.csv`, or `orders.csv` must never be logged, printed to standard output, included in analytics outputs, or displayed unprotected in UI tables.
   - Sample ticket inspection for classification verification must redact customer names and contact details, presenting only tokenized identifiers (e.g., `Ticket TK-240***`, `Customer C100***`).

2. **No Persistent External Transmission of Customer Text:**
   - Ticket text extracts sent to LLMs or embedding models must be stripped of PII entities (names, email addresses, order IDs, phone numbers) before inference.
   - No customer data will be stored on third-party cloud infrastructure or unapproved storage buckets.

3. **Role-Based Metric Visibility:**
   - Individual agent display names must not be used for individual shaming or public league tables. Performance evaluations must use system keys (`agent_id`) and account for tier, shift, and channel context.

---

## 2. GOVERNING BUSINESS CONSTRAINTS & CORE ASSUMPTIONS

The following explicit constraints and data realities govern all subsequent analytical modeling, AI classification, staffing assessments, and financial calculations:

### 2.1. Category Tags & Intake Bot Unreliability
- **Finding:** The `category` field in `tickets.csv` is set automatically by the intake chatbot based on initial user responses. Agents have the ability to re-tag tickets at closure, but in practice, they rarely do.
- **Data Reality:** Analysis reveals a rigid, deterministic 1:1 mapping between bot categories and assigned teams for four major departments:
  - 100% of tickets tagged `Billing & Payments` (2,564 tickets) were auto-assigned to the `Billing` team.
  - 100% of tickets tagged `Delivery & Shipping` (1,905 tickets) were auto-assigned to the `Logistics` team.
  - 100% of tickets tagged `Returns & Refunds` (1,049 tickets) were auto-assigned to `Returns Desk`.
  - 100% of tickets tagged `Warranty & Repair` (525 tickets) were auto-assigned to `Escalations & Warranty`.
- **Constraint:** Existing bot category tags cannot be treated as ground-truth labels. Many delivery complaints (e.g., "order not delivered", "delayed tracking") were tagged as "Billing & Payments" because customers mentioned payments, or "Other" by default.

### 2.2. Transfer Data Interpretation (Legacy vs. Current System)
- **Finding:** Helpdesk migration occurred on **14 September 2025**. Pre-migration tickets originate from Freshdesk (`legacy_fd`, 4,052 rows); post-migration tickets originate from the current system (`helpdesk`, 7,728 rows).
- **Constraint:** The `transfers` field was not captured in Freshdesk.
- **Rule:** Blank values in `transfers` for legacy records signify **unknown / unrecorded**, NOT zero. Imputing zero would severely distort transfer and routing metrics. Transfer rate benchmarks must be evaluated on current helpdesk records or explicitly flagged as unavailable for pre-migration data.

### 2.3. Agent Identity & Roster Structure
- **Finding:** Two active agents in `agents.csv` share the identical display name **"Om Sharma"**:
  - `A3006`: Indore site, Chat Frontline, Tier 1.
  - `A3029`: Bengaluru site, Voice Frontline, Tier 1.
- **Rule:** All joins, aggregations, and performance evaluations must strictly utilize `agent_id` as the primary key, never display name.
- **Roster Dynamics:** `to_date` is 100% null across all 44 agents in `agents.csv`, indicating an active roster snapshot.

### 2.4. Tier 2 vs. Tier 1 Workload Comparability
- **Finding:** Escalations & Warranty operates as Tier 2 (6 certified agents).
- **Operational Reality:** Per Operating Policy §6, Tier 2 cases handle RMA, hardware diagnostics, and warranty claims. These cases are multi-touch, requiring physical inspection and vendor coordination.
- **Metric Contrast:** Median handle time for Tier 2 is **122.0 hours (~5.1 days)**, compared to **0.35 hours (21 minutes)** for Tier 1 Frontline teams.
- **Constraint:** Tier 2 agents must never be evaluated against Tier 1 agents using raw ticket closure volume.

### 2.5. Returns Desk Role in Refunds
- **Finding:** Returns Desk processes 53% of all refund transactions and 52% of total refund value.
- **Operational Reality:** Per Operating Policy §6, Returns Desk is tasked by design with reverse pickups and refund processing.
- **Constraint:** High refund counts in Returns Desk are expected operational throughput, not evidence of queue distress or understaffing.

### 2.6. Timestamp Inversion & Timezone Discrepancy
- **Finding:** 2,575 tickets in `legacy_fd` displayed `resolved_at < first_response_at`, and 2,379 displayed `resolved_at < created_at`.
- **Root Cause Identified:** Per Operating Policy §9, resolution timestamps for migrated Freshdesk tickets were reconstructed from the legacy event log, which recorded in **UTC (+00:00)**, whereas helpdesk exports and creation/first-response timestamps are in **IST (+05:30)**.
- **Remediation Rule:** A +5 hour 30 minute offset must be added to `resolved_at` for all `legacy_fd` tickets. This mathematically eliminates 100% of negative handle time anomalies (from 2,575 down to 0). Helpdesk records require no offset.

### 2.7. Monetary Values & Refund Fields
- **Finding:** `refund_amount_inr` has 1,894 non-null entries (1,238 helpdesk, 656 legacy_fd). The values align with order amounts and product retail prices in INR across both systems.
- **Constraint:** Blanks in `refund_amount_inr` represent **no refund raised**, not missing data. They must not be conflated with ₹0 refunds.

### 2.8. Customer Satisfaction (CSAT) Treatment
- **Finding:** 6,435 tickets (54.63%) have blank `csat_score`. Non-null count is 5,345 (45.37%), matching Operating Policy §8 ("Around 45% of customers respond").
- **Constraint:** Blanks represent customer non-response. They must be excluded from denominator calculations when computing average CSAT, never imputed as zero. Imputing zero would artificially depress Vireo's CSAT from ~3.4 to ~1.5.

### 2.9. Auto-Closed Tickets as Completed Attendance
- **Finding:** 1,069 tickets have `status == 'closed'`.
- **Constraint:** Per Operating Policy §8 & §10, tickets auto-closed after 72 hours without customer reply count as **valid completed attendance** for agent capacity calculations and SLA tracking.

### 2.10. Dual Refund & Replacement Policy Violations
- **Finding:** Operating Policy §5 strictly mandates: *"In no case is a customer to receive both a refund and a replacement for the same order."*
- **Discovered Violations:**
  - 2 tickets have both `refund_amount_inr > 0` and `replacement_issued == 'Y'` within the same ticket (`TK-241926` and `TK-248344`).
  - Across the entire dataset, **74 distinct orders** received both a refund and a replacement across different tickets.
- **Financial Implication:** This represents unrecovered financial leakage requiring immediate quantification and audit.

### 2.11. Staffing Budget & Cost Baseline
- **Hiring Benchmark:** Two additional support hires cost approximately **₹9,00,000 annually** (~₹4,50,000 per agent fully loaded, or ₹165/agent-hour across standard annual shifts).
- **Cost Trade-off:** Staffing decisions must compare the ₹9L headcount addition against the cost of process improvements, automated bot re-routing, and reducing SLA breach credits (currently ₹350 per breach).

---

## 3. SUMMARY OF DATA VALIDATION RULES

| Field / Metric | Potential Trap | Mandated Rule |
| :--- | :--- | :--- |
| `agent_id` vs `name` | Duplicate name "Om Sharma" | Strictly group and join by `agent_id`. |
| `legacy_fd` `transfers` | Stored as NaN / empty | Treat as `UNKNOWN`, do not fill with 0. |
| `legacy_fd` `resolved_at` | Stored in UTC in event log | Apply `+ 05:30:00` offset before computing handle time. |
| `csat_score` | 54.6% unresponded | Exclude nulls from CSAT means; never replace with 0. |
| `status == 'closed'` | Auto-closed tickets | Include in attendance and agent productivity metrics. |
| `refund_amount_inr` | 83.9% null | Treat null as "no refund event"; preserve null vs ₹0 distinction. |
| Analysis Date Window | 2024 pilot data exists | Core business evaluation spans 18 months (Jan 2025 – Jun 2026). |

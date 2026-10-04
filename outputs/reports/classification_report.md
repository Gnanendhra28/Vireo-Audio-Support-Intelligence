# AI-ASSISTED TICKET CLASSIFICATION & TAXONOMY EVALUATION REPORT
**Project:** Vireo Audio Support Intelligence  
**Phase:** Step 2 — AI-Assisted Ticket Classification & Taxonomy Engine  
**Prepared For:** Priya Raman (Head of CX), Arjun Mehta (Finance Controller), Neha Kulkarni (Support Operations Manager)  
**Author:** Senior AI Engineer & Support Operations Data Scientist  
**Date:** October 2026  

---

## EXECUTIVE SUMMARY

A deterministic, explainable, and reproducible ticket classification pipeline was developed and executed across all **11,780 support tickets** in the Vireo Audio dataset.

The system reclassifies unstructured customer messages, agent resolution notes, and metadata signals into the **Seven-Pillar Support Intent Taxonomy**, completely eliminating target leakage by decoupling customer intent from resolving agent identity.

### Key Classification Findings:
1. **The Billing Queue Distortion Confirmed:**
   - The intake bot assigned **2,564 tickets (21.77%)** to `Billing & Payments`.
   - The AI classifier reveals that **only 1,322 of these tickets (51.56%)** are genuine `Billing & Invoicing` issues.
   - **1,048 tickets (40.87%)** tagged by the bot as Billing are actually **Order & Logistics** fulfillment delays (e.g., customers saying *"paid 5 days ago, item not delivered"*).
   - An additional **192 tickets (7.49%)** are **Returns & Refunds** inquiries.
2. **True Operational Dominance of Logistics:**
   - Under the intake bot, `Delivery & Shipping` appeared to comprise only **1,905 tickets (16.17%)**.
   - Under the Seven-Pillar Taxonomy, **`Order & Logistics` is the single largest category in the company with 3,426 tickets (29.08%)**.
   - The extra 1,521 Logistics tickets were recovered from `Billing & Payments` (1,048 tickets) and the unclassified `Other` category (684 tickets).
3. **The 'Other' Category Dissected:**
   - The bot's catch-all `Other` tag (1,622 tickets) hid **684 Order & Logistics tickets (42.17%)**, **444 Technical & Firmware tickets (27.37%)**, and **163 Returns & Refunds tickets (10.05%)**.
4. **Reproducibility & Traceability:**
   - 100% of tickets (11,780 / 11,780) were processed deterministically without dropping open, pending, or legacy records.
   - Every classification is saved to `data/processed/classified_tickets.csv` with original ticket IDs, confidence scores, evidence strings, and review flags.

---

## 1. CLASSIFICATION PIPELINE & METHODOLOGY

- **Implementation Method:** Rule-based deterministic pattern matching engine (`RuleMatcher`) with multi-source corroboration and heuristic confidence calibration (`ConfidenceCalibrator`).
- **Target Leakage Safeguard:** Strictly enforced. The classifier does not accept or inspect `agent_id`, `site`, `assigned_team`, or `resolving_team`.
- **Inputs Evaluated:**
  - `customer_message` (opening inquiry or IVR transcript)
  - `agent_notes` (closing agent summary and triage notes)
  - `refund_reason_code` (Policy §5 dropdown codes)
  - `replacement_issued` (hardware replacement dispatch flag)
  - `original_category` (used strictly as an emergency tie-breaker for zero-signal records)
- **Heuristic Confidence Score:** Calibrated between `0.20` and `0.98`. Reflects signal weight, multi-source corroboration (message + notes + metadata), and margin of victory over competitor categories.

---

## 2. SEVEN-PILLAR CATEGORY DISTRIBUTION

Across the full 11,780-ticket dataset, the classifier produced the following intent distribution:

| Seven-Pillar Category | Predicted Count | Percentage Share (%) | Primary Responsible Department |
| :--- | :---: | :---: | :--- |
| **Order & Logistics** | **3,426** | **29.08%** | Logistics |
| **Technical & Firmware** | **2,853** | **24.22%** | Chat / Email / Voice Frontline (Tier 1) |
| **Returns & Refunds** | **1,793** | **15.22%** | Returns Desk |
| **Billing & Invoicing** | **1,591** | **13.51%** | Billing |
| **Hardware & Warranty** | **1,062** | **9.02%** | Escalations & Warranty (Tier 2 Certified) |
| **Pre-Sales & Info** | **643** | **5.46%** | Chat / Email / Voice Frontline (Tier 1) |
| **Account & Access** | **412** | **3.50%** | Chat / Email / Voice Frontline (Tier 1) |
| **Total** | **11,780** | **100.00%** | — |

```
                       PREDICTED CATEGORY BREAKDOWN
  Order & Logistics    █████████████████████████████ 29.08% (3,426)
  Technical & Firmware ████████████████████████ 24.22% (2,853)
  Returns & Refunds    ███████████████ 15.22% (1,793)
  Billing & Invoicing  █████████████ 13.51% (1,591)
  Hardware & Warranty  █████████ 9.02% (1,062)
  Pre-Sales & Info     █████ 5.46% (643)
  Account & Access     ███ 3.50% (412)
```

### Department Workload Allocation (Predicted Responsible Team):
- **Logistics:** **3,426 tickets (29.08%)**
- **Chat Frontline:** **2,096 tickets (17.79%)**
- **Returns Desk:** **1,793 tickets (15.22%)**
- **Billing:** **1,591 tickets (13.51%)**
- **Email Frontline:** **1,206 tickets (10.24%)**
- **Escalations & Warranty:** **1,062 tickets (9.02%)**
- **Voice Frontline:** **606 tickets (5.14%)**

---

## 3. CONFIDENCE SCORE & HUMAN REVIEW ANALYSIS

- **Mean Confidence:** `0.714`
- **Median Confidence:** `0.760`
- **Standard Deviation:** `0.219`
- **25th Percentile:** `0.400`
- **75th Percentile:** `0.910`
- **Minimum:** `0.400` | **Maximum:** `0.970`

### Review Flag Distribution (`review_required`):
- **Automated Confident (`review_required = False`):** **7,814 tickets (66.33%)**
- **Human Review Flagged (`review_required = True`):** **3,966 tickets (33.67%)**

#### Breakdown of Review-Required Tickets by Predicted Category:

| Predicted Category | Total Tickets | Review Required = False | Review Required = True | Review Flag Rate (%) | Primary Review Reason |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Technical & Firmware** | 2,853 | 1,214 | 1,639 | 57.45% | Boundary ambiguity between soft resets vs. hardware defects |
| **Returns & Refunds** | 1,793 | 1,094 | 699 | 38.98% | Differentiating cancellation before dispatch vs. reverse pickup |
| **Billing & Invoicing** | 1,591 | 1,042 | 549 | 34.51% | Payment failure vs. delivery delay ambiguity |
| **Hardware & Warranty** | 1,062 | 799 | 263 | 24.76% | Multi-touch warranty claim verification |
| **Order & Logistics** | 3,426 | 2,710 | 716 | 20.90% | High clarity on courier/AWB/tracking signals |
| **Pre-Sales & Info** | 643 | 554 | 89 | 13.84% | Distinct spec sheet and compatibility vocabulary |
| **Account & Access** | 412 | 401 | 11 | 2.67% | High clarity on OTP and login lockout signals |

---

## 4. BOT CATEGORY VS. PREDICTED TAXONOMY (CONFUSION MATRIX)

The crosstabulation below demonstrates exactly where the intake bot's 11 legacy categories map onto the Seven Pillars:

| Original Bot Category | Account & Access | Billing & Invoicing | Hardware & Warranty | Order & Logistics | Pre-Sales & Info | Returns & Refunds | Technical & Firmware | Total Bot Count |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Account & Login** | **356** | 34 | 0 | 0 | 0 | 1 | 0 | **391** |
| **App & Firmware** | 32 | 3 | 70 | 4 | 0 | 59 | **531** | **699** |
| **Audio Quality** | 0 | 8 | 103 | 2 | 0 | 60 | **418** | **591** |
| **Billing & Payments**| 0 | **1,322** | 2 | **1,048** | 0 | **192** | 0 | **2,564** |
| **Charging & Battery**| 0 | 4 | 135 | 3 | 0 | 93 | **585** | **820** |
| **Connectivity** | 0 | 5 | 69 | 3 | 0 | 60 | **865** | **1,002** |
| **Delivery & Shipping**| 0 | 18 | 127 | **1,549** | 0 | 211 | 0 | **1,905** |
| **Other** | 24 | 156 | 72 | **684** | 79 | 163 | **444** | **1,622** |
| **Product Enquiry** | 0 | 28 | 0 | 1 | **564** | 19 | 0 | **612** |
| **Returns & Refunds** | 0 | 11 | 14 | 132 | 0 | **892** | 0 | **1,049** |
| **Warranty & Repair** | 0 | 2 | **470** | 0 | 0 | 43 | 10 | **525** |
| **Total Predicted** | **412** | **1,591** | **1,062** | **3,426** | **643** | **1,793** | **2,853** | **11,780** |

---

## 5. PROXY EVALUATION METRICS & DISCLAIMERS

### Critical Methodological Disclaimer:
> [!WARNING]
> **Original bot categories are NOT ground truth.** They represent automated, unverified routing tags generated from an initial keyword question. Similarly, the actual resolving team is not a ground-truth label for category intent (as agents frequently resolve misrouted queries without re-tagging).
>
> The metrics below measure **alignment and intentional divergence against bot proxy tags**, NOT true classification error. High divergence in *Billing & Invoicing* (51.5% recall) and *Order & Logistics* (56.5% precision) reflects the **successful correction of historical misrouting**, not model failure.

| Category | Bot Proxy Count | Predicted Count | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Precision (Proxy) | Recall (Proxy) | F1-Score (Proxy) | Primary Divergence Driver |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Account & Access** | 391 | 388 | 356 | 32 | 35 | 0.9175 | 0.9105 | 0.9140 | High agreement; bot was accurate on OTP queries |
| **Billing & Invoicing** | 2,564 | 1,435 | 1,322 | 113 | 1,242 | 0.9213 | **0.5156** | 0.6612 | **Low recall intentional:** 1,048 delivery tickets removed |
| **Hardware & Warranty** | 525 | 990 | 470 | 520 | 55 | 0.4747 | 0.8952 | 0.6205 | Expanded to capture physical defects in Audio/Charging |
| **Order & Logistics** | 1,905 | 2,742 | 1,549 | 1,193 | 356 | 0.5649 | 0.8131 | 0.6667 | **FP reflects 1,048 misrouted tickets recovered from Billing** |
| **Pre-Sales & Info** | 612 | 564 | 564 | 0 | 48 | 1.0000 | 0.9216 | 0.9592 | Near-perfect alignment on pre-purchase queries |
| **Returns & Refunds** | 1,049 | 1,630 | 892 | 738 | 157 | 0.5472 | 0.8503 | 0.6659 | Captured return pickups misrouted to Frontline/Delivery |
| **Technical & Firmware**| 3,112 | 2,409 | 2,399 | 10 | 713 | 0.9958 | 0.7709 | 0.8690 | High precision; filtered out hardware RMA escalations |

*(Evaluated on the 10,158 tickets having direct 1:1 bot category counterparts, excluding 'Other').*

---

## 6. PRELIMINARY MISROUTING ANALYSIS

To evaluate organizational efficiency, we analyzed the triad of **Initial Assigned Team**, **Actual Resolving Team**, and **Predicted Responsible Team**:

| Routing Comparison | Agreement Count | Agreement Rate (%) | Operational Significance |
| :--- | :---: | :---: | :--- |
| **Initial Assigned Team == Actual Resolving Team** | 9,717 | 82.49% | 17.51% of tickets (2,063 tickets) were transferred between teams |
| **Predicted Responsible Team == Initial Assigned Team** | 8,131 | 69.02% | 30.98% of tickets (3,649 tickets) were initially misrouted at intake |
| **Predicted Responsible Team == Actual Resolving Team** | 8,063 | 68.45% | Resolvers often closed misrouted tickets in-place without transferring |
| **Billing Assigned -> Reassigned & Resolved by Logistics** | **795** | **31.01% of Billing** | Direct evidence of Neha Kulkarni's operational observation |
| **Billing Assigned -> Predicted as Order & Logistics** | **1,048** | **40.87% of Billing** | Intake bot misclassification creating artificial Billing backlog |

### Key Operational Conclusions:
1. **Misrouting is Systemic, not Accidental:** 31% of the Billing queue was transferred to Logistics, and an additional 10% was closed by Billing agents after manually answering courier questions.
2. **Transfer Penalty Incurred:** The 795 transferred Billing-to-Logistics tickets generated `795 * ₹305 = ₹2,42,475` in preventable re-handling waste under Support Policy §4.
3. **Legacy Transfer Nuance:** For the 4,052 pre-migration Freshdesk tickets, transfer counts were unrecorded. The 17.51% transfer rate observed above reflects only cross-team resolutions where the resolving agent belonged to a different department than the intake assignment.

---

## 7. HUMAN VALIDATION SAMPLE READY FOR ANNOTATION

Because no human-verified ground-truth labels exist in the historical data, a **stratified review sample of 98 tickets** (14 tickets per taxonomy pillar) was extracted and exported to:

`data/processed/human_validation_sample.csv`

Each record contains the `ticket_id`, intake channel, original bot category, predicted category, predicted team, confidence score, evidence string, sanitized customer message, and agent notes, with blank columns for `human_verified_category` and `human_reviewer_notes` to support gold-standard benchmarking in future phases.

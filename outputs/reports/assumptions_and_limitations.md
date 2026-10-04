# ASSUMPTIONS, DATA LIMITATIONS & METHODOLOGICAL GOVERNANCE
**Project:** Vireo Audio Support Intelligence  
**Phase:** Step 3 — Data Validation, Monthly Business Analytics & Staffing Decision Engine  
**Author:** Senior Data Scientist & Analytics Engineer  
**Date:** October 2026  

---

## 1. DATA AUDIT FINDINGS & APPLIED SAFEGUARDS

Throughout Steps 1, 2, and 3, rigorous data quality checks were conducted across the 11,780 support records. The table below documents every anomaly discovered, its root cause, and the applied safeguard:

| Anomaly Discovered | Root Cause Identified | Applied Engineering Safeguard | Methodological Justification |
| :--- | :--- | :--- | :--- |
| **Negative Handle Times**<br>(2,575 tickets in `legacy_fd` had `resolved_at < first_response_at`) | Freshdesk event logs stored resolution in **UTC (+00:00)**, while helpdesk exports and creation/response timestamps were in **IST (+05:30)**. | Applied `+05:30:00` offset strictly to `legacy_fd.resolved_at`. Original `resolved_at` raw column is preserved untouched. | Eliminates 100% of negative handle times. The resulting legacy handle time distribution matches helpdesk metrics almost identically (mean 25.2h vs 24.4h). |
| **Missing Legacy Transfers**<br>(4,052 tickets had null `transfers`) | Freshdesk did not capture inter-team hand-offs. Field was introduced during the 14-Sep-2025 migration. | Null values in `transfers` are treated strictly as **unknown**, never imputed as zero. | Imputing zero would artificially depress historical transfer rates and distort post-migration comparisons. |
| **Blank CSAT Scores**<br>(6,435 tickets / 54.6% null) | Standard survey non-response. Per Policy §8, customer response rate is ~45%. | Excluded nulls from all denominator calculations when computing mean and median CSAT. Never imputed as zero. | Imputing zero would crash Vireo's CSAT from 3.38 to an absurd 1.54. |
| **Duplicate Agent Display Names**<br>(Two agents named "Om Sharma") | Two distinct agents share the same name (`A3006` in Indore, `A3029` in Bengaluru). | System operations, merges, and aggregations strictly utilize `agent_id` as primary key. | Prevents cross-site credential and performance attribution errors. |
| **Blank Order IDs**<br>(4,017 tickets lacked `order_id`) | Customers omitted quoting their order number during chatbot intake. | Executed fallback join on composite key `(customer_id, product_sku)` against `orders.csv`. | 100% of blank order tickets (4,017) successfully joined without orphan records. |
| **Dual Disbursement Violation**<br>(74 orders received both refund and replacement) | Lack of system cross-validation between Returns Desk and Escalations & Warranty. | Audited and quantified as ₹3.94L in financial leakage exposure. Flagged for hard validation rules. | Operating Policy §5 strictly prohibits dual disbursements. |

---

## 2. GOVERNING ASSUMPTIONS & UNCERTAINTIES

### 2.1. Agent Capacity & Handling Time Uniformity
- **Assumption:** Agent labor is valued at ₹165/hour across standard 8-hour shifts (Operating Policy §4).
- **Uncertainty Boundary:** Support tickets do not consume uniform handle times. A simple password reset takes 5 minutes, while an RMA diagnostic takes days. We do not use a simplistic "tickets divided by hours" model to claim employee capacity. Departmental evaluations evaluate median cycle times and actual observed throughput.

### 2.2. Agent Roster Temporal Stability
- **Assumption:** All 44 agents in `agents.csv` are active and resolved tickets in the core window.
- **Uncertainty Boundary:** `to_date` is 100% null in `agents.csv`. While all 44 agents were observed resolving tickets, the dataset does not capture individual sick leave, attrition, or mid-year promotions. Staffing conclusions assume the 44-agent roster reflects normal operational presence.

### 2.3. Transfer Cost Applicability
- **Assumption:** Each recorded internal transfer incurs ₹305 in administrative re-handling penalty (Operating Policy §4).
- **Uncertainty Boundary:** Policy §4 states ₹305 represents internal re-handling and administration. In practice, some transfers may be swift misroute re-assignments, while others involve detailed escalations. The ₹305 rate is applied uniformly as the mandated planning standard.

### 2.4. Proxy Labels vs. Ground Truth
- **Assumption:** Intake bot categories are used as a proxy reference to measure historical misrouting.
- **Uncertainty Boundary:** Bot categories are **not ground truth**. The 51.6% recall observed in Billing reflects deliberate correction of delivery misroutes, not classifier inaccuracy. True statistical precision/recall requires human annotation using the generated 98-ticket validation sample (`data/processed/human_validation_sample.csv`).

---

## 3. SCOPE EXCLUSIONS

The current delivery phase explicitly excludes:
- Production database installations (Docker, PostgreSQL, Redis, Kafka).
- Live CRM/ERP API webhook listeners or automatic order cancellations.
- Real-time carrier GPS tracking integrations.
- Speculative staffing models based on unverified employee timesheet data.

---

## 4. RECOMMENDED 90-DAY MEASURABLE OPERATIONAL GOAL

To provide Priya Raman, Arjun Mehta, and Neha Kulkarni with an actionable, accountable roadmap, we establish the following **90-Day Operational Target**:

```
                         THE 90-DAY OPERATIONAL TARGET
  "Reduce avoidable routing transfers into Logistics by 75% over the next 90 days
   while improving Logistics first-response SLA compliance from 83.6% to 90.0%
   (+6.4 percentage points)."
```

### Detailed Target Metrics & Success Criteria:

| Operational Dimension | Baseline Period (18M Baseline) | 90-Day Target Value | Target Improvement | Verification Mechanism |
| :--- | :---: | :---: | :---: | :--- |
| **Logistics Inbound Transfer Rate** | 31.2% (approx. 69 transfers/month) | **<= 8.0%** (< 18 transfers/month) | **-74.3% reduction** in avoidable queue transfers | Helpdesk transfer logs |
| **Logistics SLA Compliance** | 83.57% (16.43% breach rate) | **>= 90.00%** (<= 10.00% breach rate) | **+6.43 percentage points** compliance improvement | First-response SLA report |
| **Logistics Median Resolution Delay**| 26.03 hours | **<= 18.00 hours** | **-30.8% reduction** in total resolution time | Helpdesk resolution cycle metrics |
| **Avoidable Transfer Waste** | ₹20,940 / month | **<= ₹5,400 / month** | **Save ~₹1,86,000 annualized** | Support P&L transfer line |
| **Customer Satisfaction (Logistics)**| 2.89 / 5.0 | **>= 3.25 / 5.0** | **+0.36 point CSAT recovery** | Monthly CSAT survey |

### Execution Milestones:
- **Days 0–15:** Deploy Seven-Pillar keyword routing rules to the intake chatbot. Stop delivery complaints from routing to Billing.
- **Days 15–30:** Implement hard validation rules in helpdesk preventing dual refund and replacement disbursements on the same `order_id`.
- **Days 30–60:** Onboard **1 additional support hire into Logistics** to expand dedicated carrier escalation capacity.
- **Days 60–90:** Audit transfer reduction and SLA compliance against the 90-day targets before releasing budget for the second hire.

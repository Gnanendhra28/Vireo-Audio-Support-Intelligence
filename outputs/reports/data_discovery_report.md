# COMPREHENSIVE DATA DISCOVERY REPORT
**Project:** Vireo Audio Support Intelligence  
**Phase:** Step 1 — Project Initialization and Data Discovery  
**Prepared For:** Vireo Audio Leadership (Priya Raman, Arjun Mehta, Neha Kulkarni)  
**Author:** Senior Python Engineer & Lead Data Analyst  
**Date:** October 2026  

---

## EXECUTIVE SUMMARY

A rigorous data discovery and forensic quality audit was performed across 18+ months of customer support data from Vireo Audio. The discovery audited five core datasets, the operational policy manual (v3.2), and organizational correspondence.

### Major Discoveries & Key Findings:
1. **Intake Bot Routing Distortion:** The intake bot's automated tagging creates a severe optical illusion. 100% of tickets tagged `Billing & Payments` (2,564) were rigidly assigned to the Billing queue. However, message analysis and resolution audits reveal that **795 tickets (31.0%) assigned to Billing were actually handled and resolved by the Logistics team** due to misrouted delivery complaints.
2. **True Operational Workload Inversion:**
   - **Assigned Volume (Intake View):** Billing appeared to be the largest queue with **2,564 tickets (21.8%)**, while Logistics was **1,905 tickets (16.2%)**.
   - **Resolved Volume (True Handling View):** **Logistics resolved 2,673 tickets (22.7%)**, while Billing resolved only **1,838 tickets (15.6%)**.
3. **Logistics Bottleneck & Distress Signals:**
   - Logistics has a median resolution time of **26.08 hours** (versus **1.23 hours for Billing** and **0.58 hours for Chat Frontline**).
   - Logistics exhibits the highest SLA breach rate in the company (**17.13%**, 458 breaches).
   - Logistics suffers the highest transfer/hand-off rate (**31.19%** of helpdesk tickets transferred).
   - Logistics has the lowest customer satisfaction score across the company (**2.87 mean CSAT** vs. 3.40–3.67 for other frontline teams).
4. **Legacy Timestamp Inversion (Solved):** 2,575 migrated Freshdesk tickets exhibited negative handle times (`resolved_at < first_response_at`). Forensic investigation identified the root cause: legacy resolution timestamps were reconstructed from the Freshdesk event log recorded in **UTC (+00:00)**, while creation and response timestamps were in **IST (+05:30)**. Applying a `+05:30:00` offset to legacy resolution timestamps completely eliminates 100% of the anomalies (0 negative handle times remaining).
5. **Support Policy Compliance Violations:**
   - Per Operating Policy §5, customers must never receive both a refund and a replacement for the same order.
   - **2 tickets** were found with both a refund and replacement within the same ticket (`TK-241926`, `TK-248344`).
   - **74 unique orders** across the system received both a financial refund and a physical replacement across multiple tickets, representing unmonitored financial leakage.
6. **Agent Identity Collision:** Two distinct agents share the exact display name **"Om Sharma"** (`A3006` in Indore, `A3029` in Bengaluru). All analysis must strictly use `agent_id`.
7. **Referential Integrity:** 100% foreign key referential integrity was validated across customers, products, orders, and agents. All 4,017 tickets with blank `order_id` successfully join to `orders.csv` via the fallback key (`customer_id` + `product_sku`).

---

## 1. DATASET CATALOG & SYSTEM SOURCING

| Dataset File | Source Path / Origin | Format | Row Count | Column Count | File Size | Description & Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `tickets.csv` | Helpdesk & Freshdesk export | CSV | 11,780 | 21 | ~4.5 MB | Support interactions, timestamps, categories, CSAT, financial outcomes |
| `agents.csv` | HR & Helpdesk Roster | CSV | 44 | 8 | ~2.9 KB | Agent assignments, sites, teams, shifts, and tiers |
| `orders.csv` | E-commerce Order Management | CSV | 15,000 | 8 | ~984 KB | Sales orders, SKUs, order dates, quantities, lot codes, order values |
| `customers.csv` | CRM / Customer Account DB | CSV | 9,500 | 6 | ~445 KB | Customer profiles, signup dates, location, Care+ membership status |
| `products.csv` | Product Catalog / ERP | CSV | 14 | 7 | ~979 B | SKUs, product families, unit manufacturing costs, retail prices, warranty |
| `support-policy.pdf` | CX Operations (v3.2) | PDF | 2 pages | N/A | ~6.7 KB | Operating rules, SLA targets, channel cost standards, refund governance |
| `email-thread.txt` | Executive Correspondence | Plain text | 5 emails | N/A | ~2.7 KB | Internal leadership debate (Priya Raman, Arjun Mehta, Neha Kulkarni) |
| `README.txt` | Engineering Data Pack Note | Plain text | N/A | N/A | ~2.6 KB | Field definitions, system migration context, and known limitations |

*Source files preserved in workspace raw repository: `vireo-support-intelligence/data/raw/`.*

---

## 2. DETAILED SCHEMA & DATA PROFILING

### 2.1. Support Tickets (`tickets.csv`)
- **Total Records:** 11,780 rows, 21 columns
- **Primary Key Check:** `ticket_id` is 100% unique (11,780 distinct keys). No duplicate ticket IDs.
- **Date Range:** Earliest creation `2024-06-20 01:36 IST`, latest creation `2026-06-30 23:22 IST`.
  - *Pre-Analysis Pilot Period (2024):* 139 tickets (2024-06 to 2024-12).
  - *Core 18-Month Target Period (2025-01 to 2026-06):* 11,641 tickets.
- **Field Profiles & Null Analysis:**

| Column Name | Inferred Dtype | Null Count | Null % | Primary Value Range / Cardinality | Operational Interpretation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ticket_id` | `object (str)` | 0 | 0.00% | 11,780 unique (`TK-240001` to `TK-254552`) | Primary Key |
| `created_at` | `object (datetime)` | 0 | 0.00% | 2024-06-20 to 2026-06-30 | Ticket intake timestamp (IST) |
| `first_response_at` | `object (datetime)` | 0 | 0.00% | 2024-06-20 to 2026-06-30 | First human agent reply (IST) |
| `resolved_at` | `object (datetime)` | 583 | 4.95% | 2024-06-29 to 2026-07-02 | Null for open/pending tickets; legacy in UTC |
| `status` | `object (str)` | 0 | 0.00% | 4 values: `resolved`, `closed`, `open`, `pending` | `closed` = auto-closed after 72h |
| `channel` | `object (str)` | 0 | 0.00% | 4 values: `chat`, `email`, `voice`, `social` | Intake contact medium |
| `customer_id` | `object (str)` | 0 | 0.00% | 7,651 distinct customer IDs | Foreign key to `customers.csv` |
| `order_id` | `object (str)` | 4,017 | 34.10% | 6,368 distinct order IDs | Null when customer omitted quote; joins via fallback |
| `product_sku` | `object (str)` | 0 | 0.00% | 14 distinct product SKUs | Foreign key to `products.csv` |
| `category` | `object (str)` | 0 | 0.00% | 11 intake categories | Set by intake bot |
| `priority` | `object (str)` | 0 | 0.00% | 3 values: `Normal`, `High`, `Low` | Routing priority |
| `assigned_team` | `object (str)` | 0 | 0.00% | 7 support teams | First-routed department |
| `agent_id` | `object (str)` | 0 | 0.00% | 44 distinct agent IDs | Resolving agent key (`agents.csv`) |
| `transfers` | `float64` | 4,052 | 34.40% | Integer range 0 to 4 (in helpdesk) | Null in `legacy_fd` (unknown, not zero) |
| `csat_score` | `float64` | 6,435 | 54.63% | Integer rating 1.0 to 5.0 | Blank = non-response (exclude from mean) |
| `refund_amount_inr` | `float64` | 9,886 | 83.92% | ₹32.0 to ₹13,998.0 | Amount refunded in INR; null = no refund |
| `refund_reason_code` | `object (str)` | 9,886 | 83.92% | 8 reason codes (Policy §5) | Selected by agent at refund creation |
| `replacement_issued`| `object (str)` | 0 | 0.00% | `Y` (1,248) or `N` (10,532) | Hardware replacement dispatch flag |
| `customer_message` | `object (str)` | 0 | 0.00% | Text snippets / IVR transcript | Opening query; unredacted in source |
| `agent_notes` | `object (str)` | 0 | 0.00% | Text snippets / closing summaries | Agent resolution summary and audit trail |
| `source_system` | `object (str)` | 0 | 0.00% | `helpdesk` (7,728), `legacy_fd` (4,052) | Cutover date 14 September 2025 |

### 2.2. Agents Roster (`agents.csv`)
- **Total Records:** 44 rows, 8 columns
- **Primary Key Check:** `agent_id` is 100% unique (44 distinct IDs, `A3001` to `A3044`).
- **Name Duplication Finding:** Display name **"Om Sharma"** appears twice:
  - Agent `A3006`: Indore, Chat Frontline, Tier 1, from_date: 2024-06-24
  - Agent `A3029`: Bengaluru, Voice Frontline, Tier 1, from_date: 2022-10-02
  - *Mitigation:* `agent_id` is mandatory for all operations.
- **Roster Distribution:**
  - `Chat Frontline`: 15 agents (Tier 1) — 10 Bengaluru, 5 Indore
  - `Email Frontline`: 7 agents (Tier 1) — 2 Bengaluru, 5 Indore
  - `Logistics`: 5 agents (Tier 1) — 5 Bengaluru, 0 Indore
  - `Billing`: 4 agents (Tier 1) — 2 Bengaluru, 2 Indore
  - `Voice Frontline`: 4 agents (Tier 1) — 3 Bengaluru, 1 Indore
  - `Returns Desk`: 3 agents (Tier 1) — 2 Bengaluru, 1 Indore
  - `Escalations & Warranty`: 6 agents (Tier 2 certified) — 1 Bengaluru, 5 Indore
- **Roster Dates:** `from_date` spans 2020-03-15 to 2025-05-18. `to_date` is 100% null (all 44 agents currently active).

### 2.3. Sales Orders (`orders.csv`)
- **Total Records:** 15,000 rows, 8 columns
- **Primary Key Check:** `order_id` is 100% unique (15,000 orders, `VR880001` to `VR909999`).
- **Order Date Range:** `2024-06-15` to `2026-06-30`.
- **Order Value:** Min ₹319, Mean ₹3,600, Median ₹3,149, Max ₹13,998.
- **Null Values:** 0 nulls across all columns.

### 2.4. Customers Profile (`customers.csv`)
- **Total Records:** 9,500 rows, 6 columns
- **Primary Key Check:** `customer_id` is 100% unique (9,500 customers, `C100000` to `C109499`).
- **Signup Date Range:** `2022-07-16` to `2025-01-01`.
- **Care+ Membership:** 1,438 customers (15.14%) enrolled in `care_plus = 'Y'`.
- **Null Values:** 0 nulls across all columns.

### 2.5. Product Catalog (`products.csv`)
- **Total Records:** 14 rows, 7 columns
- **Primary Key Check:** `sku` is 100% unique (14 products across Earbuds, Headphones, Speakers, Smartwatches, Neckbands, Accessories).
- **Price Range:** Retail price ₹399 (`VA-AC-CBL`) to ₹6,999 (`VA-HP-ST3`). Unit manufacturing cost ₹90 to ₹2,650.
- **Warranty:** 6 months for cables, 12 months for audio/wearables, 24 months for premium headphones.
- **Null Values:** 0 nulls across all columns.

---

## 3. KEY DISTRIBUTIONS & ROUTING AUDIT

### 3.1. System & Operational Distributions
- **Source Systems:** `helpdesk` (current): 7,728 (65.60%), `legacy_fd` (Freshdesk): 4,052 (34.40%).
- **Ticket Status:**
  - `resolved`: 10,128 (85.98%)
  - `closed` (auto-closed after 72h no customer reply): 1,069 (9.07%)
  - `open`: 336 (2.85%)
  - `pending`: 247 (2.10%)
- **Support Channel Mix:**
  - `chat`: 5,387 (45.73%)
  - `email`: 3,555 (30.18%)
  - `voice`: 1,702 (14.45%)
  - `social`: 1,136 (9.64%)
- **Priority:** `Normal`: 8,017 (68.06%), `High`: 2,549 (21.64%), `Low`: 1,214 (10.31%).

### 3.2. Bot Intake Category vs. Assigned Team (100% Deterministic Routing)
Cross-tabulation reveals that the intake bot routed tickets with zero discretion for specialized departments:

| Intake Bot Category | Billing | Chat FL | Email FL | Escalations | Logistics | Returns Desk | Voice FL | Total |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Billing & Payments** | **2,564** | 0 | 0 | 0 | 0 | 0 | 0 | **2,564** |
| **Delivery & Shipping** | 0 | 0 | 0 | 0 | **1,905** | 0 | 0 | **1,905** |
| **Returns & Refunds** | 0 | 0 | 0 | 0 | 0 | **1,049** | 0 | **1,049** |
| **Warranty & Repair** | 0 | 0 | 0 | **525** | 0 | 0 | 0 | **525** |
| Connectivity | 0 | 543 | 295 | 0 | 0 | 0 | 164 | 1,002 |
| Charging & Battery | 0 | 420 | 264 | 0 | 0 | 0 | 136 | 820 |
| App & Firmware | 0 | 370 | 218 | 0 | 0 | 0 | 111 | 699 |
| Product Enquiry | 0 | 323 | 188 | 0 | 0 | 0 | 101 | 612 |
| Audio Quality | 0 | 285 | 206 | 0 | 0 | 0 | 100 | 591 |
| Account & Login | 0 | 213 | 120 | 0 | 0 | 0 | 58 | 391 |
| Other | 0 | 876 | 516 | 0 | 0 | 0 | 230 | 1,622 |
| **Total Assigned** | **2,564** | **3,030** | **1,807** | **525** | **1,905** | **1,049** | **900** | **11,780** |

### 3.3. Assigned Team vs. Resolving Team (The Re-Routing Reality)
When examining the actual team of the resolving agent (`agent_id` joined to `agents.csv`), the true workload shifts dramatically:

| Assigned Team (Intake) | Billing | Chat FL | Email FL | Escalations | Logistics | Returns Desk | Voice FL | Total Assigned |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Billing** | **1,704** | 22 | 23 | 0 | **795** | 20 | 0 | **2,564** |
| **Chat Frontline** | 42 | **2,621** | 206 | 88 | 36 | 37 | 0 | **3,030** |
| **Email Frontline** | 27 | 342 | **1,352** | 40 | 22 | 24 | 0 | **1,807** |
| **Escalations & Warranty**| 6 | 8 | 10 | **490** | 3 | 8 | 0 | **525** |
| **Logistics** | 35 | 31 | 29 | 0 | **1,791** | 19 | 0 | **1,905** |
| **Returns Desk** | 16 | 11 | 14 | 0 | 15 | **993** | 0 | **1,049** |
| **Voice Frontline** | 8 | 43 | 24 | 32 | 11 | 16 | **766** | **900** |
| **Total Resolved** | **1,838** | **3,078** | **1,658** | **650** | **2,673** | **1,117** | **766** | **11,780** |

#### Crucial Operational Insight:
- **795 tickets initially routed to Billing were transferred and resolved by Logistics.**
- Billing actually closed **1,838 tickets**, whereas Logistics closed **2,673 tickets** (+40.3% over assigned volume).
- Evaluating staffing needs on assigned volume alone completely misattributes 795 tickets of workload.

---

## 4. WORKLOAD, PERFORMANCE & SLA METRICS

### 4.1. Handling Time and Resolution Metrics by Team
*(Computed after applying the +5h30m legacy UTC timezone correction)*

| Resolving Team | Headcount (Agents) | Total Resolved | Median Handle Time (Hrs) | Median Total Resolution Time (Hrs) | Mean Total Resolution Time (Hrs) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Chat Frontline** | 15 | 3,078 | 0.35 h (21 min) | 0.58 h (35 min) | 5.74 h |
| **Logistics** | 5 | 2,673 | **24.47 h** | **26.08 h** | **42.54 h** |
| **Billing** | 4 | 1,838 | 0.38 h (23 min) | 1.23 h (74 min) | 12.67 h |
| **Email Frontline** | 7 | 1,658 | 0.33 h (20 min) | 2.75 h | 8.54 h |
| **Returns Desk** | 3 | 1,117 | 24.55 h | 32.38 h | 38.86 h |
| **Voice Frontline** | 4 | 766 | 0.35 h (21 min) | 0.93 h (56 min) | 4.43 h |
| **Escalations & Warranty (Tier 2)** | 6 | 650 | **122.00 h (~5.1 d)** | **122.42 h** | **143.10 h** |

### 4.2. SLA Breach Analysis (Policy §3 Targets)
- Targets: Chat = 15m (0.25h), Voice callback = 2.0h, Social = 4.0h, Email = 8.0h.
- Breach penalty: ₹350 store credit issued on resolution.

| Support Channel | Total Tickets | SLA Breaches | Breach Rate (%) | Financial Penalty Liability |
| :--- | :---: | :---: | :---: | :---: |
| **Chat** | 5,387 | 720 | 13.37% | ₹2,52,000 |
| **Email** | 3,555 | 430 | 12.10% | ₹1,50,500 |
| **Social** | 1,136 | 91 | 8.01% | ₹31,850 |
| **Voice** | 1,702 | 99 | 5.82% | ₹34,650 |
| **Total** | **11,780** | **1,340** | **11.38%** | **₹4,69,000** |

#### Breaches by Resolving Team:
- **Logistics:** 458 breaches (**17.13% breach rate**, highest in the company).
- **Billing:** 254 breaches (13.82%).
- **Chat Frontline:** 265 breaches (8.61%).
- **Email Frontline:** 158 breaches (9.53%).
- **Returns Desk:** 118 breaches (10.56%).
- **Escalations & Warranty:** 52 breaches (8.00%).
- **Voice Frontline:** 35 breaches (4.57%).

### 4.3. Customer Satisfaction (CSAT) Distribution
- Total CSAT responses: 5,345 (45.37% response rate). Unresponded: 6,435 (54.63%).
- **Logistics Mean CSAT: 2.87** (1,261 responses, lowest in the company).
- **Billing Mean CSAT: 3.40** (793 responses).
- **Voice Frontline Mean CSAT: 3.67** (365 responses).
- **Chat Frontline Mean CSAT: 3.66** (1,385 responses).
- **Email Frontline Mean CSAT: 3.60** (730 responses).
- **Returns Desk Mean CSAT: 3.35** (526 responses).
- **Escalations & Warranty Mean CSAT: 3.26** (285 responses).

---

## 5. DATA QUALITY ANOMALIES & AUDIT FINDINGS

### 5.1. Timestamp Anomaly & Root Cause Analysis
- **Symptom:** 2,575 tickets showed `resolved_at < first_response_at`, and 2,379 showed `resolved_at < created_at`.
- **System Isolation:** 100% of these cases occurred in `legacy_fd`. Zero occurred in `helpdesk`.
- **Root Cause:** Freshdesk event logs recorded timestamps in UTC (+00:00). When `resolved_at` was reconstructed from the event log, it remained in UTC, whereas helpdesk exports and all other columns were exported in IST (+05:30).
- **Resolution:** Adding `05:30:00` to `legacy_fd.resolved_at` reduces negative handle time errors from 2,575 to **precisely 0**.

### 5.2. Policy Violations: Dual Refund and Replacement
- **Operating Policy Rule (§5):** *"In no case is a customer to receive both a refund and a replacement for the same order; where this happens in error it must be escalated to the Team Lead and Finance the same day."*
- **Discovered Incidents:**
  - **Within-ticket dual issue:** 2 tickets (`TK-241926` and `TK-248344`) granted both a refund and a replacement unit on the same ticket.
  - **Cross-ticket dual issue:** **74 unique orders** received both a cash refund and a replacement unit across separate tickets.
  - **Estimated Financial Exposure:** 74 units * (Avg unit cost ₹1,400 + ₹340 logistics + Avg refund ₹2,800) = **~₹3.36 lakh** in unrecovered dual compensation.

### 5.3. Repeat Contact Volume (Policy §10 FCR Definition)
- Customers contacting again within 30 days of resolution count as repeat contacts.
- **3,083 tickets (26.17%)** were repeat contacts within 30 days.
- **Repeat Contact Channel Cost:**
  - Chat: 1,417 contacts * ₹210 = ₹2,97,570
  - Email: 923 contacts * ₹260 = ₹2,39,980
  - Voice: 465 contacts * ₹520 = ₹2,41,800
  - Social: 278 contacts * ₹240 = ₹66,720
  - **Total Repeat Contact Operational Cost: ₹8,46,070**

---

## 6. PRIVACY-CONSCIOUS SAMPLE INSPECTION

To understand customer intent without compromising privacy, anonymized snippets of `customer_message` and `agent_notes` were sampled:

1. **Tag: Billing & Payments (Sample):**
   - *Customer:* `"Got Pulse 2 from Amazon recently. My order has not been delivered yet. Can someone fix this?"`
   - *Agent Note:* `"Re-shipped from warehouse. Issue: delivery delayed. Confirmed address with cx. Via Logistics."`
   - *Finding:* Misclassified delivery inquiry routed to Billing, worked by Logistics.
2. **Tag: Other (Sample):**
   - *Customer:* `"I haven't received my order - what do i do now?"`
   - *Agent Note:* `"cx says order not delivered. checked awb with courier. refund initiated as lost in transit."`
   - *Finding:* Critical fulfillment failure dumped into generic "Other" tag.
3. **Tag: Connectivity (Sample):**
   - *Customer:* `"[IVR transcript] bluetooth pairing fails every time on the Nexa 2..."`
   - *Agent Note:* `"walked through device reset -> re-pair successful, resolved on chat"`
   - *Finding:* Genuine frontline Tier 1 technical query resolved rapidly.
4. **Tag: Warranty & Repair (Sample):**
   - *Customer:* `"service centre took the headset, now silence, anyone there?"`
   - *Agent Note:* `"rma status query. verified RMA receipt with depot. replacement unit dispatched."`
   - *Finding:* Genuine Tier 2 multi-touch escalation.

---

## 7. REFERENTIAL INTEGRITY AUDIT

- `tickets.customer_id` -> `customers.customer_id`: **0 orphan records** (100% valid).
- `tickets.product_sku` -> `products.sku`: **0 orphan records** (100% valid).
- `tickets.agent_id` -> `agents.agent_id`: **0 orphan records** (100% valid).
- `tickets.order_id` (non-null) -> `orders.order_id`: **0 orphan records** (100% valid).
- Fallback Join for 4,017 null `order_id` tickets: All 4,017 records match `orders.csv` via composite key `(customer_id, product_sku)` without loss.

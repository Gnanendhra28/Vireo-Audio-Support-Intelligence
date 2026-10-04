# STAFFING CAPACITY & OPERATIONS DECISION REPORT
**Project:** Vireo Audio Support Intelligence  
**Phase:** Step 3 — Data Validation, Monthly Business Analytics & Staffing Decision Engine  
**Analysis Period:** 1 January 2025 through 30 June 2026 (18 Months Baseline)  
**Prepared For:** Priya Raman (Head of CX), Arjun Mehta (Finance Controller), Neha Kulkarni (Support Operations Manager)  
**Author:** Senior Data Scientist & Support Operations Consultant  
**Date:** October 2026  

---

## EXECUTIVE SUMMARY & STRATEGIC RECOMMENDATION

This report directly addresses Priya Raman's executive question:  
**"Should Vireo Audio allocate two additional support hires to Billing, Logistics, or another team—or can process improvements reduce the need for hiring?"**

Based on a forensic audit of 18 months of actual ticket resolution, handling times, SLA penalties, and transfer matrices, our evidence-based findings are:

1. **Allocating Hires to Billing is Disproven by the Data:**
   - Billing is **not understaffed**. Its intake queue appears large (2,425 tickets) only because the intake chatbot misroutes delivery complaints mentioning payments.
   - Billing actually resolves only **99.9 tickets/month across 4 agents** (25.0 tickets/agent/month).
   - Billing agents resolve tickets in a median time of **1.22 hours** (under 75 minutes), with a median active handle time of **23 minutes**.
   - Billing successfully sheds 627 misrouted tickets to other departments. Adding 2 agents to Billing would create acute overstaffing and idle capacity.
2. **Logistics is in Acute Operational Failure:**
   - Logistics has a roster of only **5 agents** but resolved **2,574 tickets** (143.0 tickets/month, or **28.6 tickets/agent/month**—the highest load in Vireo).
   - Logistics suffers a median resolution time of **26.03 hours** (21x slower than Billing).
   - Logistics generated **423 SLA breaches (16.43% breach rate)**, racking up **₹1,48,050 in automated store credit penalties**.
   - Logistics absorbed **658 transfers (50.65% of all helpdesk transfers)**, with a staggering **31.2% transfer rate**.
   - Customer satisfaction in Logistics is the lowest in the company (**2.89 CSAT** vs. 3.40–3.67 for other teams).
3. **The Recommended Phased Decision (Process First, Targeted Headcount Second):**
   - **Phase 1 (Immediate Process Fix, Days 0–30):** Retrain and update intake bot routing rules using the Seven-Pillar taxonomy. Route delivery complaints directly to Logistics, eliminating 696 avoidable re-transfers from Billing and saving **₹1,41,520 annually** in direct administrative transfer waste (`₹305/transfer`), and **₹1,99,853 annually (~₹2.00 Lakh/year)** when factoring in associated SLA penalties.
   - **Phase 2 (Targeted Headcount Allocation, Days 30–60):** Allocate **1 hire to Logistics** (₹4.5L/year). When offset by the ~₹2.00L in transfer and SLA process savings, the net annual cost of this hire is only **~₹2.50 Lakh**, while immediately increasing Logistics capacity by +20% to eliminate the 26-hour resolution delay.
   - **Phase 3 (Frontline Capacity or Budget Hold):** Allocate the **second hire to Chat Frontline** (Vireo's highest incoming channel with 13.4% SLA breaches), OR retain the remaining ₹4.5L in budget reserve pending post-process-fix 90-day review.

---

## 1. COMPREHENSIVE TEAM-BY-TEAM CAPACITY AUDIT

*Baseline: 18 months (Jan 2025 – Jun 2026). Fully loaded labor rate: ₹165/agent-hour across 8-hour shifts.*

| Department | Tier | Roster Headcount | Assigned Intake Vol. | Actual Resolved Vol. | Net Volume Delta | Monthly Avg. Resolved | Monthly Tickets / Agent | Median Res. Time (h) | Median Handle Time (h) | SLA Breaches | SLA Breach Rate (%) | Transfers (Helpdesk) | CSAT Mean |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Billing** | 1 | 4 | 2,425 | 1,798 | -627 (-25.9%) | 99.9 | 25.0 | 1.22 h | 0.38 h (23m) | 241 | 13.40% | 116 | 3.41 |
| **Logistics** | 1 | 5 | 1,905 | **2,574** | **+669 (+35.1%)** | **143.0** | **28.6** | **26.03 h** | **24.47 h** | **423** | **16.43%** | **658** | **2.89** |
| **Returns Desk** | 1 | 3 | 1,049 | 1,117 | +68 (+6.5%) | 62.1 | 20.7 | 32.38 h | 24.55 h | 118 | 10.56% | 114 | 3.35 |
| **Chat Frontline** | 1 | 15 | 3,030 | 3,078 | +48 (+1.6%) | 171.0 | 11.4 | 0.58 h | 0.35 h (21m) | 265 | 8.61% | 152 | 3.66 |
| **Email Frontline**| 1 | 7 | 1,807 | 1,658 | -149 (-8.2%) | 92.1 | 13.2 | 2.75 h | 0.33 h (20m) | 158 | 9.53% | 129 | 3.60 |
| **Voice Frontline**| 1 | 4 | 900 | 766 | -134 (-14.9%) | 42.6 | 10.6 | 0.93 h | 0.35 h (21m) | 35 | 4.57% | 5 | 3.67 |
| **Escalations & Wty**| 2 | 6 | 525 | 650 | +125 (+23.8%) | 36.1 | 6.0 | **122.42 h** | **122.00 h** | 52 | 8.00% | 125 | 3.26 |

---

## 2. DETAILED DEPARTMENTAL PROFILES

### 2.1. Billing Team (Tier 1)
- **Current Staffing:** 4 agents (2 Bengaluru, 2 Indore).
- **Workload Trend:** Resolved 1,798 tickets across 18 months (~100 tickets/month). Handled volume is stable across quarters.
- **Resolution Velocity:** Median resolution time is **1.22 hours**; median active handle time is **23 minutes**. 
- **The Routing Reality:** Intake assigned 2,425 tickets, but Billing shed a net 627 tickets (resolving 1,798). Specifically, 696 tickets in the core 18M window were misrouted to Billing and resolved by Logistics (795 all-time across the full dataset including 2024 pilot).
- **Backlog & Queue Health:** Open backlog is low (79 tickets company-wide in Billing).
- **Hiring Assessment:** **REJECT HIRING.** Adding 2 hires to Billing would increase headcount from 4 to 6 (+50%), reducing tickets per agent to an unviable ~16 tickets/month. Billing does not have a capacity problem; it has an intake filtering problem.

### 2.2. Logistics Team (Tier 1)
- **Current Staffing:** 5 agents (all 5 Bengaluru).
- **Workload Trend:** Severe upward pressure. Handled volume jumped from 70 tickets/month in early 2025 to over 200 tickets/month during Q4 peak.
- **Resolution Velocity:** Median resolution time is **26.03 hours**. Because carriers take 24–48 hours to confirm delivery attempts and AWB scans, tickets remain open in Logistics queues for days.
- **Transfer Influx:** Absorbed 658 recorded transfers in helpdesk (31.2% transfer rate). 50.6% of all helpdesk transfers land on Logistics desks.
- **SLA & CSAT Impact:** Highest breach rate (16.43%, 423 breaches) and lowest CSAT (2.89). Customers are deeply dissatisfied by delivery delays and carrier silence.
- **Hiring Assessment:** **STRONGLY RECOMMEND 1 HIRE.** Logistics carries the highest tickets per agent (28.6/month) on the longest cycle time (26 hours). A 6th agent increases dedicated carrier follow-up capacity by +20%, directly compressing resolution cycle time.

### 2.3. Returns Desk (Tier 1)
- **Current Staffing:** 3 agents (2 Bengaluru, 1 Indore).
- **Workload & Refund Role:** Resolved 1,117 tickets, processing 53% of all company refunds.
- **Operating Policy Context (§6):** Returns Desk processes refunds *by operational design*. High refund counts are its core mandate, not evidence of queue distress.
- **Resolution Time:** Median resolution is **32.38 hours**, reflecting physical reverse courier pickup and warehouse QC inspection times.
- **CSAT:** 3.35 / 5.0 (healthy considering return interactions).
- **Hiring Assessment:** **MONITOR ONLY.** Roster of 3 agents is tight (20.7 tickets/agent/month), but queue metrics are stable and do not warrant priority over Logistics.

### 2.4. Escalations & Warranty (Tier 2 Certified)
- **Current Staffing:** 6 certified agents (1 Bengaluru, 5 Indore).
- **Operating Policy Context (§6):** Tier 2 handles certified warranty claims, RMA approvals, and service center investigations. Multi-touch cases measured in *days, not tickets per week*.
- **Resolution Time:** Median resolution time is **122.42 hours (~5.1 days)**, reflecting depot inspection and repair cycles.
- **Volume:** 36.1 tickets/month (6.0 tickets/agent/month).
- **Hiring Assessment:** **DO NOT EXPAND.** Tier 2 staffing is adequate for certified RMA volumes. Raw volume must never be compared to Tier 1 frontline queues.

### 2.5. Frontline Teams (Chat, Email, Voice)
- **Chat Frontline (15 agents):** Handles 45.7% of all company interactions. Median resolution is fast (0.58 hours), but generated 265 SLA breaches due to 15-minute response target spikes. A strong candidate for the second hire if SLA protection is prioritized.
- **Email Frontline (7 agents):** Stable resolution (2.75 hours), low breach rate (9.53%), healthy CSAT (3.60).
- **Voice Frontline (4 agents):** Lowest breach rate (4.57%), fastest handle time (0.35h), highest CSAT (3.67).

---

## 3. COMPARATIVE HIRING MATRIX: BILLING VS. LOGISTICS

| Dimension | Billing Team | Logistics Team | Evidence & Operational Conclusion |
| :--- | :---: | :---: | :--- |
| **Intake Queue Share** | 20.8% (2,425) | 16.4% (1,905) | Bot misclassification creates artificial Billing inflation |
| **Actual Handled Volume**| 15.4% (1,798) | **22.1% (2,574)** | **Logistics handles 43.2% more volume than Billing** |
| **Current Headcount** | 4 agents | 5 agents | Workload ratio is 25.0 vs. 28.6 tickets/agent/month |
| **Median Resolution Delay**| **1.22 hours** | **26.03 hours** | **Logistics takes 21.3x longer to resolve customer issues** |
| **SLA Breaches (Core 18M)**| 241 breaches | **423 breaches** | **Logistics causes 75.5% more SLA breaches than Billing** |
| **SLA Credit Penalties** | ₹84,350 | **₹1,48,050** | Logistics generates ₹63,700 more in direct cash credit losses |
| **Transfer Rate (Helpdesk)**| 8.5% (116) | **31.2% (658)** | Logistics bears 50.6% of all internal transfer friction |
| **Customer CSAT Score** | 3.41 / 5.0 | **2.89 / 5.0** | **Logistics has the worst customer sentiment in Vireo** |
| **Verdict** | **DO NOT HIRE** | **ALLOCATE HIRE** | **Data completely refutes hiring into Billing** |

---

## 4. THE PROCESS IMPROVEMENT ALTERNATIVE (ARJUN MEHTA'S INQUIRY)

Arjun Mehta correctly asked: *"I'd rather fix a process than hire into it if that's an option."*

### What Process Fixes Can Achieve:
1. **Intake Bot Re-Classification:**
   - Re-configuring the intake chatbot with the Seven-Pillar keyword patterns prevents delivery inquiries from routing to Billing.
   - Eliminates ~627 misrouted tickets over 18 months (~35–40 tickets/month).
   - **Direct Transfer Savings:** ~40 transfers/month * ₹305 = **~₹1,46,400 annually**.
   - **SLA Breach Avoidance:** Misrouted tickets currently wait ~1.2h in Billing before transfer, causing first-response breaches in Logistics. Direct routing avoids an estimated ~15 breaches/month = **~₹63,000 annually**.
   - **Total Annual Process Opportunity: ~₹2,09,400**.
2. **Does Process Fix Completely Eliminate the Need for Hires?**
   - **No, but it funds 50% of a hire.**
   - Even after direct routing, Logistics must still handle ~145 tickets/month with complex carrier delays. Process improvement removes queue ping-pong, but does not add the human capacity needed to call couriers, inspect depot tracking, and answer customer chats.
   - **The Synthesis:** Combine the process fix (~₹2.1L savings) with **1 new hire in Logistics** (₹4.5L cost). The net financial impact is only **₹2.4L/year**, while solving the company's biggest operational bottleneck.

# MONTHLY BUSINESS ANALYTICS & SUPPORT OPERATIONS REPORT
**Project:** Vireo Audio Support Intelligence  
**Phase:** Step 3 — Data Validation, Monthly Business Analytics & Staffing Decision Engine  
**Analysis Period:** 1 January 2025 through 30 June 2026 (18 Months Inclusive)  
**Prepared For:** Priya Raman (Head of CX), Arjun Mehta (Finance Controller), Neha Kulkarni (Support Operations Manager)  
**Author:** Senior Data Scientist & Support Operations Consultant  
**Date:** October 2026  

---

## EXECUTIVE SUMMARY

A comprehensive monthly operational audit was conducted across the core 18-month target window (**11,641 tickets** created between 1 January 2025 and 30 June 2026). Pre-period pilot records from 2024 (139 tickets) were cataloged and excluded from monthly KPI calculations to preserve temporal integrity.

### Key Monthly Analytics Findings:
1. **Volume Trajectory & Growth S-Curve:**
   - Inbound support volume expanded from **314 tickets in January 2025** to a peak of **952 tickets in November 2025** during the festive/Diwali season, stabilizing at **750–830 tickets/month** in 2026.
   - Cumulative core window incoming: **11,641 tickets**. Resolved: **9,997 tickets (85.88%)**; Auto-Closed (72h no reply): **1,061 tickets (9.11%)**; Active Backlog (Open + Pending): **583 tickets (5.01%)**.
2. **True Monthly Departmental Burden:**
   - **Logistics resolved 2,574 tickets** over the 18 months (**143.0 tickets/month** across 5 agents, or **28.6 tickets/agent/month**), exceeding its assigned intake volume of 1,905 by **+669 tickets (+35.1%)**.
   - **Billing resolved 1,798 tickets** (**99.9 tickets/month** across 4 agents, or **25.0 tickets/agent/month**), running at a net delta of **-627 tickets (-25.9%)** below its assigned intake volume (2,425 tickets).
3. **Severe Operational Delay in Logistics:**
   - Logistics maintained a median resolution time of **26.03 hours** across the 18 months, compared to **1.22 hours for Billing**, **0.58 hours for Chat Frontline**, and **0.93 hours for Voice Frontline**.
   - Logistics generated **423 SLA breaches (16.43% breach rate)**, creating **₹1,48,050** in automated store credit liabilities.
4. **Customer Sentiment Divergence:**
   - Out of 5,283 customer CSAT ratings in the core window (45.38% response rate), **Logistics scored the lowest across Vireo at 2.89 / 5.0**.
   - Frontline teams scored between **3.60 and 3.67**, while Billing scored **3.41**.
5. **Transfer Observability & System Transition:**
   - Helpdesk migration went live on **14 September 2025**. Pre-migration Freshdesk records (January – August 2025) lack transfer logs (unrecorded, not zero).
   - In the 9.5 months of helpdesk tracking, **1,299 internal transfers** were recorded. **Logistics received 658 of these transfers (50.65%)**, suffering a **31.2% transfer rate**.
6. **Repeat Contact Deficit:**
   - **3,079 tickets (26.45%)** were repeat contacts from the same customer within 30 days of prior resolution, generating **₹8,44,250** in channel re-handling costs.

---

## 1. MONTH-BY-MONTH OPERATIONAL KPIS TABLE

*Incoming volume is grouped by ticket creation month. Resolved volume includes all closed attendances.*

| Month | Incoming Volume | Resolved Tickets | Auto-Closed (72h) | Open Backlog | Pending Backlog | SLA Breaches | SLA Breach Rate (%) | Median Res. Time (h) | CSAT Responses | Mean CSAT (1-5) | Observable Transfers | Repeat Contacts (30d) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2025-01** | 314 | 268 | 28 | 8 | 10 | 38 | 12.10% | 1.76 | 136 | 3.36 | *Unrecorded* | 42 |
| **2025-02** | 368 | 317 | 32 | 11 | 8 | 50 | 13.59% | 2.33 | 161 | 3.43 | *Unrecorded* | 82 |
| **2025-03** | 462 | 404 | 44 | 6 | 8 | 54 | 11.69% | 1.75 | 204 | 3.33 | *Unrecorded* | 117 |
| **2025-04** | 449 | 380 | 41 | 18 | 10 | 52 | 11.58% | 2.27 | 211 | 3.27 | *Unrecorded* | 116 |
| **2025-05** | 424 | 370 | 37 | 7 | 10 | 49 | 11.56% | 2.10 | 179 | 3.31 | *Unrecorded* | 90 |
| **2025-06** | 439 | 372 | 48 | 10 | 9 | 48 | 10.93% | 2.19 | 202 | 3.41 | *Unrecorded* | 138 |
| **2025-07** | 462 | 391 | 54 | 8 | 9 | 50 | 10.82% | 2.20 | 208 | 3.27 | *Unrecorded* | 111 |
| **2025-08** | 695 | 604 | 55 | 17 | 19 | 78 | 11.22% | 1.93 | 313 | 3.37 | *Unrecorded* | 191 |
| **2025-09** | 671 | 579 | 59 | 18 | 15 | 74 | 11.03% | 2.05 | 299 | 3.33 | 75 | 188 |
| **2025-10** | 847 | 719 | 80 | 26 | 22 | 87 | 10.27% | 2.10 | 391 | 3.38 | 145 | 224 |
| **2025-11** | 952 | 814 | 86 | 28 | 24 | 105 | 11.03% | 2.18 | 450 | 3.45 | 175 | 247 |
| **2025-12** | 869 | 751 | 75 | 24 | 19 | 102 | 11.74% | 1.76 | 426 | 3.46 | 162 | 241 |
| **2026-01** | 812 | 694 | 77 | 25 | 16 | 93 | 11.45% | 2.08 | 362 | 3.38 | 119 | 231 |
| **2026-02** | 733 | 632 | 65 | 20 | 16 | 82 | 11.19% | 2.13 | 336 | 3.40 | 114 | 202 |
| **2026-03** | 780 | 671 | 67 | 23 | 19 | 89 | 11.41% | 2.22 | 341 | 3.38 | 131 | 213 |
| **2026-04** | 832 | 730 | 67 | 19 | 16 | 93 | 11.18% | 1.83 | 366 | 3.43 | 132 | 210 |
| **2026-05** | 756 | 640 | 73 | 24 | 19 | 74 | 9.79% | 2.00 | 360 | 3.36 | 113 | 184 |
| **2026-06** | 776 | 671 | 74 | 18 | 13 | 74 | 9.54% | 2.21 | 340 | 3.42 | 133 | 192 |
| **Total / Avg**| **11,641**| **9,997** | **1,061** | **310** | **273** | **1,292** | **11.10%** | **2.08 h** | **5,283** | **3.38** | **1,299** | **3,079** |

---

## 2. MONTHLY PREDICTED CATEGORY VOLUME PIVOT TABLE

*Shows actual customer intent across the Seven Pillars based on ticket creation month:*

| Month | Order & Logistics | Technical & Firmware | Returns & Refunds | Billing & Invoicing | Hardware & Warranty | Pre-Sales & Info | Account & Access | Total Incoming |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2025-01** | 84 | 82 | 47 | 45 | 28 | 17 | 11 | **314** |
| **2025-02** | 100 | 97 | 56 | 50 | 32 | 19 | 14 | **368** |
| **2025-03** | 132 | 116 | 68 | 65 | 40 | 25 | 16 | **462** |
| **2025-04** | 129 | 107 | 71 | 64 | 39 | 24 | 15 | **449** |
| **2025-05** | 122 | 102 | 64 | 60 | 37 | 23 | 16 | **424** |
| **2025-06** | 125 | 109 | 66 | 61 | 38 | 24 | 16 | **439** |
| **2025-07** | 133 | 115 | 69 | 65 | 40 | 24 | 16 | **462** |
| **2025-08** | 195 | 171 | 108 | 94 | 63 | 39 | 25 | **695** |
| **2025-09** | 188 | 164 | 105 | 91 | 61 | 38 | 24 | **671** |
| **2025-10** | 241 | 207 | 131 | 115 | 77 | 47 | 29 | **847** |
| **2025-11** | 272 | 231 | 147 | 129 | 87 | 52 | 34 | **952** |
| **2025-12** | 248 | 212 | 134 | 118 | 79 | 48 | 30 | **869** |
| **2026-01** | 232 | 198 | 125 | 110 | 74 | 45 | 28 | **812** |
| **2026-02** | 209 | 179 | 113 | 100 | 67 | 40 | 25 | **733** |
| **2026-03** | 223 | 190 | 120 | 106 | 71 | 43 | 27 | **780** |
| **2026-04** | 237 | 203 | 128 | 113 | 76 | 46 | 29 | **832** |
| **2026-05** | 215 | 184 | 117 | 103 | 69 | 42 | 26 | **756** |
| **2026-06** | 221 | 189 | 120 | 105 | 71 | 43 | 27 | **776** |
| **Total** | **3,297** | **2,853** | **1,793** | **1,581** | **1,062** | **643** | **412** | **11,641** |

*(Note: The 139 excluded 2024 pilot tickets contained 129 Order & Logistics and 10 Billing tickets, reconciling with the 3,426 and 1,591 full-dataset totals).*

---

## 3. MONTHLY RESOLVING TEAM VOLUME PIVOT TABLE

*Shows actual workload handled by each department based on the resolving agent's roster team:*

| Month | Chat Frontline | Logistics | Billing | Email Frontline | Returns Desk | Voice Frontline | Escalations & Wty (T2) | Total Handled |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2025-01** | 80 | 70 | 48 | 44 | 30 | 24 | 18 | **314** |
| **2025-02** | 98 | 81 | 58 | 53 | 36 | 22 | 20 | **368** |
| **2025-03** | 122 | 103 | 72 | 66 | 44 | 30 | 25 | **462** |
| **2025-04** | 119 | 99 | 69 | 64 | 43 | 30 | 25 | **449** |
| **2025-05** | 112 | 94 | 66 | 60 | 41 | 28 | 23 | **424** |
| **2025-06** | 116 | 97 | 68 | 63 | 42 | 29 | 24 | **439** |
| **2025-07** | 122 | 102 | 72 | 66 | 44 | 30 | 26 | **462** |
| **2025-08** | 184 | 154 | 107 | 99 | 67 | 45 | 39 | **695** |
| **2025-09** | 177 | 148 | 104 | 96 | 64 | 44 | 38 | **671** |
| **2025-10** | 224 | 187 | 131 | 121 | 81 | 55 | 48 | **847** |
| **2025-11** | 252 | 210 | 148 | 136 | 91 | 62 | 53 | **952** |
| **2025-12** | 230 | 192 | 135 | 124 | 83 | 56 | 49 | **869** |
| **2026-01** | 215 | 179 | 126 | 116 | 78 | 53 | 45 | **812** |
| **2026-02** | 194 | 162 | 114 | 105 | 70 | 48 | 40 | **733** |
| **2026-03** | 206 | 172 | 121 | 112 | 75 | 50 | 44 | **780** |
| **2026-04** | 220 | 184 | 129 | 119 | 80 | 54 | 46 | **832** |
| **2026-05** | 200 | 167 | 117 | 108 | 73 | 49 | 42 | **756** |
| **2026-06** | 206 | 173 | 120 | 111 | 75 | 50 | 41 | **776** |
| **Total** | **3,078** | **2,574** | **1,798** | **1,658** | **1,117** | **766** | **650** | **11,641** |

---

## 4. INTAKE ASSIGNED VOLUME VS. ACTUAL RESOLVED WORKLOAD

The table below contrasts what each department *appeared* to receive via the intake bot versus what each department *actually resolved*:

| Department | Tier | Roster Headcount | Intake Assigned Volume | Actual Resolved Volume | Net Workload Delta | Monthly Avg. Resolved | Monthly Tickets / Agent |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Chat Frontline** | 1 | 15 | 3,030 | 3,078 | +48 (+1.6%) | 171.0 | 11.4 |
| **Logistics** | 1 | 5 | 1,905 | **2,574** | **+669 (+35.1%)** | **143.0** | **28.6 (Highest)** |
| **Billing** | 1 | 4 | **2,425** | **1,798** | **-627 (-25.9%)** | **99.9** | **25.0** |
| **Email Frontline** | 1 | 7 | 1,807 | 1,658 | -149 (-8.2%) | 92.1 | 13.2 |
| **Returns Desk** | 1 | 3 | 1,049 | 1,117 | +68 (+6.5%) | 62.1 | 20.7 |
| **Voice Frontline** | 1 | 4 | 900 | 766 | -134 (-14.9%) | 42.6 | 10.6 |
| **Escalations & Wty**| 2 | 6 | 525 | 650 | +125 (+23.8%) | 36.1 | 6.0 (Multi-touch) |
| **Total** | — | **44** | **11,641** | **11,641** | **0** | **646.7** | **14.7** |

---

## 5. AUDIT SUMMARY & RECONCILIATION

- **Date Consistency:** 11,641 core tickets + 139 pilot tickets = 11,780 total tickets.
- **Status Reconciliation:** 9,997 resolved + 1,061 auto-closed + 310 open + 273 pending = 11,641 tickets (100% accounted for).
- **Roster Alignment:** All 44 agents in `agents.csv` actively resolved tickets in the core window. No phantom agents detected.

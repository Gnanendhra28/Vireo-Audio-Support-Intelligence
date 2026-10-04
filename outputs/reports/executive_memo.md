# BUSINESS MEMORANDUM

**TO:** Priya Raman, Head of Customer Experience  
**FROM:** Support Operations Data Science & Analytics Team  
**DATE:** October 4, 2026  
**SUBJECT:** Evidence-Based Support Staffing and Operational Improvement Recommendation  

---

### Executive Recommendation

We recommend **declining the immediate hiring of two support agents for the Billing team** and adopting a **phased, process-first operational strategy**. Empirical analysis of 18 months of support operations reveals that Billing possesses ample capacity (resolving issues in a median 1.22 hours with 23 minutes active touch time) and that its apparent intake queue is inflated by an intake chatbot misrouting delivery inquiries. Instead, Vireo should **immediately implement intake bot routing re-engineering (Phase 1)**, consider a **conditional allocation of one hire to the Logistics team (Phase 2)** strictly subject to verifying active team capacity, and **hold the second headcount in reserve pending a formal 90-day post-intervention review (Phase 3)**. Operational process changes and courier API integrations are required alongside any staffing adjustments, as hiring alone cannot resolve carrier-dependent delays.

---

### Key Decision-Relevant Evidence Summary

The table below reconciles 18 months of support data (1 Jan 2025 – 30 Jun 2026), isolating observed operational reality from hypothetical projections:

| Operational Dimension | Billing Team | Logistics Team | Company Baseline | Nature of Evidence & Audit Reference |
| :--- | :---: | :---: | :---: | :--- |
| **Roster Headcount** | 4 agents | 5 agents | 44 agents (Company) | Observed Roster Snapshot |
| **Assigned Intake Volume** | 2,425 tickets (20.8%) | 1,905 tickets (16.4%) | 11,641 core tickets | Observed Helpdesk Intake Queue |
| **Actual Resolved Volume** | 1,798 tickets (15.4%) | **2,574 tickets (22.1%)** | 11,641 core tickets | Observed Final Resolution Volume |
| **Volume Differential** | **-627 net delta (-25.9%)** | **+669 net delta (+35.1%)** | Balanced (0) | Observed Net Hand-off Shift |
| **Workload / Agent / Month** | 25.0 tickets/mo | **28.6 tickets/mo** | 14.7 tickets/mo (Avg) | Observed Historical Roster Average |
| **Median Resolution Delay** | **1.22 hours (73 mins)** | **26.03 hours** | 2.00 hours (Company) | Observed Wait Time (Created to Resolved) |
| **Median Active Handle Time** | **0.38 hours (23 mins)** | 24.47 hours | 0.42 hours (Company) | Observed Labor Touch Time (Carrier Latency) |
| **First-Response SLA Breaches** | 13.40% (241 breaches) | **16.43% (423 breaches)**| 11.10% (1,292 breaches) | Observed SLA Penalty Liability (Policy §3) |
| **Customer Satisfaction (CSAT)**| 3.41 / 5.0 | **2.89 / 5.0 (Lowest)** | 3.38 / 5.0 (Company) | Observed Post-Resolution Survey Rating |
| **Billing to Logistics Hand-offs**| \multicolumn{2}{c}{**696 core hand-offs (795 all-time)**} | — | Observed Misrouted Intake Volume |
| **Annualized Process Waste** | \multicolumn{2}{c}{**₹1,99,853 (~₹2.00 Lakh / year)**} | — | **Hypothetical Opportunity** (Friction + SLA) |
| **Annual Cost of 2 Hires** | \multicolumn{2}{c}{**₹9,00,000 (₹4.50 Lakh / Agent)**} | Fixed Budget | Planning Parameter (Operating Policy §4) |

*Note: Billing's -627 net delta reflects total net transferred volume (761 out, 134 in), distinct from 696 gross hand-offs transferred specifically to Logistics in core 18M (795 all-time). Handled volume in Logistics (2,574) is 43.2% higher than Billing (1,798), reflecting a +35.1% net expansion over Logistics' assigned intake (1,905).*

---

### Recommended Action Plan

* **Phase 1: Immediate Process Intervention (Days 0–30 · Capital Outlay: ₹0)**  
  Reconfigure intake chatbot rules using the validated Seven-Pillar taxonomy to route delivery tracking and courier inquiries directly to Logistics, eliminating 696 misrouted hand-offs from Billing. Establish formal ticket transfer ownership tracking and institute weekly cross-departmental SLA reviews.
* **Phase 2: Conditional Logistics Capacity (Days 30–60 · Annual Planning Cost: ₹4.50 Lakh)**  
  Audit active attendance and shift availability in Logistics to verify whether existing staff can absorb direct order volume once routing friction is eliminated. If operational pressure persists, authorize **one hire dedicated to carrier escalation management** at the audited planning cost of ₹4.50 Lakh/year. Concurrently, integrate courier tracking APIs (Delhivery/BlueDart) to eliminate manual portal lookups, as headcount alone cannot resolve carrier delays.
* **Phase 3: Formal 90-Day Review & Decision (Days 60–90 · Capital Outlay: ₹0 or ₹4.50 Lakh)**  
  Evaluate measured operational metrics following Phases 1 and 2. Release the second hire to Chat Frontline only if 15-minute response SLA breaches persist; otherwise, retain the ₹4.50 Lakh allocation in corporate budget reserve.

---

### Proposed 90-Day Success Measures (Targets, Not Guaranteed Outcomes)

1. **Reduce avoidable routing hand-offs by 75%** (cutting Billing-to-Logistics transfers from ~39/month to $\le 10$/month).
2. **Improve Logistics first-response SLA compliance from 83.57% to at least 90.0%**.
3. **Compress Logistics median resolution delay from 26.03 hours to $\le 18.0$ hours** via automated courier tracking.
4. **Elevate Logistics CSAT from 2.89 to $\ge 3.25$**, closing the departmental customer sentiment gap.

---

### Financial Perspective

* **Headcount Investment vs. Process Savings:** Support headcount additions require an approved annual planning cost of **₹4,50,000 per hire** (**₹9,00,000/year for two**). Re-routing intake volume captures an estimated **₹1,99,853 annually (~₹2.00 Lakh)** in avoided transfer friction (₹1,41,520: 696 transfers × ₹305 annualized) and preventable SLA credits (₹58,333: 250 breaches × ₹350 annualized). This figure represents a **hypothetical operational cost opportunity** rather than guaranteed cash savings, and does not alter the approved salary planning cost of ₹4.50 Lakh per full-year hire.
* **Non-Conflation of Financial Exposures:** Dual-disbursement leakage (**₹3,94,616** across 74 orders) represents an **unmonitored compliance exposure** requiring ERP dispatch controls, not guaranteed recoverable revenue. Similarly, repeat-contact cost (**₹8,44,250**) is an **empirical behavioral proxy** reflecting customer return frequency within 30 days, not confirmed avoidable spend. These lines must not be added together as cumulative realized savings.

---

### Material Risks and Analytical Limitations

1. **Roster Granularity:** Workload metrics reflect historical averages across the 44-agent snapshot roster; actual shift-level attendance, leaves, and timecards were unrecorded in legacy systems.
2. **AI Classification Nature:** Predicted category labels are model-assisted classifications generated via multi-source pattern matching and confidence calibration, and are not fully human-validated ground truth.
3. **Carrier Externalities:** Logistics resolution delay (26.03 hours) is driven primarily by external courier turnaround times; headcount alone cannot resolve carrier delays without API webhook integration.

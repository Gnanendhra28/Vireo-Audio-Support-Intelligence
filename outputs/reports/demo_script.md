# EXECUTIVE VIDEO DEMONSTRATION SCRIPT (MAXIMUM 3 MINUTES)
**Project:** Vireo Audio Support Intelligence  
**Audience:** Hiring Manager & Senior Leadership (Priya Raman, Head of CX)  
**Tone:** Professional, conversational, evidence-driven, structured  
**Total Target Duration:** 2 minutes 50 seconds (with 10s buffer for a strict 3-minute cap)  
**Calibrated Word Count:** ~395 words (speaking pace: ~135 words/minute)  

---

## Visual Setup & Screen Layout
- **Browser Window:** Clean Chrome window open to `http://localhost:8501`.
- **Display Resolution:** 1440 × 900 or 1920 × 1080, sidebar expanded.
- **Audio:** Clear microphone input with system notification sounds muted.
- **Mouse Pointer:** Highlighted cursor or smooth scrolling; avoid erratic mouse movements.

---

## Timed Narration & Stage Directions

### [0:00 – 0:20] ⏱️ Section 1: The Business Problem
**Visual:** Show Streamlit Dashboard landing page on the **Executive Overview** view. Hover cursor briefly over the title and the KPI card showing *11,641 Core Period Tickets*.

> *"Hello! Today I'm presenting our support intelligence analysis for Vireo Audio, directly addressing Priya Raman’s core question: Should Vireo invest ₹9 lakh annually to add two support hires to Billing, or can targeted process improvements solve our delivery backlog? Over the next three minutes, I’ll walk through the empirical evidence across 18 months of support operations."*

---

### [0:20 – 0:50] ⏱️ Section 2: Executive Operations Overview
**Visual:** Scroll smoothly down to the Status Donut Chart, the Monthly Volume & SLA Trend chart, and highlight the peak in Q4 2025 (Diwali).

> *"Looking at the Executive Overview, across our 18-month baseline of 11,641 tickets, 86.0%—or 10,007 tickets—were resolved by agents, while 1,057 auto-closed under policy, leaving an active backlog of 577 tickets. Our overall SLA compliance sits at 88.9%, with 1,292 breaches generating ₹4.52 lakh in store credit liabilities. You can see ticket volume steadily climbed to a peak during the Diwali festive season in late 2025."*

---

### [0:50 – 1:20] ⏱️ Section 3: Category & Routing Analysis
**Visual:** Click on the sidebar and navigate to **🏷️ Category Analytics**. Scroll to the *Billing-Assigned Tickets vs. Predicted Customer Intent* chart.

> *"Navigating to Category Analytics reveals the central friction in our helpdesk. The intake bot tagged 2,425 tickets as Billing. However, our model-assisted Seven-Pillar classifier—which analyzes customer messages without looking at agent IDs—shows that over 900 of these tickets were actually delivery inquiries, where customers mentioned payments only in the context of delayed shipments. It is critical to note these are model predictions rather than human ground truth, but they explain why 696 gross hand-offs were bounced from Billing to Logistics."*

---

### [1:20 – 1:50] ⏱️ Section 4: Team Workload & Headcount Reality
**Visual:** Navigate to **👥 Team Workload**. Highlight the side-by-side comparison between Billing and Logistics.

> *"This intake distortion severely misleads staffing decisions. In the Team Workload view, Billing actually sheds a net 627 tickets, resolving inquiries in a median time of just 1.22 hours, with only 23 minutes of active handle touch time. In stark contrast, Logistics is overwhelmed: assigned 1,905 tickets, they resolved 2,574—a 35.1% net expansion. Logistics agents handle 28.6 tickets per month on a grueling 26.03-hour median resolution cycle, driving 423 SLA breaches and our lowest CSAT of 2.89."*

---

### [1:50 – 2:20] ⏱️ Section 5: Financial Reconciliation & Cost Modeling
**Visual:** Navigate to **💰 Financial Impact**. Highlight the *Audited Financial Reconciliation Summary Table*.

> *"Moving to Financial Impact, we enforce strict accounting boundaries. Inbound labor costs ₹31.82 lakh, while repeat contacts represent an estimated ₹8.44 lakh proxy. The 696 Billing-to-Logistics misroutes created ₹1.99 lakh in annualized process waste across transfer fees and SLA credits. We must be transparent: this ₹2 lakh is a hypothetical operational opportunity, not guaranteed liquid bank cash, and it cannot be conflated with the ₹3.95 lakh in unmonitored dual-disbursement compliance exposure."*

---

### [2:20 – 2:45] ⏱️ Section 6: Strategic Staffing Recommendation
**Visual:** Navigate to **⚖️ Staffing Decision**. Highlight *Scenario 3 (Conditional Hybrid)* and the *3-Phase Action Plan*.

> *"Based on this evidence, our recommendation is clear: Reject hiring for Billing—adding headcount there would create acute idle capacity. Instead, implement Phase 1 immediately by re-routing intake delivery queries directly to Logistics at zero capital cost. In Phase 2, audit Logistics shift attendance, and if capacity pressure persists, conditionally approve one hire for carrier escalations at ₹4.5 lakh. The second hire should remain on hold pending a formal 90-day review. Furthermore, carrier API integration is mandatory, because headcount alone cannot fix external courier delays."*

---

### [2:45 – 3:00] ⏱️ Section 7: Closing & 90-Day Operational Targets
**Visual:** Scroll to the *Measurable 90-Day Executive Operational Goal* banner at the bottom of the Staffing view.

> *"Within 90 days of implementing this plan, our proposed targets are to cut routing hand-offs by 75%, lift Logistics first-response SLA compliance to at least 90%, compress median resolution delay to 18 hours or less, and bring CSAT above 3.25. All code, tests, and our one-page executive memo are verified in the repository. Thank you!"*

---

## Presenter Rehearsal Checklist
1. **Pacing Check:** Read aloud with a stopwatch. Target timing is 2:45 to 2:55. If you exceed 2:55, speak slightly more briskly on Section 2.
2. **Screen Transitions:** Practice clicking through the 5 sidebar views (`Executive Overview` $\rightarrow$ `Category Analytics` $\rightarrow$ `Team Workload` $\rightarrow$ `Financial Impact` $\rightarrow$ `Staffing Decision`) smoothly.
3. **Pronunciation:**
   - Priya Raman (*Pree-yah Rah-mun*)
   - Arjun Mehta (*Ar-joon Meh-tah*)
   - CSAT (*See-sat*)
   - SLA (*S-L-A*)

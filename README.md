# Vireo Audio Support Intelligence

AI-assisted support ticket classification, capacity planning, and business operations analytics for **Vireo Audio Pvt. Ltd.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](#-technology-stack)
[![Streamlit App](https://img.shields.io/badge/Streamlit-8%20Interactive%20Views-FF4B4B.svg)](#-dashboard-walkthrough-8-views)
[![Tests Passing](https://img.shields.io/badge/Tests-120%2F120%20Passing-brightgreen.svg)](#-automated-testing-suite)

---

## ⚡ 30-Second Quick Start

```bash
# 1. Navigate to the project root
cd vireo-support-intelligence

# 2. Create and activate a clean virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Windows (PowerShell): .venv\Scripts\Activate.ps1
                                # Windows (CMD):        .venv\Scripts\activate.bat

# 3. Install dependencies from requirements.txt
pip install -r requirements.txt

# 4. Run the 120-test automated verification suite
pytest tests/ -v

# 5. Launch the Streamlit dashboard (8 views)
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 📌 Executive Summary & Business Case

Vireo Audio Support Intelligence analyzes **18 months of customer support records** (1 Jan 2025 – 30 Jun 2026; **11,641 core tickets**) across 4 omnichannel touchpoints (Chat, Email, Voice Callback, Social) to resolve an executive leadership deadlock over a **₹9,00,000 annual headcount budget** (two support hires at ₹4.5L/agent).

### The ₹9 Lakh Hiring Deadlock

| Stakeholder | Initial Stance | Empirical Data Finding | Verdict |
| :--- | :--- | :--- | :---: |
| **Priya Raman**<br>*(Head of CX)* | Award **both hires to Billing**, citing intake volume (2,564 tickets, 21.8% of inbound). | **Intake volume is artificial.** 100% of tickets tagged `Billing & Payments` were dumped into Billing, but **795 tickets (31.0%)** were re-handled and resolved by Logistics. Billing median resolution time is only **1.23 hours**. | ❌ **Rejected**<br>(Overstaffing low-handle-time queue) |
| **Neha Kulkarni**<br>*(Support Ops)* | Contends **Logistics is drowning** with multi-day resolution delays and collapsing customer satisfaction. | **Validated.** Logistics handles **2,574 resolved tickets** (+43% higher than Billing), has a **26.08-hour median resolution time**, accounts for **458 SLA breaches (17.13%)**, and has the lowest CSAT in the company (**2.87 / 5.0**). | ✅ **Validated**<br>(Logistics is the acute bottleneck) |
| **Arjun Mehta**<br>*(Finance Controller)* | Demands an ironclad financial case before authorizing ₹9L payroll, asking if **process fixes** can solve the issue. | **Process fixes yield ₹1,99,853** in annual transfer waste reduction. However, process fixes alone cannot absorb carrier turnaround delays without targeted staffing. | ✅ **Addressed**<br>(Combined process + targeted hire ROI) |

### Strategic Recommendation
1. **Reject Hiring for Billing:** Billing is adequately staffed (4 agents, 1.23h resolution time). Adding headcount to Billing wastes capital.
2. **Execute Intake Routing Fixes:** Re-tune chatbot intake classification to eliminate 795 misrouted tickets, saving **₹1,99,853** in preventable internal transfer penalties (₹305/transfer).
3. **Targeted Headcount Allocation:** Allocate **1 agent to Logistics** (reducing resolution delay to ~14.8h and slashing SLA credits) and **1 agent to Frontline Chat** to protect 15-minute response targets during festive peaks.

---

## 🛠️ Technology Stack

- **Runtime:** Python **3.11, 3.12, 3.13, and 3.14** (standard CPython, fully cross-platform)
- **Application Framework:** [Streamlit](https://streamlit.io/) (>= 1.32.0)
- **Data Engineering:** [Pandas](https://pandas.pydata.org/) (>= 2.2.0), [NumPy](https://numpy.org/) (>= 1.26.0)
- **Interactive Visualizations:** [Plotly](https://plotly.com/) (>= 5.20.0)
- **Schema Contracts & Data Models:** [Pydantic](https://docs.pydantic.dev/) (>= 2.6.0)
- **Document & PDF Processing:** [PyMuPDF](https://pymupdf.readthedocs.io/) (`pymupdf` >= 1.24.0)
- **Automated Testing Suite:** [Pytest](https://pytest.org/) (>= 8.0.0)
---

## 📁 Project Architecture & Directory Structure

```text
vireo-support-intelligence/
├── app.py                          # Main Streamlit dashboard application (8 views)
├── requirements.txt                # Pinned production Python dependencies
├── .env.example                    # Optional environment configuration template
├── .gitignore                      # Git exclusion rules
├── README.md                       # Project documentation & evaluation guide
├── PRIVACY_AND_ASSUMPTIONS.md      # Governing data hygiene & privacy rules
│
├── .streamlit/
│   └── config.toml                 # Streamlit headless & telemetry configuration
│
├── data/
│   ├── raw/                        # Preserved source datasets & documents (read-only)
│   │   ├── tickets.csv             # 11,780 support ticket records (11,641 core 18m)
│   │   ├── orders.csv              # 15,000 order transactions
│   │   ├── agents.csv              # 44 support agent roster profiles
│   │   ├── products.csv            # 14 product catalog SKUs & pricing
│   │   ├── customers.csv           # 9,500 customer records
│   │   ├── support-policy.pdf      # Customer Support Operating Policy v3.2
│   │   ├── email-thread.txt        # Executive email debate (Priya / Arjun / Neha)
│   │   └── README.txt              # Original assignment dataset manifest
│   │
│   └── processed/                  # Enriched & normalized analytics tables
│       ├── classified_tickets.csv  # 11,780 tickets enriched with 7-pillar predictions
│       └── human_validation_sample.csv # 98-ticket stratified audit sample
│
├── src/
│   ├── __init__.py
│   ├── data/                       # Ingestion, validation, preprocessing & dynamic CSV
│   │   ├── loader.py               # Pathlib-based safe dataset loader
│   │   ├── validation.py           # Integrity, timestamp & PII validation
│   │   ├── preprocessing.py        # Timezone fixes (+5h30m), metric enrichment & joins
│   │   ├── schema_contract.py      # Canonical schema contracts & field definitions
│   │   ├── column_mapper.py        # Deterministic & fuzzy column name mapper
│   │   ├── dynamic_validator.py    # In-memory uploaded CSV structural validator
│   │   └── dynamic_pipeline.py     # Dynamic analytics pipeline & compatibility engine
│   │
│   ├── classification/             # Seven-Pillar intent classification engine
│   │   ├── taxonomy.py             # MECE 7-Pillar taxonomy configuration
│   │   ├── rules.py                # Deterministic pattern matching engine
│   │   ├── confidence.py           # Multi-factor confidence scoring & review flags
│   │   └── classifier.py           # Master classification orchestrator
│   │
│   ├── analytics/                  # Capacity, SLA, and financial KPIs
│   │   ├── monthly.py              # Month-by-month KPI aggregations & status counts
│   │   ├── workload.py             # Assigned vs resolved capacity & tier demarcation
│   │   ├── sla.py                  # Policy §3 channel-specific SLA breach auditor
│   │   ├── financial.py            # Cost modeling, transfer waste & policy violations
│   │   └── staffing.py             # Hiring evaluation & 90-day goal engine
│   │
│   ├── agent/                      # Controlled Human-in-the-Loop Triage Agent
│   │   ├── schemas.py              # Pydantic request, response, and trace models
│   │   └── triage_agent.py         # 10-stage deterministic advisory triage agent
│   │
│   ├── evaluation/                 # Model evaluation metrics & confusion matrices
│   │   └── metrics.py              # Classification metrics calculation
│   │
│   └── ui/                         # Modular Streamlit views and components
│       ├── data_service.py         # Data caching, filtering & formatting
│       ├── executive.py            # View 1: Executive Overview
│       ├── categories.py           # View 2: Seven-Pillar Category Analytics
│       ├── workload.py             # View 3: Team Workload & Tier Demarcation
│       ├── staffing.py             # View 4: Staffing Decision Engine & Scenarios
│       ├── financial.py            # View 5: Financial Impact & Policy Compliance
│       ├── audit_view.py           # View 6: Master Audit Reconciliation
│       ├── triage_view.py          # View 7: Support Triage Agent Interface
│       └── upload_view.py          # View 8: Dynamic CSV Upload Workspace
│
├── tests/                          # Automated test suite (120 tests, 100% passing)
│   ├── test_data_loader.py         # Ingestion, validation & PII masking tests (6)
│   ├── test_classification.py      # 7-Pillar classification & rules tests (15)
│   ├── test_analytics.py           # Monthly, workload, SLA & financial tests (12)
│   ├── test_dashboard.py           # UI filtering, data caching & formatting tests (6)
│   ├── test_triage_agent.py        # 10-stage agent logic & security tests (24)
│   ├── test_triage_view.py         # Triage UI components & state simulation tests (6)
│   ├── test_dynamic_ingestion.py   # Schema contract, mapping & validator tests (15)
│   ├── test_dynamic_pipeline.py    # Dynamic pipeline execution & safety tests (15)
│   ├── test_upload_view.py         # Upload workspace rendering & state tests (11)
│   └── test_upload_navigation.py   # Full 8-view navigation integration tests (10)
│
└── outputs/
    ├── screenshots/                # Rendered executive dashboard screenshots
    └── reports/                    # Certified audit deliverables & reports
        ├── business_requirements.md # Analytical blueprint & requirement mappings
        ├── executive_memo.md       # 1-page executive memorandum for Priya Raman
        ├── executive_memo.pdf      # Single-page PDF memorandum (PyMuPDF verified)
        ├── metric_reconciliation.md # Authoritative cross-module reconciliation table
        ├── staffing_analysis.md    # Evidence-based capacity & hiring report
        ├── financial_impact.md     # Financial modeling & policy audit
        ├── data_discovery_report.md # Initial forensic dataset analysis
        ├── demo_script.md          # 3-minute timed executive walkthrough script
        └── recording_checklist.md  # Video recording protocol
```

---

## 🖥️ Dashboard Walkthrough (8 Views)

| # | Navigation View | Primary Function & Strategic Insight |
| :-: | :--- | :--- |
| **1** | **📊 Executive Overview** | High-level metrics, 18-month volume trends, Diwali peak analysis (Oct 2025 spike of 998 tickets), and strict status accounting donut (**10,007 resolved**, **1,057 closed**, **577 active backlog**). |
| **2** | **🏷️ Category Analytics** | Seven-Pillar intent distribution, intake bot misclassification matrix (identifying 795 misrouted tickets), and confidence review flag distributions (33.67% review rate). |
| **3** | **👥 Team Workload** | Headcount, monthly tickets per agent, resolution delay benchmarks, and Tier 1 frontline vs. Tier 2 hardware escalation separation. |
| **4** | **⚖️ Staffing Decision** | Head-to-head empirical comparison (Billing vs. Logistics), 4 strategic headcount scenarios, 3-phase action plan, and 90-day targets. |
| **5** | **💰 Financial Impact** | Inbound channel costs (**₹31.82L**), SLA breach store credit liabilities (**₹4.52L / ₹4.69L**), internal transfer penalty waste (**₹3.96L total**, **₹1,99,853 preventable**), repeat-contact friction (**₹8.44L**), and dual disbursement compliance leakage (**~₹3.36L across 74 orders**). |
| **6** | **🔍 Master Audit Reconciliation** | Interactive verification of the authoritative reconciliation table ensuring 100% mathematical consistency across views and reports. |
| **7** | **🤖 Support Triage Agent** | Interactive human-in-the-loop triage interface with structured 10-stage reasoning, policy compliance warnings, PII sanitization, prompt injection defense, and supervisor override simulation. |
| **8** | **📁 Dynamic CSV Upload Workspace** | In-memory upload workspace allowing users to upload arbitrary support CSVs, inspect fuzzy column mappings, validate schema contracts, and generate dynamic KPI analytics without modifying baseline files. |

---

## 🧪 Automated Testing Suite

The project includes **120 automated unit and integration tests** providing complete coverage across data contracts, preprocessing, classification rules, financial formulas, agent safety, and dashboard rendering.

### Running Tests
```bash
pytest tests/ -v
```

### Test Suite Structure (10 Modules)
- `tests/test_data_loader.py` (6 tests): Referential integrity, Freshdesk UTC-to-IST (+5h30m) timestamp normalization, and PII masking.
- `tests/test_classification.py` (15 tests): Seven-Pillar intent taxonomy, keyword boundaries, confidence calibration, and target leakage prevention.
- `tests/test_analytics.py` (12 tests): Monthly KPI aggregations, workload modeling, Policy §3 SLA breaches, and financial penalty calculations.
- `tests/test_dashboard.py` (6 tests): UI filtering, caching decorators, and responsive Plotly chart formatting.
- `tests/test_triage_agent.py` (24 tests): 10-stage agent pipeline, prompt injection defense, policy violations, repeat contacts, and PII sanitization.
- `tests/test_triage_view.py` (6 tests): Triage Streamlit interface, supervisor review buttons, and session state immutability.
- `tests/test_dynamic_ingestion.py` (15 tests): Canonical schema contracts, fuzzy column mapping, collision detection, and null-safety.
- `tests/test_dynamic_pipeline.py` (15 tests): Dynamic capability matrix, tier resolution, missing metric preservation, and baseline isolation.
- `tests/test_upload_view.py` (11 tests): Upload workspace UI, CSV parsing, mapping inspector, and dynamic report rendering.
- `tests/test_upload_navigation.py` (10 tests): Full 8-view navigation integration, dispatcher routing, and zero baseline filesystem writes.

---

## 📊 Summary of Audited Baseline Findings

1. **Intake Bot Distortion:**
   - 100% of tickets tagged `Billing & Payments` (2,564) were assigned to the Billing queue.
   - However, **795 tickets (31.0%)** assigned to Billing were re-handled and resolved by **Logistics**.
2. **Workload Inversion:**
   - **Billing Resolved:** 1,798 tickets.
   - **Logistics Resolved:** 2,574 tickets (+43% higher volume than Billing).
3. **Logistics Operational Distress:**
   - Median resolution time is **26.08 hours** (vs. 1.23h for Billing).
   - Highest SLA breach rate (**17.13%**, 458 breaches under Policy §3).
   - Lowest customer satisfaction in the company (**2.87 / 5.0**).
4. **Legacy Timestamp Inversion (Resolved):**
   - 2,575 Freshdesk tickets exhibited negative handle times due to event log reconstruction in UTC.
   - Applying a `+05:30:00` offset to legacy resolution timestamps eliminates 100% of negative times.
5. **Policy Violation (Dual Disbursements):**
   - 74 unique orders received **both a cash refund and a replacement unit**, violating Operating Policy §5 (~₹3.36L exposure).

---

## ⚠️ Known Assumptions & Analytical Boundaries

1. **Agent Roster Snapshot:** `agents.csv` reflects static team and site rosters rather than dynamic historical join/leave dates, hourly shift rotations, or sick leaves.
2. **Model-Assisted Intent:** Predicted category labels are generated via deterministic pattern matching with calibrated confidence scores, rather than human ground truth.
3. **Carrier Logistics Dependency:** Logistics resolution delay (26.08 hours) is largely driven by third-party carrier transit times; internal staffing alone cannot fix courier turnaround without webhook tracking.
4. **Repeat Contact Behavioral Proxy:** Repeat contacts within 30 days capture customer re-inquiry frequency using `customer_id`, rather than helpdesk ticket re-open threads.
5. **Read-Only Advisory Scope:** The Support Triage Agent and Dynamic CSV Workspace are designed as local supervisory evaluation interfaces, not live production CRM connectors.

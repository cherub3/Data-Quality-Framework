# Resume Assets — Enterprise Data Quality & Governance Framework

## Resume Project Title

**Enterprise Data Quality & Governance Framework** | Python, DuckDB, SQL, Streamlit, Plotly

---

## Resume Bullet Points

Choose 4–6 of the following based on the role you are applying for.

### For Data Governance / Data Quality Roles

- Designed and implemented an **eight-layer data governance framework** covering data inventory,
  control rulebook, automated testing, exception detection, early-warning watchlisting, remediation
  workflow, governance reporting, and monthly board review — modelled on banking governance standards

- Built a **Data Quality Watchlist** that monitors three trend signals (null rate, duplicate rate,
  control failure rate) across 13 datasets and identifies deteriorating datasets 5–10 days before
  traditional control failures occur

- Engineered a **Data Trust Score (0–100)** per business domain and at enterprise level, enabling
  non-technical stakeholders to assess data health at a glance; thresholds: Trusted (90+), Monitor
  (75–89), At Risk (<75)

- Defined **30 governance controls** across Completeness, Accuracy, Consistency, and Timeliness
  dimensions with thresholds and severity ratings; executed daily across all datasets with 30-day
  history stored in DuckDB

- Implemented a **remediation workflow** tracking exceptions from detection to verified resolution
  across five statuses (Open → Assigned → In Progress → Escalated → Resolved) with SLA enforcement
  and root cause classification (Source System, ETL, Manual Entry, Mapping, Feed Delay)

### For Business Analyst / Data Analyst Roles

- Produced an **auto-generated Monthly Governance Review** structured as a board-level narrative
  covering: What Happened, Why It Happened, Business Risk Assessment, Recommended Actions, and
  Expected Impact — mapped to regulatory, audit, and reporting stakeholder needs

- Developed a **Governance Maturity Model** (Initial → Developing → Managed → Optimized) scored
  against four dimensions: Control Coverage, Automation %, SLA Compliance, and Audit Completeness

- Built a **five-page Streamlit governance dashboard** used by four stakeholder personas (CDO, CRO,
  Data Stewards, Internal Audit) with role-appropriate KPIs, heatmaps, trend charts, and
  remediation trackers

### For Risk / Compliance Roles

- Implemented **regulatory criticality tiering** across 13 datasets (High / Medium / Low) with
  exception auto-escalation for any control failure on Regulatory Critical datasets (Transaction
  Ledger, Risk Exposure, General Ledger, Customer Master)

- Designed a **control framework with audit trail** — every control test is timestamped, pass/fail
  classified, and stored for 30 days, providing auditable evidence of governance control execution

---

## LinkedIn Project Description

**Enterprise Data Quality & Governance Framework**

Built a complete data governance framework in Python, DuckDB, SQL, and Streamlit that goes beyond
standard quality checking to implement the full governance lifecycle: Detect → Assess → Prioritize
→ Remediate → Govern → Improve.

Key features:
• Data Inventory (13 datasets, 4 criticality tiers) with named owners and stewards
• Control Rulebook (30 controls across Completeness, Accuracy, Consistency, Timeliness)
• Automated daily control testing with 30-day history
• Exception detection with severity classification and escalation recommendations
• Data Quality Watchlist — early-warning system catching deterioration 5–10 days before failure
• Remediation workflow with SLA tracking and root cause classification
• Data Trust Score (0–100) per domain and enterprise level
• Governance Maturity Model (Initial → Optimized)
• Auto-generated Monthly Governance Review for board distribution
• 5-page Streamlit dashboard for CDO, CRO, Data Stewards, and Internal Audit

Built to demonstrate banking-grade data governance thinking at a portfolio level.

#DataGovernance #DataQuality #BusinessAnalysis #Python #SQL #Streamlit #DataEngineering #Banking

---

## GitHub Repository Description

Enterprise Data Quality & Governance Framework — 8-layer banking data governance system with
Data Trust Scoring, DQ Watchlist early-warning, 30-control rulebook, remediation workflow,
Governance Maturity Model, and 5-page Streamlit executive dashboard. Python | DuckDB | SQL |
Streamlit | Plotly.

---

## Portfolio Narrative (For Interview Opening)

"My portfolio covers three interconnected risk domains in banking.

Project 1 addresses Customer Risk — I built a customer intelligence and portfolio risk management
platform that identifies which customers pose credit and behavioural risk.

Project 2 addresses Fraud and Operational Risk — I built a fraud detection platform that identifies
anomalous transactions and automates the operational response workflow.

Project 3 — this project — addresses Data Risk and Governance. Because if the underlying data
feeding the risk models in Projects 1 and 2 is poor quality, the models produce unreliable outputs.
This framework governs the data itself: it monitors quality, detects deterioration early, enforces
controls, tracks remediation, and delivers a Data Trust Score that tells executives whether they
can trust the data their decisions are based on.

Together, the three projects demonstrate a risk mindset: customer risk, transaction risk, and
data risk. That is the full picture of what a modern bank's data function needs to manage."

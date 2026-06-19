# Enterprise Data Quality & Governance Framework

> A complete eight-layer banking data governance framework that moves beyond simple validation
> to implement the full lifecycle: **Detect → Assess → Prioritize → Remediate → Govern → Improve**

---

## What This Is

Most data quality projects detect problems and stop. This framework governs data — the way a bank
or regulated financial institution is expected to.

It monitors **13 datasets** across four criticality tiers, executes **30 governance controls** daily,
runs an **early-warning watchlist** to catch deterioration before it reaches reporting, tracks every
issue through a **remediation workflow** with SLA enforcement, and delivers an executive
**Data Trust Score (0–100)** alongside a **Governance Maturity assessment**.

---

## Portfolio Context

| Project | Domain | Focus |
|---|---|---|
| Project 1 — Customer Intelligence Platform | Customer Risk | Who poses credit and behavioural risk |
| Project 2 — Fraud Detection & Risk Operations | Fraud & Operational Risk | Anomalous transactions and operational response |
| **Project 3 — This Project** | **Data Risk & Governance** | **Governing the data that feeds everything else** |

---

## Eight Governance Layers

| Layer | Name | What It Does |
|---|---|---|
| 1 | Data Inventory | Registers 13 datasets with owners, stewards, source systems, and regulatory criticality |
| 2 | Control Rulebook | Defines 30 controls across Completeness, Accuracy, Consistency, Timeliness |
| 3 | Control Testing | Executes all controls daily — 30-day history, pass/fail classification |
| 4 | Exception Detection | Flags critical failures, repeated failures, regulatory critical issues |
| 5 | Data Quality Watchlist | Three-signal early-warning system (null rate, duplicate rate, failure rate) |
| 6 | Remediation Workflow | Tracks issues from detection to verified resolution with SLA enforcement |
| 7 | Governance Reporting | Data Trust Score (0–100) and Governance Maturity (Initial → Optimized) |
| 8 | Monthly Governance Review | Auto-generated board-level narrative: What, Why, Risk, Actions, Impact |

---

## Dashboard (5 Pages)

| Page | Name | Audience |
|---|---|---|
| 1 | Executive Governance Overview | CDO, Board |
| 2 | Data Quality Watchlist | Governance Office, Data Stewards |
| 3 | Control Testing | Data Engineers, Data Stewards |
| 4 | Issue & Remediation Management | Governance Office, Operations |
| 5 | Monthly Governance Review | CDO, Internal Audit, Regulators |

---

## Tech Stack

- **Python** — Pipeline, data generation, governance computation
- **Pandas** — Data manipulation
- **DuckDB** — In-process SQL warehouse (8 tables)
- **SQL** — All analytical queries for dashboard and reporting
- **Streamlit** — Interactive 5-page governance dashboard
- **Plotly** — Charts, gauges, heatmaps

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the pipeline

```bash
python src/pipeline.py
```

This generates all synthetic governance data and populates the DuckDB warehouse.

### 3. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard is available at `http://localhost:8501`.

---

## Project Structure

```
├── src/
│   └── pipeline.py           # Master ETL pipeline (all 8 layers)
├── dashboard/
│   └── app.py                # Streamlit 5-page dashboard
├── data/
│   └── warehouse/
│       └── governance.duckdb # DuckDB database (8 tables)
├── docs/
│   ├── BUSINESS_PROBLEM.md
│   ├── ARCHITECTURE.md
│   ├── EXECUTIVE_SUMMARY.md
│   ├── KEY_FINDINGS.md
│   ├── MONTHLY_GOVERNANCE_REVIEW.md
│   ├── INTERVIEW_NOTES.md
│   └── RESUME_ASSETS.md
├── requirements.txt
└── README.md
```

---

## Database Schema (8 Tables)

| Table | Purpose |
|---|---|
| `data_inventory` | 13 datasets with ownership and criticality metadata |
| `control_rulebook` | 30 governance controls with thresholds and severity |
| `control_test_results` | 30-day daily test history (~1,200+ rows) |
| `exceptions` | Auto-detected critical failures and regulatory issues |
| `dq_watchlist` | Early-warning dataset monitoring with trend classification |
| `remediation_tickets` | Issue lifecycle tracking with SLA and root cause |
| `domain_trust_scores` | Data Trust Score per domain and enterprise-wide |
| `governance_maturity` | Maturity assessment across four dimensions |

---

## Key Design Choices

**Why a Data Quality Watchlist?**
Standard control testing catches failures after they occur. The Watchlist monitors three trend
signals over a rolling window — null rate, duplicate rate, and control failure rate — to detect
deterioration 5–10 days before a control fails. This mirrors how governance teams in banks operate:
they want early signals, not post-failure alerts.

**Why a Data Trust Score?**
A Chief Data Officer does not need to read 30 control results. They need one number. The Data Trust
Score aggregates control effectiveness, watchlist status, and exception severity into a 0–100 score
with three categories (Trusted / Monitor / At Risk), giving non-technical executives a clear signal.

**Why DuckDB?**
DuckDB is SQL-compliant, requires no server, handles analytical workloads efficiently, and keeps
the project fully self-contained. All SQL patterns used here translate directly to Snowflake,
BigQuery, or Databricks in a production environment.

---

## Documentation

| Document | Purpose |
|---|---|
| [BUSINESS_PROBLEM.md](docs/BUSINESS_PROBLEM.md) | Problem statement, stakeholder map, business value |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, database schema, layer descriptions |
| [EXECUTIVE_SUMMARY.md](docs/EXECUTIVE_SUMMARY.md) | One-page project summary |
| [KEY_FINDINGS.md](docs/KEY_FINDINGS.md) | Five governance findings with risk and recommendations |
| [MONTHLY_GOVERNANCE_REVIEW.md](docs/MONTHLY_GOVERNANCE_REVIEW.md) | Sample board governance report |
| [INTERVIEW_NOTES.md](docs/INTERVIEW_NOTES.md) | Layer-by-layer interview answers and 30-second explanations |
| [RESUME_ASSETS.md](docs/RESUME_ASSETS.md) | CV bullets, LinkedIn description, portfolio narrative |

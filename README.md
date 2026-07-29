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

> **Note:** this repo also contains an earlier, separate subsystem (`run_pipeline.py`, `src/checks.py`, `src/scorer.py`, `warehouse/dq_warehouse.duckdb`) that runs event-level QA checks against a different sample dataset. It is unrelated to the governance framework above — always use `python src/pipeline.py` (not the root-level `run_pipeline.py`) to run this project.

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
│   ├── RESUME_ASSETS.md
│   └── DISCOVERY_NARRATIVE.md          # Improvement 1
├── sql/
│   └── v2_rebuild/                     # Improvement 4 — SQL rewritten from first principles
│       ├── 01_control_test_execution.sql
│       ├── 02_dq_watchlist_signals.sql
│       ├── 03_data_trust_score.sql
│       ├── 04_remediation_sla_tracking.sql
│       └── SQL_COMPARISON.md
├── dashboard/
│   ├── app.py                          # Streamlit 5-page dashboard
│   ├── data/                           # CSV exports for the Power BI build
│   ├── DASHBOARD_BUILD_GUIDE.md        # Improvement 5
│   └── dashboard_preview.html          # Improvement 5
├── GOVERNANCE_RECOMMENDATION_MEMO.md   # Improvement 2
├── RESUME_BULLET.md                    # Improvement 2
├── INTERVIEW_PREP_OBJECTIONS.md        # Improvement 3
├── requirements.txt
└── README.md
```

---

## Database Schema (8 Tables)

| Table | Purpose |
|---|---|
| `data_inventory` | 13 datasets with ownership and criticality metadata |
| `control_rulebook` | 30 governance controls with thresholds and severity |
| `control_test_results` | 30-day daily test history (1,350 rows) |
| `exceptions` | Auto-detected critical failures and regulatory issues |
| `dq_watchlist` | Early-warning dataset monitoring with trend classification |
| `remediation_tickets` | Issue lifecycle tracking with SLA and root cause |
| `domain_trust_scores` | Data Trust Score per domain and enterprise-wide |
| `governance_maturity` | Maturity assessment across four dimensions |

---

## Key Design Choices

**Why a Data Quality Watchlist?**
Standard control testing catches failures after they occur. The Watchlist monitors three trend
signals over a rolling window — null rate, duplicate rate, and control failure rate — designed to
surface deterioration before it reaches a hard control failure. This mirrors how governance teams
in banks operate: they want early signals, not post-failure alerts. The specific lead time this
buys is a design intent, not a backtested number — `dq_watchlist` stores a point-in-time snapshot
rather than dated daily history, so a claim like "N days early" can't be verified against this
warehouse's data. See [`docs/DISCOVERY_NARRATIVE.md`](docs/DISCOVERY_NARRATIVE.md) and
[`INTERVIEW_PREP_OBJECTIONS.md`](INTERVIEW_PREP_OBJECTIONS.md) Q6 for what the data does and
doesn't support.

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

---

## Interview & Governance Deep-Dive

This project includes five hardening deliverables prepared for senior-level interviews:

1. **Discovery Narrative** ([docs/DISCOVERY_NARRATIVE.md](docs/DISCOVERY_NARRATIVE.md)) — the exploration journey from naive null/duplicate detection to the full 8-layer governance framework, grounded in real pipeline output.
2. **Governance Recommendation Memo** ([GOVERNANCE_RECOMMENDATION_MEMO.md](GOVERNANCE_RECOMMENDATION_MEMO.md)) — business-impact case for the framework, plus a resume bullet ([RESUME_BULLET.md](RESUME_BULLET.md)) drawn from it.
3. **Objection Prep** ([INTERVIEW_PREP_OBJECTIONS.md](INTERVIEW_PREP_OBJECTIONS.md)) — 15 anticipated hard questions with data-backed, honestly-scoped answers (including named limitations).
4. **SQL v2 Rebuild** ([sql/v2_rebuild/](sql/v2_rebuild/)) — governance logic rewritten from first principles in pure SQL and reconciled against the production pipeline's output ([SQL_COMPARISON.md](sql/v2_rebuild/SQL_COMPARISON.md)).
5. **Dashboard Build Guide** ([dashboard/DASHBOARD_BUILD_GUIDE.md](dashboard/DASHBOARD_BUILD_GUIDE.md), [dashboard/dashboard_preview.html](dashboard/dashboard_preview.html)) — a Power BI build spec plus a static HTML preview.

All figures cited in these documents are pulled live from `data/warehouse/governance.duckdb` and are illustrative/synthetic — they describe a simulated banking environment, not a real one. The pipeline is seeded, so the figures reproduce exactly on re-run (only absolute dates slide forward). See [project_metrics.md](project_metrics.md) for the single source of truth on every headline number, the tested reproducibility breakdown, and the project's known limitations.

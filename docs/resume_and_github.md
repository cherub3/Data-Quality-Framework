# Resume Bullets & GitHub Packaging

---

## Resume Bullets

### Version A — 2 Bullets (tight resume, limited space)

```
• Built an Automated Data Quality Monitoring Framework in Python that validates
  2.75M+ ecommerce event records across 16 rules and 6 quality dimensions, scoring
  datasets 0–100 and surfacing results through a Streamlit dashboard backed by DuckDB.

• Detected real-world data quality issues in the Retail Rocket dataset including
  67 duplicate transaction IDs and 18,430 orphaned product references (9.2% of records)
  that would have silently corrupted revenue and category-level analytics.
```

---

### Version B — 4 Bullets (projects section with more space)

```
• Designed and implemented an end-to-end Data Quality Monitoring Framework in Python
  (Pandas, DuckDB, Streamlit) that validates 2.75M+ ecommerce event records across
  6 quality dimensions: Completeness, Uniqueness, Validity, Consistency, Freshness,
  and Referential Integrity.

• Engineered 16 automated validation checks with a weighted scoring engine (0–100)
  and severity-based classification (Critical / High / Medium / Low); implemented a
  Critical Override that prevents datasets with broken user attribution from being
  rated as trustworthy regardless of aggregate score.

• Detected real data quality issues in the Retail Rocket dataset prior to any synthetic
  injection: 67 duplicate transaction IDs, 18,430 orphaned product references (9.2%),
  and 132 referential integrity failures — demonstrating the framework's real-world
  validation value.

• Built a 4-page Streamlit monitoring dashboard reading from a DuckDB warehouse
  (3 tables, 14 historical runs) showing quality score trends, severity breakdowns,
  per-check validation results, and freshness/gap detection with business-plain
  recommendations.
```

---

### Version C — ATS-Optimised

*(For Applicant Tracking Systems — keyword density, no special formatting)*

```
Data Quality Engineer / Analytics Engineer — Portfolio Project

Automated Data Quality Monitoring Framework | Python, Pandas, DuckDB, Streamlit, SQL

• Developed automated data quality pipeline validating 2,756,101 ecommerce event records
  from the Retail Rocket dataset using Python, Pandas, and DuckDB.
• Implemented 16 data validation rules across 6 quality dimensions: completeness,
  uniqueness, validity, consistency, freshness, and referential integrity.
• Designed weighted quality scoring system (0–100) with severity classification
  (Critical, High, Medium, Low) and business-rule override logic.
• Identified real-world data quality issues: 67 duplicate transaction IDs, 18,430
  orphaned item references (9.2% of dataset), and 132 referential integrity failures
  in raw data prior to synthetic testing.
• Built ETL pipeline producing structured validation output stored in DuckDB warehouse
  (dq_run_log, dq_results, dq_summary tables) across 14 historical pipeline runs.
• Developed 4-page Streamlit dashboard displaying quality score trends, dimension
  breakdowns, freshness monitoring, and severity-ranked issue tracking.
• Created four data quality tiers (clean, light, moderate, severe) with controlled
  corruption injection demonstrating score progression from 55.6 to 95.4.
• Generated human-readable validation reports with ranked business impact analysis,
  actionable recommendations, and data-trust verdicts for stakeholder communication.

Technologies: Python, Pandas, DuckDB, Streamlit, Plotly, SQL, Git
```

---

## GitHub Repository

### One-Line Description (GitHub repo tagline)

```
Automated data quality framework that validates 2.75M+ ecommerce events across
16 checks and 6 dimensions — with real findings from the Retail Rocket dataset.
```

### LinkedIn-Style Description (for LinkedIn Projects section)

```
Built an end-to-end Automated Data Quality Monitoring Framework on the Retail Rocket
ecommerce dataset (2.75M+ events). The framework runs 16 validation checks across
6 quality dimensions, scores datasets 0–100, and surfaces results through a Streamlit
dashboard.

Before introducing any synthetic issues, the framework detected real data quality
problems in the raw dataset: 67 duplicate transaction IDs, 18,430 orphaned product
references (9.2% of records), and 132 referential integrity failures — issues that
would silently corrupt revenue reporting and category-level analytics.

Key technical components:
• Python quality engine with standardised check contract (Pandas + DuckDB)
• Weighted scoring model with severity classification and critical-failure override
• DuckDB warehouse storing 14 historical pipeline runs and 224 check results
• 4-page Streamlit monitoring dashboard with score trends and freshness detection
• Four corruption tiers demonstrating score progression from 55.6 to 95.4
• Plain-text validation reports with business impact analysis and recommendations

Stack: Python | Pandas | DuckDB | Streamlit | Plotly | SQL | Git
```

### Full Repository About Description

```
Automated Data Quality Monitoring Framework for ecommerce event data.

Validates the Retail Rocket dataset (2.75M+ events) across 16 rules and 6 quality
dimensions (Completeness, Uniqueness, Validity, Consistency, Freshness, Referential
Integrity). Produces a scored quality report, writes results to a DuckDB warehouse,
and surfaces a 4-page Streamlit monitoring dashboard.

Detected real issues in raw data: 67 duplicate transaction IDs, 18,430 orphaned
product references (9.2%), and 132 referential integrity failures.

Stack: Python · Pandas · DuckDB · Streamlit · Plotly · SQL
```

### GitHub Topics / Tags

```
data-quality
data-engineering
python
pandas
duckdb
streamlit
sql
etl
data-validation
data-monitoring
analytics-engineering
ecommerce
retail
data-pipeline
portfolio-project
```

---

## Architecture Diagrams

### Simple (README / Recruiter)

```
┌─────────────────────────────────────────┐
│         RETAIL ROCKET DATASET           │
│  events.csv  │  item_properties  │  cat │
└──────────────────────┬──────────────────┘
                       │
               [ INGESTION ]
               ingestion.py
               Sample: 200k rows
                       │
               [ QUALITY ENGINE ]
               checks.py
               16 checks │ 6 dimensions
                       │
               [ SCORING ENGINE ]
               scorer.py
               0–100 score │ status
                       │
          ┌────────────┴────────────┐
          │                         │
  [ WAREHOUSE ]              [ REPORTER ]
  DuckDB                     Plain-text
  3 tables                   .txt report
  14 runs                         │
          │                         │
          └────────────┬────────────┘
                       │
              [ DASHBOARD ]
              Streamlit
              4 pages
```

### Detailed (Interview / Technical Discussion)

```
INPUT LAYER
───────────────────────────────────────────────────
events.csv (2.75M rows)  item_properties x2  category_tree.csv
      │                        │                    │
      └──────────────────────┬─┘                    │
                        ingestion.py                │
                   (load / sample / merge)          │
                             │                      │
                      df_events             df_categories
                      df_items ─────────────────────┘

CHECK LAYER
───────────────────────────────────────────────────
                      checks.py
    ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
    │COMPLETE  │UNIQUE    │VALIDITY  │CONSIST.  │FRESHNESS │REF.INTEG │
    │COMP-001  │UNIQ-001  │VALID-001 │CONS-001  │FRESH-001 │RI-001    │
    │COMP-002  │UNIQ-002  │VALID-002 │CONS-002  │FRESH-002 │RI-002    │
    │COMP-003  │          │VALID-003 │CONS-003  │          │          │
    │COMP-004  │          │          │          │          │          │
    └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
                        16 result dicts
                       {rule_id, severity, status,
                        total_records, failed_records, failure_pct}

SCORING LAYER
───────────────────────────────────────────────────
                        scorer.py
    Dimension score = 100 - Σ(severity_penalties)  [clamped ≥ 0]
    Final score     = Σ(dimension_score × weight)
    Critical override: any Critical FAIL → status ≤ Warning

    scored_result = {quality_score, status, dimension_scores,
                     pass/fail/warn counts, severity breakdowns}

PERSISTENCE LAYER                    REPORTING LAYER
─────────────────────────────────    ────────────────────────────────
warehouse.py                         reporter.py
┌──────────────────────────────┐     ┌──────────────────────────────┐
│ dq_run_log                   │     │ Top 5 Issues (ranked)        │
│  run_id │ timestamp │ status  │     │ Dimension Scores             │
├──────────────────────────────┤     │ All 16 Check Results         │
│ dq_results (224 rows)        │     │ Recommendations              │
│  run_id │ rule_id │ severity  │     │ Data Trust Verdict           │
│  status │ failed  │ pct       │     └──────────────────────────────┘
├──────────────────────────────┤
│ dq_summary (14 rows)         │
│  score │ status │ dimensions  │
│  critical/high/med/low counts│
└──────────────────────────────┘

DASHBOARD LAYER
───────────────────────────────────────────────────
dashboard/app.py  ←  reads DuckDB (never touches raw CSV)

  Page 1: Executive Overview  │  Score gauge │ KPIs │ Dimension bars
  Page 2: Validation Results  │  16 checks │ per-dimension expand
  Page 3: Freshness & Monitor │  Gap detection │ run history table
  Page 4: Quality Trends      │  Score line │ severity stack │ dim lines
```

---

## Project Summary Document

*(One-page format — suitable for applications, LinkedIn posts, interview leave-behind)*

---

### Automated Data Quality Monitoring Framework

**Problem**

Data teams receive raw event logs, CSV exports, and API feeds daily. Before analysts build dashboards and reports on that data, a fundamental question must be answered: *can this data be trusted?* Manual inspection doesn't scale at millions of rows. Errors go undetected. Dashboards display wrong numbers. Business decisions are made on corrupted data.

**Solution**

An automated Python framework that validates any tabular dataset against 16 quality rules across six dimensions, scores it 0–100, and produces a plain-English report and monitoring dashboard. One command runs the entire pipeline.

**Dataset**

Retail Rocket Ecommerce Dataset — 2,756,101 event records (view, add-to-cart, transaction) from a real ecommerce platform. Three tables: events, item properties (20M+ rows), category tree.

**Architecture**

```
Raw Data → Ingestion → Quality Engine (16 checks) → Scoring →
DuckDB Warehouse → Validation Report + Streamlit Dashboard
```

**Real Findings (before synthetic testing)**

| Finding | Records Affected | Business Impact |
|---|---|---|
| Duplicate transaction IDs | 67 duplicates | Revenue double-counted |
| Duplicate event rows | 3 rows | Inflated funnel metrics |
| Orphaned product references | 18,430 (9.2%) | Silent category report gaps |
| Category integrity failures | 132 references | Broken hierarchy rollups |

**Verified Results**

| Dataset | Score | Status |
|---|---|---|
| Clean | 95.4 / 100 | Excellent |
| Light corruption | 82.4 / 100 | Warning |
| Moderate corruption | 63.6 / 100 | Warning |
| Severe corruption | 55.6 / 100 | Critical |

**Tech Stack**

Python · Pandas · DuckDB · Streamlit · Plotly · SQL · Git

**Key Technical Decisions**

- *DuckDB* over SQLite — analytical SQL locally, no server, reads CSV files directly
- *Standardised check contract* — every check returns the same dict shape, decoupling the engine from the scorer and reporter
- *Critical override* — one Critical failure caps the status at Warning regardless of aggregate score; prevents dashboards from being refreshed on fundamentally broken data
- *Four corruption tiers* — demonstrates realistic score degradation, not a binary clean/broken

**Business Outcomes**

Prevents corrupted data from reaching reporting layers. Detects revenue-impacting duplicates and attribution failures automatically. Produces a dated, versioned quality report every analyst can reference. Reduces time-to-detection from "we noticed the numbers looked wrong" to "the pipeline flagged it before anyone saw it."

**Warehouse**

DuckDB warehouse with 3 tables, 14 historical runs, 224 check result rows. Score improvement journey from 55.6 → 95.4 stored and visualised in the dashboard trend chart.

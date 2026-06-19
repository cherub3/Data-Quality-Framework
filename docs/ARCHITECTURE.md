# Architecture — Enterprise Data Quality & Governance Framework

## Overview

The framework is built on a lightweight, interview-friendly stack that demonstrates governance
concepts without unnecessary complexity.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES (13 Datasets)                        │
│  Regulatory Critical │ Business Critical │ Operational │ Reference Data  │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │   src/pipeline.py      │
                    │   Master ETL Pipeline  │
                    └───────────┬────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼───────┐   ┌───────────▼───────────┐  ┌───────▼───────┐
│  Layer 1–2    │   │      Layer 3–6        │  │  Layer 7      │
│  Inventory    │   │  Testing, Exceptions, │  │  Governance   │
│  + Rulebook   │   │  Watchlist, Remediation│  │  Scoring      │
└───────┬───────┘   └───────────┬───────────┘  └───────┬───────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │      DuckDB            │
                    │   governance.duckdb    │
                    │   (8 tables)           │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │   Streamlit Dashboard  │
                    │   dashboard/app.py     │
                    │   (5 pages)            │
                    └────────────────────────┘
```

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| Data Pipeline | Python + Pandas | Layer 1–7 data generation and computation |
| Warehouse | DuckDB | In-process SQL database for all governance data |
| SQL Layer | DuckDB SQL | Analytical queries for dashboard and reporting |
| Dashboard | Streamlit | 5-page interactive governance dashboard |
| Visualisation | Plotly | Charts, gauges, heatmaps |
| Version Control | Git + GitHub | Code and documentation |

## Database Schema (8 Tables)

### 1. `data_inventory`
Registers all 13 datasets with ownership and criticality metadata.

| Column | Type | Description |
|---|---|---|
| dataset_id | VARCHAR | Unique dataset identifier (DS-001 to DS-013) |
| dataset_name | VARCHAR | Human-readable dataset name |
| domain | VARCHAR | Business domain (Customer, Risk, Finance, etc.) |
| category | VARCHAR | Criticality category (Regulatory Critical, etc.) |
| owner | VARCHAR | Accountable data owner |
| steward | VARCHAR | Operational data steward |
| refresh_frequency | VARCHAR | Daily / Intraday / Weekly / Monthly |
| source_system | VARCHAR | Originating system (CRM, Core Banking, ERP, etc.) |
| regulatory_criticality | VARCHAR | High / Medium / Low |

### 2. `control_rulebook`
Defines all 30 governance controls.

| Column | Type | Description |
|---|---|---|
| rule_id | VARCHAR | Unique rule identifier (COMP-001, ACCU-001, etc.) |
| rule_name | VARCHAR | Control name |
| category | VARCHAR | Completeness / Accuracy / Consistency / Timeliness |
| description | VARCHAR | Business description of the control |
| threshold | DOUBLE | Minimum acceptable control effectiveness % |
| severity | VARCHAR | Critical / High / Medium / Low |

### 3. `control_test_results`
Stores 30-day control testing history.

| Column | Type | Description |
|---|---|---|
| test_id | VARCHAR | Unique test run identifier |
| test_date | VARCHAR | Date of the control test |
| dataset_id | VARCHAR | FK → data_inventory |
| rule_id | VARCHAR | FK → control_rulebook |
| total_records | INTEGER | Records tested |
| pass_count | INTEGER | Records passing the control |
| fail_count | INTEGER | Records failing the control |
| failure_rate | DOUBLE | Failure percentage |
| control_effectiveness | DOUBLE | Pass rate percentage |
| status | VARCHAR | Pass / Fail |

### 4. `exceptions`
Tracks detected exceptions requiring attention.

| Column | Type | Description |
|---|---|---|
| exception_id | VARCHAR | Unique exception identifier (EXC-XXXX) |
| exception_type | VARCHAR | Critical Failure / Repeated Failure / Regulatory Issue |
| dataset_id | VARCHAR | Affected dataset |
| rule_id | VARCHAR | Violated control |
| severity | VARCHAR | Critical / High / Medium |
| priority | INTEGER | 1 = Highest |
| detected_date | VARCHAR | When detected |
| failure_rate | DOUBLE | Observed failure rate |
| regulatory_criticality | VARCHAR | Dataset regulatory criticality |
| recommended_action | VARCHAR | Prescribed response |

### 5. `dq_watchlist`
Early-warning system with trend monitoring.

| Column | Type | Description |
|---|---|---|
| watchlist_id | VARCHAR | Unique watchlist entry identifier |
| dataset_id | VARCHAR | Monitored dataset |
| null_rate_early / recent | DOUBLE | Null rate in early vs recent period |
| null_rate_trend | VARCHAR | Improving / Stable / Deteriorating |
| duplicate_rate_early / recent | DOUBLE | Duplicate rate trends |
| control_failure_rate_early / recent | DOUBLE | Control failure rate trends |
| watchlist_status | VARCHAR | Watchlist / Monitor / Clear |
| risk_trend | VARCHAR | Deteriorating / Caution / Stable / Improving |
| watchlist_reason | VARCHAR | Human-readable reason |
| priority | VARCHAR | High / Medium / Low |
| recommended_action | VARCHAR | Prescribed response |

### 6. `remediation_tickets`
Full remediation workflow tracking.

| Column | Type | Description |
|---|---|---|
| ticket_id | VARCHAR | Unique ticket identifier (REM-XXXX) |
| exception_id | VARCHAR | FK → exceptions |
| severity | VARCHAR | Inherited from exception |
| status | VARCHAR | Open / Assigned / In Progress / Escalated / Resolved |
| owner | VARCHAR | Assigned team |
| open_date | VARCHAR | Ticket creation date |
| sla_date | VARCHAR | Resolution deadline |
| sla_breach | BOOLEAN | True if past SLA and unresolved |
| root_cause | VARCHAR | Source System / ETL / Manual Entry / Mapping / Feed Delay |
| resolution_date | VARCHAR | Actual resolution date (if resolved) |
| verification_status | VARCHAR | Pending / Verified |

### 7. `domain_trust_scores`
Data Trust Score per domain (0–100).

| Column | Type | Description |
|---|---|---|
| domain | VARCHAR | Business domain |
| trust_score | DOUBLE | 0–100 composite score |
| trust_category | VARCHAR | Trusted / Monitor / At Risk |
| avg_control_effectiveness | DOUBLE | Avg control effectiveness for domain |
| dataset_count | INTEGER | Number of datasets in domain |

### 8. `governance_maturity`
Enterprise governance maturity assessment.

| Column | Type | Description |
|---|---|---|
| maturity_score | DOUBLE | 0–100 composite score |
| maturity_level | VARCHAR | Initial / Developing / Managed / Optimized |
| control_coverage | DOUBLE | % of datasets with controls |
| automation_pct | DOUBLE | % of controls automated |
| sla_compliance | DOUBLE | % of tickets resolved within SLA |
| audit_completeness | DOUBLE | % of datasets with audit trail |

## Eight Governance Layers

| Layer | Name | Purpose |
|---|---|---|
| 1 | Data Inventory | Register all datasets with metadata and ownership |
| 2 | Control Rulebook | Define 30 controls across 4 quality dimensions |
| 3 | Control Testing | Execute controls and maintain 30-day history |
| 4 | Exception Detection | Flag critical failures and regulatory risks |
| 5 | Data Quality Watchlist | Early-warning trend monitoring |
| 6 | Remediation Workflow | SLA-tracked issue resolution |
| 7 | Governance Reporting | Data Trust Score and Maturity Model |
| 8 | Monthly Governance Review | Board-ready executive narrative |

## Dashboard Pages

| Page | Name | Primary Audience |
|---|---|---|
| 1 | Executive Governance Overview | CDO, CRO, Board |
| 2 | Data Quality Watchlist | Governance Office, Data Stewards |
| 3 | Control Testing | Data Stewards, Data Engineers |
| 4 | Issue & Remediation Management | Governance Office, Ops Teams |
| 5 | Monthly Governance Review | CDO, Internal Audit, Regulators |

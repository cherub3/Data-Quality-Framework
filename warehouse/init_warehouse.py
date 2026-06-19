"""
init_warehouse.py
-----------------
Creates the DuckDB warehouse file and all three tables.
Run this once before executing the pipeline for the first time.

Tables:
  dq_run_log  — one row per pipeline execution
  dq_results  — one row per check per execution
  dq_summary  — one row per execution with the final quality score
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import duckdb
from config import WAREHOUSE_PATH

CREATE_DQ_RUN_LOG = """
CREATE TABLE IF NOT EXISTS dq_run_log (
    run_id          VARCHAR PRIMARY KEY,
    run_timestamp   TIMESTAMP,
    dataset_name    VARCHAR,
    total_records   BIGINT,
    status          VARCHAR
);
"""

CREATE_DQ_RESULTS = """
CREATE TABLE IF NOT EXISTS dq_results (
    run_id          VARCHAR,
    rule_id         VARCHAR,
    rule_desc       VARCHAR,
    dimension       VARCHAR,
    severity        VARCHAR,
    status          VARCHAR,
    total_records   BIGINT,
    failed_records  BIGINT,
    failure_pct     DOUBLE
);
"""

CREATE_DQ_SUMMARY = """
CREATE TABLE IF NOT EXISTS dq_summary (
    run_id                      VARCHAR PRIMARY KEY,
    dataset_name                VARCHAR,
    run_timestamp               TIMESTAMP,
    quality_score               DOUBLE,
    status                      VARCHAR,
    pass_count                  INTEGER,
    fail_count                  INTEGER,
    warn_count                  INTEGER,
    critical_failures           INTEGER,
    high_failures               INTEGER,
    medium_failures             INTEGER,
    low_failures                INTEGER,
    score_completeness          DOUBLE,
    score_uniqueness            DOUBLE,
    score_validity              DOUBLE,
    score_consistency           DOUBLE,
    score_freshness             DOUBLE,
    score_referential_integrity DOUBLE
);
"""


def init_warehouse():
    WAREHOUSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(WAREHOUSE_PATH))

    con.execute(CREATE_DQ_RUN_LOG)
    con.execute(CREATE_DQ_RESULTS)
    con.execute(CREATE_DQ_SUMMARY)

    con.close()
    print(f"Warehouse initialised at: {WAREHOUSE_PATH}")
    print("Tables created: dq_run_log, dq_results, dq_summary")


if __name__ == "__main__":
    init_warehouse()

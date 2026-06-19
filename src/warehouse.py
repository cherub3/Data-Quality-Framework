"""
warehouse.py
------------
All read and write operations against the DuckDB warehouse.

One responsibility: persist pipeline results and serve them to the dashboard.
No scoring, no validation logic here.

Public API:
  write_run_log(run_id, run_timestamp, dataset_name, total_records, status)
  write_results(all_results)
  write_summary(run_id, dataset_name, run_timestamp, scored_result)
  read_all_summaries()          -> pd.DataFrame
  read_results_for_run(run_id)  -> pd.DataFrame
  read_latest_run()             -> dict | None
"""

import pandas as pd
import duckdb
from config import WAREHOUSE_PATH


def _connect():
    return duckdb.connect(str(WAREHOUSE_PATH))


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------

def write_run_log(run_id, run_timestamp, dataset_name, total_records, status):
    """Insert one row into dq_run_log."""
    con = _connect()
    con.execute(
        """
        INSERT INTO dq_run_log
            (run_id, run_timestamp, dataset_name, total_records, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        [run_id, run_timestamp, dataset_name, int(total_records), status],
    )
    con.close()


def write_results(all_results):
    """Insert one row per check result into dq_results."""
    if not all_results:
        return
    con = _connect()
    con.executemany(
        """
        INSERT INTO dq_results
            (run_id, rule_id, rule_desc, dimension, severity,
             status, total_records, failed_records, failure_pct)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            [
                r["run_id"],
                r["rule_id"],
                r["rule_desc"],
                r["dimension"],
                r["severity"],
                r["status"],
                r["total_records"],
                r["failed_records"],
                r["failure_pct"],
            ]
            for r in all_results
        ],
    )
    con.close()


def write_summary(run_id, dataset_name, run_timestamp, scored_result):
    """Insert one row into dq_summary."""
    ds  = scored_result["dimension_scores"]
    con = _connect()
    con.execute(
        """
        INSERT INTO dq_summary (
            run_id, dataset_name, run_timestamp,
            quality_score, status,
            pass_count, fail_count, warn_count,
            critical_failures, high_failures, medium_failures, low_failures,
            score_completeness, score_uniqueness, score_validity,
            score_consistency, score_freshness, score_referential_integrity
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            run_id,
            dataset_name,
            run_timestamp,
            scored_result["quality_score"],
            scored_result["status"],
            scored_result["pass_count"],
            scored_result["fail_count"],
            scored_result["warn_count"],
            scored_result["critical_failures"],
            scored_result["high_failures"],
            scored_result["medium_failures"],
            scored_result["low_failures"],
            ds.get("completeness",          100.0),
            ds.get("uniqueness",            100.0),
            ds.get("validity",              100.0),
            ds.get("consistency",           100.0),
            ds.get("freshness",             100.0),
            ds.get("referential_integrity", 100.0),
        ],
    )
    con.close()


# ---------------------------------------------------------------------------
# Read operations (used by the Streamlit dashboard)
# ---------------------------------------------------------------------------

def read_all_summaries():
    """Return all rows from dq_summary joined with total_records, ordered by run_timestamp."""
    con = _connect()
    df  = con.execute(
        """
        SELECT s.*, l.total_records
        FROM dq_summary s
        LEFT JOIN dq_run_log l USING (run_id)
        ORDER BY s.run_timestamp ASC
        """
    ).df()
    con.close()
    return df


def read_results_for_run(run_id):
    """Return all check results for a specific run_id as a DataFrame."""
    con = _connect()
    df  = con.execute(
        "SELECT * FROM dq_results WHERE run_id = ? ORDER BY dimension, rule_id",
        [run_id],
    ).df()
    con.close()
    return df


def read_latest_run():
    """
    Return the most recent dq_summary row joined with total_records from
    dq_run_log, as a dict. Returns None if the warehouse is empty.
    """
    con = _connect()
    df  = con.execute(
        """
        SELECT s.*, l.total_records
        FROM dq_summary s
        LEFT JOIN dq_run_log l USING (run_id)
        ORDER BY s.run_timestamp DESC
        LIMIT 1
        """
    ).df()
    con.close()
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def read_run_log():
    """Return all rows from dq_run_log as a DataFrame."""
    con = _connect()
    df  = con.execute(
        "SELECT * FROM dq_run_log ORDER BY run_timestamp DESC"
    ).df()
    con.close()
    return df

"""
run_pipeline.py
---------------
NOTE: this file belongs to a SEPARATE, earlier subsystem (event-level QA checks
against the Retail Rocket ecommerce dataset -- src/checks.py, src/scorer.py,
warehouse/dq_warehouse.duckdb). It is NOT the Enterprise Data Quality &
Governance Framework described in README.md.

To run the governance framework (13 datasets, 30 controls, Data Trust Score,
the dashboard, and everything else documented in README.md / docs/), use:

    python src/pipeline.py

That is the correct entry point -- see README.md "Quick Start", step 2.

---

Single entry point for the (separate) event-level Data Quality Framework below.

Usage:
  python run_pipeline.py                      # runs on sample events data
  python run_pipeline.py --dataset clean      # clean_dataset.csv
  python run_pipeline.py --dataset light      # light_dataset.csv
  python run_pipeline.py --dataset moderate   # moderate_dataset.csv
  python run_pipeline.py --dataset severe     # severe_dataset.csv
  python run_pipeline.py --full               # full events.csv (Phase 2)

Execution order:
  1. Parse CLI arguments
  2. Resolve dataset path
  3. Load data (events, items, categories)
  4. Run all 16 quality checks
  5. Calculate quality score + severity counts
  6. Write run_log, results, summary to DuckDB
  7. Generate plain-text validation report
  8. Print summary to terminal
"""

import argparse
import sys
import uuid
from datetime import datetime
from pathlib import Path

from src.logger import get_logger
log = get_logger(__name__)

from config import (
    SAMPLE_EVENTS,
    CLEAN_DATASET,
    LIGHT_DATASET,
    MODERATE_DATASET,
    SEVERE_DATASET,
    RAW_EVENTS_PART1,
)
from src.ingestion  import load_events, load_item_properties, load_category_tree
from src.checks     import run_all_checks
from src.scorer     import calculate_quality_score
from src.warehouse  import write_run_log, write_results, write_summary
from src.reporter   import generate_report


# ---------------------------------------------------------------------------
# Dataset registry
# ---------------------------------------------------------------------------
DATASET_MAP = {
    "sample":   (SAMPLE_EVENTS,   True),   # (path, use_sample flag for items)
    "clean":    (CLEAN_DATASET,   True),
    "light":    (LIGHT_DATASET,   True),
    "moderate": (MODERATE_DATASET, True),
    "severe":   (SEVERE_DATASET,  True),
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the Automated Data Quality Framework."
    )
    parser.add_argument(
        "--dataset",
        choices=list(DATASET_MAP.keys()),
        default="sample",
        help="Which dataset to validate (default: sample)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run on the full events.csv instead of the sample (Phase 2)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run(dataset_name, events_path, use_sample_items=True, run_timestamp=None):
    """
    Execute the full pipeline for a single dataset.

    Parameters
    ----------
    dataset_name      : str      — label stored in the warehouse
    events_path       : Path     — path to the events CSV
    use_sample_items  : bool     — if True, load item_properties from sample/
    run_timestamp     : datetime — override run time (used by historical simulator)

    Returns
    -------
    scored_result dict
    """
    run_id        = str(uuid.uuid4())[:8]
    run_timestamp = run_timestamp or datetime.now()

    log.info(f"Pipeline start | run_id={run_id} | dataset={dataset_name} | ts={run_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    # --- Load ---
    log.info("Loading data ...")
    df_events = load_events(path=events_path, use_sample=False)
    df_items  = load_item_properties(use_sample=use_sample_items)
    df_cats   = load_category_tree()

    total_records = len(df_events)
    log.info(f"Dataset loaded: {total_records:,} events")

    # --- Check ---
    log.info("Running 16 quality checks ...")
    all_results = run_all_checks(df_events, df_items, df_cats, run_id)
    log.info(f"Checks complete: {len(all_results)} results")

    # --- Score ---
    log.info("Calculating quality score ...")
    scored_result = calculate_quality_score(all_results)
    log.info(f"Score: {scored_result['quality_score']:.1f} / 100  |  Status: {scored_result['status']}")

    # --- Warehouse ---
    log.info("Writing results to warehouse ...")
    write_run_log(run_id, run_timestamp, dataset_name, total_records, scored_result["status"])
    write_results(all_results)
    write_summary(run_id, dataset_name, run_timestamp, scored_result)
    log.info("Warehouse write complete")

    # --- Report ---
    log.info("Generating validation report ...")
    report_path = generate_report(
        all_results, scored_result, dataset_name, run_timestamp, total_records
    )
    log.info(f"Report saved: {report_path.name}")

    _print_summary(dataset_name, total_records, scored_result, report_path)
    log.info("Pipeline complete")

    return scored_result


def _print_summary(dataset_name, total_records, scored_result, report_path):
    score  = scored_result["quality_score"]
    status = scored_result["status"]
    ds     = scored_result["dimension_scores"]

    print("\n" + "=" * 46)
    print("  DATA QUALITY FRAMEWORK -- Run Complete")
    print("=" * 46)
    print(f"  Dataset    : {dataset_name}")
    print(f"  Records    : {total_records:,}")
    print()
    print(f"  QUALITY SCORE  : {score:.1f} / 100")
    print(f"  STATUS         : {status}")
    print()
    print(f"  Completeness          : {ds.get('completeness', 0):.1f}")
    print(f"  Uniqueness            : {ds.get('uniqueness', 0):.1f}")
    print(f"  Validity              : {ds.get('validity', 0):.1f}")
    print(f"  Consistency           : {ds.get('consistency', 0):.1f}")
    print(f"  Freshness             : {ds.get('freshness', 0):.1f}")
    print(f"  Referential Integrity : {ds.get('referential_integrity', 0):.1f}")
    print()
    print(f"  Checks Passed   : {scored_result['pass_count']}")
    print(f"  Checks Failed   : {scored_result['fail_count']}")
    print(f"  Checks Warned   : {scored_result['warn_count']}")
    print()
    print(f"  Critical Failures : {scored_result['critical_failures']}")
    print(f"  High Failures     : {scored_result['high_failures']}")
    print()
    print(f"  Report : {report_path.name}")
    print("=" * 46 + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = parse_args()

    if args.full:
        dataset_name = "events_full"
        events_path  = RAW_EVENTS_PART1
        use_sample   = False
    else:
        dataset_name = args.dataset
        events_path, use_sample = DATASET_MAP[args.dataset]

    if not Path(events_path).exists():
        log.error(f"Dataset not found: {events_path}")
        log.error("Run build_sample() or generate_test_data.py first.")
        sys.exit(1)

    run(dataset_name, events_path, use_sample_items=use_sample)

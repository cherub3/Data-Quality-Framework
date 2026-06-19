"""
simulate_historical_runs.py
---------------------------
Populates the DuckDB warehouse with 10 historical runs to make the
dashboard trend charts look realistic.

Run profile — a data quality improvement story over ~5 weeks:

  Run  1  (T-37 days)  severe    — framework first deployed; data is bad
  Run  2  (T-30 days)  severe    — issues still unresolved
  Run  3  (T-25 days)  moderate  — team starts fixing upstream data
  Run  4  (T-20 days)  moderate  — incremental improvement
  Run  5  (T-16 days)  moderate  — more fixes applied
  Run  6  (T-12 days)  light     — major data quality initiative lands
  Run  7  (T-8  days)  light     — stable at light issues
  Run  8  (T-5  days)  clean     — pipeline fixed; near-perfect quality
  Run  9  (T-3  days)  clean     — holding steady
  Run 10  (T-1  day )  clean     — current state (most recent run)

All runs are processed through the full pipeline with backdated timestamps.
Results are stored in dq_run_log, dq_results, and dq_summary.

Usage:
  python scripts/simulate_historical_runs.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CLEAN_DATASET, LIGHT_DATASET, MODERATE_DATASET, SEVERE_DATASET
from run_pipeline import run

# (days_ago, dataset_path, dataset_label)
RUN_PROFILES = [
    (37, SEVERE_DATASET,   "severe"),
    (30, SEVERE_DATASET,   "severe"),
    (25, MODERATE_DATASET, "moderate"),
    (20, MODERATE_DATASET, "moderate"),
    (16, MODERATE_DATASET, "moderate"),
    (12, LIGHT_DATASET,    "light"),
    ( 8, LIGHT_DATASET,    "light"),
    ( 5, CLEAN_DATASET,    "clean"),
    ( 3, CLEAN_DATASET,    "clean"),
    ( 1, CLEAN_DATASET,    "clean"),
]


def run_historical_simulations():
    now = datetime.now()

    print("=" * 50)
    print("  Historical Run Simulation")
    print(f"  Generating {len(RUN_PROFILES)} backdated runs")
    print("=" * 50)

    for i, (days_ago, dataset_path, label) in enumerate(RUN_PROFILES, 1):
        backdated_ts = now - timedelta(days=days_ago)

        print(f"\n[{i:02d}/{len(RUN_PROFILES)}] "
              f"Dataset: {label:<10}  "
              f"Date: {backdated_ts.strftime('%Y-%m-%d')}")

        run(
            dataset_name=label,
            events_path=dataset_path,
            use_sample_items=True,
            run_timestamp=backdated_ts,
        )

    print("\n" + "=" * 50)
    print("  Simulation complete.")
    print(f"  {len(RUN_PROFILES)} runs written to warehouse.")
    print("=" * 50)


if __name__ == "__main__":
    run_historical_simulations()

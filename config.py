"""
config.py
---------
Single source of truth for all project configuration.
Every path, threshold, weight, and constant lives here.
No other file should hardcode these values.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Project Root
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Data Paths
# ---------------------------------------------------------------------------
DATA_RAW_DIR       = ROOT_DIR / "data" / "raw"
DATA_SAMPLE_DIR    = ROOT_DIR / "data" / "sample"
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"

RAW_EVENTS_PART1        = DATA_RAW_DIR / "events.csv"
RAW_ITEM_PROPS_PART1    = DATA_RAW_DIR / "item_properties_part1.csv"
RAW_ITEM_PROPS_PART2    = DATA_RAW_DIR / "item_properties_part2.csv"
RAW_CATEGORY_TREE       = DATA_RAW_DIR / "category_tree.csv"

SAMPLE_EVENTS           = DATA_SAMPLE_DIR / "events_sample.csv"
SAMPLE_ITEM_PROPS       = DATA_SAMPLE_DIR / "item_properties_sample.csv"

CLEAN_DATASET           = DATA_PROCESSED_DIR / "clean_dataset.csv"
LIGHT_DATASET           = DATA_PROCESSED_DIR / "light_dataset.csv"
MODERATE_DATASET        = DATA_PROCESSED_DIR / "moderate_dataset.csv"
SEVERE_DATASET          = DATA_PROCESSED_DIR / "severe_dataset.csv"

# ---------------------------------------------------------------------------
# Warehouse
# ---------------------------------------------------------------------------
WAREHOUSE_DIR  = ROOT_DIR / "warehouse"
WAREHOUSE_PATH = WAREHOUSE_DIR / "dq_warehouse.duckdb"

# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
REPORTS_DIR = ROOT_DIR / "reports"

# ---------------------------------------------------------------------------
# Dataset Observation Window
# The Retail Rocket dataset covers May–September 2015.
# Timestamps outside this window are considered invalid.
# ---------------------------------------------------------------------------
DATASET_WINDOW_START = "2015-05-01"
DATASET_WINDOW_END   = "2015-09-30"

# Unix epoch milliseconds for the observation window boundaries
WINDOW_START_MS = 1430438400000   # 2015-05-01 00:00:00 UTC in ms
WINDOW_END_MS   = 1443657599000   # 2015-09-30 23:59:59 UTC in ms

# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------
SAMPLE_SIZE        = 200_000   # rows to use during development (Phase 1)
RANDOM_SEED        = 42        # reproducible sampling

# ---------------------------------------------------------------------------
# Valid Domain Values
# ---------------------------------------------------------------------------
VALID_EVENT_TYPES = ["view", "addtocart", "transaction"]

# ---------------------------------------------------------------------------
# Freshness
# Freshness is evaluated against the dataset's own observation window,
# not today's wall-clock date, because this is historical data.
# A dataset is considered "fresh" if its latest event is within
# FRESHNESS_MAX_AGE_DAYS of DATASET_WINDOW_END.
# ---------------------------------------------------------------------------
FRESHNESS_MAX_AGE_DAYS = 30

# ---------------------------------------------------------------------------
# Quality Score — Dimension Weights
# Must sum to 1.0
# ---------------------------------------------------------------------------
DIMENSION_WEIGHTS = {
    "completeness":          0.20,
    "uniqueness":            0.20,
    "validity":              0.20,
    "consistency":           0.20,
    "freshness":             0.10,
    "referential_integrity": 0.10,
}

# ---------------------------------------------------------------------------
# Quality Score — Severity Penalties
# Applied per failed check within a dimension.
# Dimension score starts at 100 and penalties are subtracted.
# Capped at 0 (cannot go negative).
# ---------------------------------------------------------------------------
SEVERITY_PENALTIES = {
    "critical": 25,
    "high":     15,
    "medium":    8,
    "low":       3,
}

# ---------------------------------------------------------------------------
# Dataset Status Thresholds
# ---------------------------------------------------------------------------
STATUS_EXCELLENT = 90
STATUS_GOOD      = 75
STATUS_WARNING   = 60
# Below STATUS_WARNING = Critical

# ---------------------------------------------------------------------------
# Historical Run Simulation
# Used by scripts/simulate_historical_runs.py
# ---------------------------------------------------------------------------
SIMULATION_RUNS = [
    # (label, dataset_path, description)
    # Populated in simulate_historical_runs.py — config just holds count
]
NUM_HISTORICAL_RUNS = 10

# ---------------------------------------------------------------------------
# Corruption Tier — Expected Score Ranges
# Used for validation in generate_test_data.py
# ---------------------------------------------------------------------------
TIER_SCORE_RANGES = {
    "clean":    (90, 100),
    "light":    (75,  89),
    "moderate": (60,  74),
    "severe":   ( 0,  59),
}

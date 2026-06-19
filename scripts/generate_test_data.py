"""
generate_test_data.py
---------------------
Generates four quality-tier datasets from the development sample.

Output files (data/processed/):
  clean_dataset.csv     Expected score: 90–100  (Excellent)
  light_dataset.csv     Expected score: 75–89   (Good)
  moderate_dataset.csv  Expected score: 60–74   (Warning)
  severe_dataset.csv    Expected score: <60     (Critical)

Corruption is additive across tiers — severe contains everything
moderate has, plus more. This produces a realistic degradation curve
for the dashboard trend charts.

Run:
  python scripts/generate_test_data.py

Requires:
  data/sample/events_sample.csv to exist (run build_sample() first).
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    SAMPLE_EVENTS,
    SAMPLE_ITEM_PROPS,
    CLEAN_DATASET,
    LIGHT_DATASET,
    MODERATE_DATASET,
    SEVERE_DATASET,
    RANDOM_SEED,
    VALID_EVENT_TYPES,
    WINDOW_START_MS,
    WINDOW_END_MS,
)

rng = np.random.default_rng(RANDOM_SEED)

# ---------------------------------------------------------------------------
# Corruption injection helpers
# Each helper accepts a DataFrame copy and a percentage (0.0–1.0) or count.
# Returns the modified DataFrame.
# ---------------------------------------------------------------------------

def inject_null_visitorid(df, pct):
    """Set visitorid to NaN for pct% of rows. Triggers COMP-001."""
    idx = _sample_idx(df, pct)
    df.loc[idx, "visitorid"] = np.nan
    return df


def inject_null_itemid(df, pct):
    """Set itemid to NaN for pct% of rows. Triggers COMP-002."""
    idx = _sample_idx(df, pct)
    df.loc[idx, "itemid"] = np.nan
    return df


def inject_null_transactionid(df, pct):
    """
    Remove transactionid from pct% of transaction rows.
    Triggers COMP-004 and CONS-001.
    """
    txn_idx = df[df["event"] == "transaction"].index.tolist()
    n = max(1, int(len(txn_idx) * pct))
    chosen = rng.choice(txn_idx, size=min(n, len(txn_idx)), replace=False)
    df.loc[chosen, "transactionid"] = np.nan
    return df


def inject_transactionid_on_views(df, pct):
    """
    Add a fake transactionid to pct% of view events.
    Triggers CONS-002 and VALID-005.
    """
    # Ensure transactionid column can hold strings
    df["transactionid"] = df["transactionid"].astype(object)
    view_idx = df[df["event"] == "view"].index.tolist()
    n = max(1, int(len(view_idx) * pct))
    chosen = rng.choice(view_idx, size=min(n, len(view_idx)), replace=False)
    fake_ids = [f"FAKE_TXN_{i:06d}" for i in range(len(chosen))]
    df.loc[chosen, "transactionid"] = fake_ids
    return df


def inject_duplicate_rows(df, count):
    """
    Append exact duplicate rows. Triggers UNIQ-002.
    """
    count = min(count, len(df))
    dupes = df.sample(n=count, random_state=RANDOM_SEED)
    return pd.concat([df, dupes], ignore_index=True)


def inject_duplicate_transactionids(df, count):
    """
    Duplicate a selection of transaction rows (same transactionid appears twice).
    Triggers UNIQ-001.
    """
    txn_rows = df[df["event"] == "transaction"].copy()
    count = min(count, len(txn_rows))
    dupes = txn_rows.sample(n=count, random_state=RANDOM_SEED)
    return pd.concat([df, dupes], ignore_index=True)


def inject_invalid_event_types(df, pct):
    """
    Replace event value with an invalid string for pct% of rows.
    Triggers VALID-001.
    """
    invalid_types = ["click", "scroll", "hover", "unknown", "PAGE_VIEW"]
    idx = _sample_idx(df, pct)
    replacements = rng.choice(invalid_types, size=len(idx))
    df.loc[idx, "event"] = replacements
    return df


def inject_out_of_range_timestamps(df, count):
    """
    Replace timestamp with an out-of-window value for `count` rows.
    Uses year-2000 epoch ms. Triggers VALID-002.
    """
    count = min(count, len(df))
    idx = rng.choice(df.index.tolist(), size=count, replace=False)
    # Jan 1 2000 00:00:00 UTC in ms
    bad_ts = 946684800000
    df.loc[idx, "timestamp"] = bad_ts
    return df


def inject_invalid_itemids(df, pct):
    """
    Replace itemid with non-existent very large IDs for pct% of rows.
    Triggers RI-001 (items not in catalog).
    """
    idx = _sample_idx(df, pct)
    # Use IDs far above any real itemid (Retail Rocket items are < 500k)
    fake_ids = rng.integers(low=9_000_000, high=9_999_999, size=len(idx))
    df.loc[idx, "itemid"] = fake_ids.astype(float)
    return df


# ---------------------------------------------------------------------------
# Tier builders
# ---------------------------------------------------------------------------

def build_clean(df):
    """
    Clean dataset.
    Remove obvious pre-existing issues from the raw sample:
      - Drop fully duplicate rows
      - Drop transaction rows where transactionid is already null
      - Drop rows with invalid event types
      - Drop rows with timestamps outside the observation window
    No injections. Expected score: 90–100.
    """
    d = df.copy()

    # Remove pre-existing fully duplicate rows
    before = len(d)
    d = d.drop_duplicates()
    print(f"  [clean] Removed {before - len(d):,} duplicate rows")

    # Remove pre-existing transaction rows without a transactionid
    before = len(d)
    bad_txn = (d["event"] == "transaction") & (d["transactionid"].isna())
    d = d[~bad_txn]
    print(f"  [clean] Removed {before - len(d):,} transaction rows missing transactionid")

    # Remove pre-existing invalid event types
    before = len(d)
    d = d[d["event"].isin(VALID_EVENT_TYPES)]
    print(f"  [clean] Removed {before - len(d):,} invalid event type rows")

    # Remove duplicate transactionids — keep first occurrence per transactionid
    # The real Retail Rocket data contains genuine duplicate transaction IDs.
    # For the clean dataset we keep only the first occurrence so UNIQ-001 passes.
    before = len(d)
    txn_mask  = d["event"] == "transaction"
    txn_dedup = d[txn_mask].drop_duplicates(subset=["transactionid"], keep="first")
    d = pd.concat([d[~txn_mask], txn_dedup], ignore_index=True)
    print(f"  [clean] Removed {before - len(d):,} duplicate transactionid rows")

    # Remove pre-existing out-of-range timestamps
    before = len(d)
    d = d[(d["timestamp"] >= WINDOW_START_MS) & (d["timestamp"] <= WINDOW_END_MS)]
    print(f"  [clean] Removed {before - len(d):,} out-of-range timestamp rows")

    return d.reset_index(drop=True)


def build_light(df_clean):
    """
    Lightly corrupted dataset.
    Applies minor issues to a few dimensions.
    Expected score: 75–89 (Good).

    Injections:
      - 0.5% null visitorid          → COMP-001
      - 150 duplicate rows           → UNIQ-002
      - 0.5% invalid event types     → VALID-001
    """
    d = df_clean.copy()
    print("  [light] Injecting null visitorid (0.5%) ...")
    d = inject_null_visitorid(d, 0.005)
    print("  [light] Injecting 150 duplicate rows ...")
    d = inject_duplicate_rows(d, 150)
    print("  [light] Injecting invalid event types (0.5%) ...")
    d = inject_invalid_event_types(d, 0.005)
    return d.reset_index(drop=True)


def build_moderate(df_clean):
    """
    Moderately corrupted dataset.
    Applies issues across multiple dimensions.
    Expected score: 60–74 (Warning).

    Injections (all light injections plus):
      - 1.0% null visitorid          → COMP-001
      - 1.5% null transactionid on txn → COMP-004, CONS-001
      - 250 duplicate rows           → UNIQ-002
      - 100 duplicate transactionids → UNIQ-001
      - 0.8% invalid event types     → VALID-001
      - 200 out-of-range timestamps  → VALID-002
    """
    d = df_clean.copy()
    print("  [moderate] Injecting null visitorid (1.0%) ...")
    d = inject_null_visitorid(d, 0.010)
    print("  [moderate] Injecting null transactionid on transaction events (1.5%) ...")
    d = inject_null_transactionid(d, 0.015)
    print("  [moderate] Injecting 250 duplicate rows ...")
    d = inject_duplicate_rows(d, 250)
    print("  [moderate] Injecting 100 duplicate transactionids ...")
    d = inject_duplicate_transactionids(d, 100)
    print("  [moderate] Injecting invalid event types (0.8%) ...")
    d = inject_invalid_event_types(d, 0.008)
    print("  [moderate] Injecting 200 out-of-range timestamps ...")
    d = inject_out_of_range_timestamps(d, 200)
    return d.reset_index(drop=True)


def build_severe(df_clean):
    """
    Severely corrupted dataset.
    Applies heavy issues across all dimensions.
    Expected score: <60 (Critical).

    Injections (all moderate injections plus higher volumes):
      - 4% null visitorid            → COMP-001
      - 2.5% null itemid             → COMP-002
      - 5% null transactionid on txn → COMP-004, CONS-001
      - 1.5% transactionid on views  → CONS-002
      - 700 duplicate rows           → UNIQ-002
      - 400 duplicate transactionids → UNIQ-001
      - 2.5% invalid event types     → VALID-001
      - 700 out-of-range timestamps  → VALID-002
      - 6% non-existent itemids      → RI-001
    """
    d = df_clean.copy()
    print("  [severe] Injecting null visitorid (4%) ...")
    d = inject_null_visitorid(d, 0.04)
    print("  [severe] Injecting null itemid (2.5%) ...")
    d = inject_null_itemid(d, 0.025)
    print("  [severe] Injecting null transactionid on transaction events (5%) ...")
    d = inject_null_transactionid(d, 0.05)
    print("  [severe] Injecting transactionid on view events (1.5%) ...")
    d = inject_transactionid_on_views(d, 0.015)
    print("  [severe] Injecting 700 duplicate rows ...")
    d = inject_duplicate_rows(d, 700)
    print("  [severe] Injecting 400 duplicate transactionids ...")
    d = inject_duplicate_transactionids(d, 400)
    print("  [severe] Injecting invalid event types (2.5%) ...")
    d = inject_invalid_event_types(d, 0.025)
    print("  [severe] Injecting 700 out-of-range timestamps ...")
    d = inject_out_of_range_timestamps(d, 700)
    print("  [severe] Injecting non-existent itemids (6%) ...")
    d = inject_invalid_itemids(d, 0.06)
    return d.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Validation — print a quick audit of each generated dataset
# ---------------------------------------------------------------------------

def audit_dataset(df, label):
    """Print a quick summary of a dataset to verify injections worked."""
    txn = df[df["event"] == "transaction"] if "event" in df.columns else pd.DataFrame()

    print(f"\n  {'-'*50}")
    print(f"  AUDIT: {label}")
    print(f"  {'-'*50}")
    print(f"  Total rows              : {len(df):,}")
    print(f"  Null visitorid          : {df['visitorid'].isna().sum():,}")
    print(f"  Null itemid             : {df['itemid'].isna().sum():,}")
    print(f"  Invalid event types     : {(~df['event'].isin(VALID_EVENT_TYPES + [np.nan])).sum():,}")
    print(f"  Duplicate rows          : {df.duplicated().sum():,}")
    if len(txn) > 0:
        print(f"  Transaction rows        : {len(txn):,}")
        print(f"  Txn missing tx_id       : {txn['transactionid'].isna().sum():,}")
        dup_txn = txn[txn['transactionid'].notna()]
        print(f"  Duplicate transact_ids  : {dup_txn.duplicated(subset='transactionid').sum():,}")
    out_of_range = ((df['timestamp'] < WINDOW_START_MS) | (df['timestamp'] > WINDOW_END_MS)).sum()
    print(f"  Out-of-range timestamps : {out_of_range:,}")
    print()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _sample_idx(df, pct):
    """Return a list of row indices representing pct% of the DataFrame."""
    n = max(1, int(len(df) * pct))
    return rng.choice(df.index.tolist(), size=min(n, len(df)), replace=False).tolist()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 54)
    print("  Test Data Generator")
    print("=" * 54)

    if not SAMPLE_EVENTS.exists():
        print(f"\n[ERROR] Sample not found: {SAMPLE_EVENTS}")
        print("Run build_sample() from ingestion.py first.\n")
        sys.exit(1)

    print("\n[1/5] Loading sample events ...")
    df_raw = pd.read_csv(SAMPLE_EVENTS)
    print(f"      Loaded {len(df_raw):,} rows")

    DATA_PROCESSED = CLEAN_DATASET.parent
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    # --- Clean ---
    print("\n[2/5] Building CLEAN dataset ...")
    df_clean = build_clean(df_raw)
    df_clean.to_csv(CLEAN_DATASET, index=False)
    audit_dataset(df_clean, "clean_dataset.csv")
    print(f"      Saved -> {CLEAN_DATASET}")

    # --- Light ---
    print("\n[3/5] Building LIGHT dataset ...")
    df_light = build_light(df_clean)
    df_light.to_csv(LIGHT_DATASET, index=False)
    audit_dataset(df_light, "light_dataset.csv")
    print(f"      Saved -> {LIGHT_DATASET}")

    # --- Moderate ---
    print("\n[4/5] Building MODERATE dataset ...")
    df_moderate = build_moderate(df_clean)
    df_moderate.to_csv(MODERATE_DATASET, index=False)
    audit_dataset(df_moderate, "moderate_dataset.csv")
    print(f"      Saved -> {MODERATE_DATASET}")

    # --- Severe ---
    print("\n[5/5] Building SEVERE dataset ...")
    df_severe = build_severe(df_clean)
    df_severe.to_csv(SEVERE_DATASET, index=False)
    audit_dataset(df_severe, "severe_dataset.csv")
    print(f"      Saved -> {SEVERE_DATASET}")

    print("=" * 54)
    print("  All four datasets generated successfully.")
    print("=" * 54)


if __name__ == "__main__":
    main()

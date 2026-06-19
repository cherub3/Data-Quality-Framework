"""
ingestion.py
------------
Loads raw Retail Rocket CSV files into DataFrames.

Public API:
  load_events(path=None, use_sample=True)   -> pd.DataFrame
  load_item_properties(use_sample=True)     -> pd.DataFrame
  load_category_tree()                      -> pd.DataFrame
  build_sample(force_rebuild=False)         -> None

Design decisions:
  - Events are loaded with explicit dtypes to avoid Pandas guessing.
    visitorid and itemid are kept as float64 on load (they may contain
    NaN in corrupted datasets) and cast after null checks in checks.py.
  - Item properties: we load both parts, concatenate, then keep only the
    rows where property = 'categoryid'. This reduces 8.8M rows to ~400k
    and is the only property needed for referential integrity checks.
  - The sample is saved to disk after first creation and reused on
    subsequent runs. Use force_rebuild=True to regenerate it.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logger import get_logger
log = get_logger(__name__)

from config import (
    RAW_EVENTS_PART1,
    RAW_ITEM_PROPS_PART1,
    RAW_ITEM_PROPS_PART2,
    RAW_CATEGORY_TREE,
    SAMPLE_EVENTS,
    SAMPLE_ITEM_PROPS,
    SAMPLE_SIZE,
    RANDOM_SEED,
)

# ---------------------------------------------------------------------------
# Column dtype map for events â€” explicit to avoid Pandas misinterpretation.
# transactionid is read as str; NaN values become the string 'nan' unless
# we use keep_default_na=True (the default), which we do.
# ---------------------------------------------------------------------------
EVENTS_DTYPES = {
    "timestamp":     "float64",  # ms since epoch; float allows NaN on bad rows
    "visitorid":     "float64",  # float allows NaN; cast to int after null checks
    "event":         "object",
    "itemid":        "float64",  # float allows NaN
    "transactionid": "object",   # alphanumeric IDs or NaN
}

ITEM_PROPS_DTYPES = {
    "timestamp": "float64",
    "itemid":    "float64",
    "property":  "object",
    "value":     "object",
}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def load_events(path=None, use_sample=True):
    """
    Load events data into a DataFrame.

    Parameters
    ----------
    path : Path or str, optional
        Explicit path to a CSV file (used for clean/corrupted datasets).
        If None, loads from sample or raw depending on use_sample.
    use_sample : bool
        If True (default) and path is None, load from data/sample/.
        If False and path is None, load full events.csv from data/raw/.

    Returns
    -------
    pd.DataFrame with columns:
        timestamp, visitorid, event, itemid, transactionid
    """
    if path is not None:
        target = Path(path)
    elif use_sample:
        target = SAMPLE_EVENTS
    else:
        target = RAW_EVENTS_PART1

    if not target.exists():
        raise FileNotFoundError(
            f"Events file not found: {target}\n"
            f"Run build_sample() first, or place events.csv in data/raw/."
        )

    df = pd.read_csv(
        target,
        dtype=EVENTS_DTYPES,
        keep_default_na=True,
    )

    # Normalise column names (strip whitespace)
    df.columns = df.columns.str.strip()

    log.info(f"Loaded events: {len(df):,} rows from {target.name}")
    return df


def load_item_properties(use_sample=True):
    """
    Load item properties and return a DataFrame of unique itemids with
    their categoryid (the only property needed for quality checks).

    For the sample: loads from data/sample/item_properties_sample.csv.
    For full data : loads and merges both raw part files, extracts categoryid rows.

    Returns
    -------
    pd.DataFrame with columns: itemid, categoryid
        One row per itemid. itemid is the known product catalog.
    """
    if use_sample:
        target = SAMPLE_ITEM_PROPS
        if not target.exists():
            raise FileNotFoundError(
                f"Item properties sample not found: {target}\n"
                f"Run build_sample() first."
            )
        df = pd.read_csv(target)
        log.info(f"Loaded item_properties: {len(df):,} unique items from {target.name}")
        return df

    # Full data: load both parts and concatenate
    log.info("Loading item_properties_part1.csv ...")
    part1 = pd.read_csv(RAW_ITEM_PROPS_PART1, dtype=ITEM_PROPS_DTYPES, keep_default_na=True)

    log.info("Loading item_properties_part2.csv ...")
    part2 = pd.read_csv(RAW_ITEM_PROPS_PART2, dtype=ITEM_PROPS_DTYPES, keep_default_na=True)

    combined = pd.concat([part1, part2], ignore_index=True)
    log.info(f"Combined item_properties: {len(combined):,} rows")

    df = _extract_item_catalog(combined)
    log.info(f"Extracted {len(df):,} unique items with categoryid")
    return df


def load_category_tree():
    """
    Load category_tree.csv.

    Returns
    -------
    pd.DataFrame with columns: categoryid, parentid
    """
    if not RAW_CATEGORY_TREE.exists():
        raise FileNotFoundError(
            f"category_tree.csv not found: {RAW_CATEGORY_TREE}\n"
            f"Place the file in data/raw/."
        )
    df = pd.read_csv(
        RAW_CATEGORY_TREE,
        dtype={"categoryid": "float64", "parentid": "float64"},
        keep_default_na=True,
    )
    df.columns = df.columns.str.strip()
    log.info(f"Loaded category_tree: {len(df):,} categories")
    return df


def build_sample(force_rebuild=False):
    """
    Create a reproducible 200k-row sample from raw events and a matching
    item_properties summary (unique itemids with categoryid).

    Saves:
      data/sample/events_sample.csv
      data/sample/item_properties_sample.csv

    Skips if both files already exist, unless force_rebuild=True.
    """
    sample_exists = SAMPLE_EVENTS.exists() and SAMPLE_ITEM_PROPS.exists()

    if sample_exists and not force_rebuild:
        log.info("Sample already exists. Use force_rebuild=True to regenerate.")
        return

    # --- Events sample ---
    if not RAW_EVENTS_PART1.exists():
        raise FileNotFoundError(
            f"Raw events file not found: {RAW_EVENTS_PART1}\n"
            f"Download the Retail Rocket dataset and place events.csv in data/raw/."
        )

    log.info("Loading full events.csv to build sample ...")
    df_full = pd.read_csv(RAW_EVENTS_PART1, dtype=EVENTS_DTYPES, keep_default_na=True)
    df_full.columns = df_full.columns.str.strip()
    log.info(f"Full events loaded: {len(df_full):,} rows")

    n = min(SAMPLE_SIZE, len(df_full))
    df_sample = df_full.sample(n=n, random_state=RANDOM_SEED).reset_index(drop=True)

    SAMPLE_EVENTS.parent.mkdir(parents=True, exist_ok=True)
    df_sample.to_csv(SAMPLE_EVENTS, index=False)
    log.info(f"Sample saved: {len(df_sample):,} rows -> {SAMPLE_EVENTS}")

    # --- Item properties sample ---
    log.info("Building item_properties sample ...")
    df_items = load_item_properties(use_sample=False)

    SAMPLE_ITEM_PROPS.parent.mkdir(parents=True, exist_ok=True)
    df_items.to_csv(SAMPLE_ITEM_PROPS, index=False)
    log.info(f"Item properties saved: {len(df_items):,} rows -> {SAMPLE_ITEM_PROPS}")


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_item_catalog(df_props):
    """
    From the full item_properties DataFrame, extract one row per itemid
    with its most recent categoryid.

    Strategy: filter to property == 'categoryid', sort by timestamp descending,
    keep the last (most recent) categoryid per itemid.
    """
    cat_rows = df_props[df_props["property"] == "categoryid"].copy()

    if cat_rows.empty:
        # Fallback: return unique itemids with no categoryid
        unique_items = df_props[["itemid"]].drop_duplicates().reset_index(drop=True)
        unique_items["categoryid"] = np.nan
        return unique_items

    # Most recent categoryid per item
    cat_rows = cat_rows.sort_values("timestamp", ascending=False)
    cat_rows = cat_rows.drop_duplicates(subset="itemid", keep="first")

    result = cat_rows[["itemid", "value"]].rename(columns={"value": "categoryid"}).reset_index(drop=True)

    # categoryid values in item_properties are stored as floats-as-strings (e.g. "1234.0")
    # Normalise to float so they match category_tree.categoryid
    result["categoryid"] = pd.to_numeric(result["categoryid"], errors="coerce")

    return result

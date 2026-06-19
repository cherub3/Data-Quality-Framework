"""
test_checks.py
--------------
Unit tests for every check category in checks.py.

Each test constructs a minimal DataFrame with known data, calls the check
function, and asserts the expected status and failed_records count.

Pattern:
  - *_pass  test: clean data  → expect status == "PASS", failed_records == 0
  - *_fail  test: bad data    → expect status == "FAIL" or "WARN", failed_records > 0

Run with:
  python -m pytest tests/ -v
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.checks import (
    check_null_visitorid,
    check_null_itemid,
    check_duplicate_transactionid,
    check_duplicate_event_rows,
    check_invalid_event_type,
    check_timestamp_out_of_range,
    check_transaction_missing_id,
    check_non_transaction_has_id,
    check_transaction_without_prior_activity,
    check_data_freshness,
    check_timestamp_gap,
    check_items_not_in_catalog,
    check_categories_not_in_tree,
)
from config import WINDOW_START_MS, WINDOW_END_MS

RUN_ID = "test_run"

# ---------------------------------------------------------------------------
# Helpers — build minimal DataFrames for specific scenarios
# ---------------------------------------------------------------------------

def _events(rows):
    """Build an events DataFrame from a list of dicts."""
    defaults = {
        "timestamp":     1430438400000 + 1000,  # safely inside window
        "visitorid":     1.0,
        "event":         "view",
        "itemid":        100.0,
        "transactionid": np.nan,
    }
    return pd.DataFrame([{**defaults, **r} for r in rows])


def _items(itemids):
    """Build a minimal item_properties DataFrame with the given itemids."""
    return pd.DataFrame({"itemid": [float(i) for i in itemids], "categoryid": [10.0] * len(itemids)})


def _categories(catids):
    """Build a minimal category_tree DataFrame."""
    return pd.DataFrame({"categoryid": [float(c) for c in catids], "parentid": [np.nan] * len(catids)})


# ---------------------------------------------------------------------------
# COMPLETENESS
# ---------------------------------------------------------------------------

class TestCompleteness:

    def test_null_visitorid_pass(self):
        df = _events([{"visitorid": 1.0}, {"visitorid": 2.0}])
        r  = check_null_visitorid(df, RUN_ID)
        assert r["status"] == "PASS"
        assert r["failed_records"] == 0

    def test_null_visitorid_fail(self):
        df = _events([{"visitorid": np.nan}, {"visitorid": 1.0}, {"visitorid": np.nan}])
        r  = check_null_visitorid(df, RUN_ID)
        assert r["status"] == "FAIL"
        assert r["failed_records"] == 2

    def test_null_itemid_pass(self):
        df = _events([{"itemid": 100.0}, {"itemid": 200.0}])
        r  = check_null_itemid(df, RUN_ID)
        assert r["status"] == "PASS"
        assert r["failed_records"] == 0

    def test_null_itemid_fail(self):
        df = _events([{"itemid": np.nan}, {"itemid": 100.0}])
        r  = check_null_itemid(df, RUN_ID)
        assert r["status"] == "FAIL"
        assert r["failed_records"] == 1


# ---------------------------------------------------------------------------
# UNIQUENESS
# ---------------------------------------------------------------------------

class TestUniqueness:

    def test_duplicate_transactionid_pass(self):
        df = _events([
            {"event": "transaction", "transactionid": "TXN001"},
            {"event": "transaction", "transactionid": "TXN002"},
        ])
        r = check_duplicate_transactionid(df, RUN_ID)
        assert r["status"] == "PASS"
        assert r["failed_records"] == 0

    def test_duplicate_transactionid_fail(self):
        df = _events([
            {"event": "transaction", "transactionid": "TXN001"},
            {"event": "transaction", "transactionid": "TXN001"},  # duplicate
            {"event": "transaction", "transactionid": "TXN002"},
        ])
        r = check_duplicate_transactionid(df, RUN_ID)
        assert r["status"] == "FAIL"
        assert r["failed_records"] == 2  # both rows with TXN001 are flagged

    def test_duplicate_rows_pass(self):
        df = _events([
            {"visitorid": 1.0, "itemid": 100.0, "event": "view"},
            {"visitorid": 2.0, "itemid": 200.0, "event": "view"},
        ])
        r = check_duplicate_event_rows(df, RUN_ID)
        assert r["status"] == "PASS"
        assert r["failed_records"] == 0

    def test_duplicate_rows_fail(self):
        row = {"visitorid": 1.0, "itemid": 100.0, "event": "view",
               "timestamp": 1430438401000, "transactionid": np.nan}
        df  = pd.DataFrame([row, row])  # exact duplicate
        r   = check_duplicate_event_rows(df, RUN_ID)
        assert r["status"] == "FAIL"
        assert r["failed_records"] == 1  # pandas.duplicated keeps=first → 1 duplicate


# ---------------------------------------------------------------------------
# VALIDITY
# ---------------------------------------------------------------------------

class TestValidity:

    def test_valid_event_types_pass(self):
        df = _events([
            {"event": "view"},
            {"event": "addtocart"},
            {"event": "transaction", "transactionid": "T1"},
        ])
        r = check_invalid_event_type(df, RUN_ID)
        assert r["status"] == "PASS"
        assert r["failed_records"] == 0

    def test_invalid_event_types_fail(self):
        df = _events([
            {"event": "view"},
            {"event": "click"},    # invalid
            {"event": "hover"},    # invalid
        ])
        r = check_invalid_event_type(df, RUN_ID)
        assert r["status"] == "FAIL"
        assert r["failed_records"] == 2

    def test_timestamp_in_range_pass(self):
        df = _events([
            {"timestamp": WINDOW_START_MS + 1000},
            {"timestamp": WINDOW_END_MS   - 1000},
        ])
        r = check_timestamp_out_of_range(df, RUN_ID)
        assert r["status"] == "PASS"
        assert r["failed_records"] == 0

    def test_timestamp_out_of_range_fail(self):
        df = _events([
            {"timestamp": WINDOW_START_MS + 1000},   # valid
            {"timestamp": 946684800000},              # year 2000 — way out of range
        ])
        r = check_timestamp_out_of_range(df, RUN_ID)
        assert r["status"] == "FAIL"
        assert r["failed_records"] == 1


# ---------------------------------------------------------------------------
# CONSISTENCY
# ---------------------------------------------------------------------------

class TestConsistency:

    def test_transaction_with_id_pass(self):
        df = _events([
            {"event": "view"},
            {"event": "transaction", "transactionid": "TXN001"},
        ])
        r = check_transaction_missing_id(df, RUN_ID)
        assert r["status"] == "PASS"
        assert r["failed_records"] == 0

    def test_transaction_missing_id_fail(self):
        df = _events([
            {"event": "transaction", "transactionid": np.nan},
            {"event": "transaction", "transactionid": "TXN001"},
        ])
        r = check_transaction_missing_id(df, RUN_ID)
        assert r["status"] == "FAIL"
        assert r["failed_records"] == 1

    def test_non_transaction_no_id_pass(self):
        df = _events([
            {"event": "view",       "transactionid": np.nan},
            {"event": "addtocart",  "transactionid": np.nan},
        ])
        r = check_non_transaction_has_id(df, RUN_ID)
        assert r["status"] == "PASS"
        assert r["failed_records"] == 0

    def test_non_transaction_has_id_fail(self):
        df = _events([
            {"event": "view", "transactionid": "TXN999"},   # should not have an ID
            {"event": "view", "transactionid": np.nan},
        ])
        r = check_non_transaction_has_id(df, RUN_ID)
        assert r["status"] == "FAIL"
        assert r["failed_records"] == 1

    def test_cons003_pass(self):
        """Visitor's first event is a view — expected normal behaviour."""
        df = _events([
            {"visitorid": 1.0, "event": "view",        "timestamp": WINDOW_START_MS + 100},
            {"visitorid": 1.0, "event": "transaction",  "timestamp": WINDOW_START_MS + 200,
             "transactionid": "T1"},
        ])
        r = check_transaction_without_prior_activity(df, RUN_ID)
        assert r["status"] == "PASS"
        assert r["failed_records"] == 0

    def test_cons003_warn(self):
        """
        Visitor's first (and only) event is a transaction.
        This is a WARN (medium severity) — it is a heuristic flag, not a
        definitive failure. Legitimate scenarios exist (guest checkout,
        API-driven orders). The check fires but should be investigated, not
        automatically rejected.
        """
        df = _events([
            {"visitorid": 1.0, "event": "transaction",  "timestamp": WINDOW_START_MS + 100,
             "transactionid": "T1"},
        ])
        r = check_transaction_without_prior_activity(df, RUN_ID)
        # Status is WARN (medium severity) — a signal for investigation, not a hard failure
        assert r["status"] == "WARN"
        assert r["failed_records"] == 1


# ---------------------------------------------------------------------------
# FRESHNESS
# ---------------------------------------------------------------------------

class TestFreshness:

    def test_data_freshness_pass(self):
        df = _events([{"timestamp": WINDOW_START_MS + 86400000}])  # one day inside window
        r  = check_data_freshness(df, RUN_ID)
        assert r["status"] == "PASS"
        assert r["failed_records"] == 0

    def test_data_freshness_fail(self):
        df = _events([{"timestamp": 946684800000}])  # year 2000 — outside window
        r  = check_data_freshness(df, RUN_ID)
        assert r["status"] == "FAIL"
        assert r["failed_records"] == 1

    def test_timestamp_gap_pass(self):
        """Daily events with no gap — should pass."""
        one_day_ms = 86_400_000
        df = _events([
            {"timestamp": WINDOW_START_MS + (i * one_day_ms)}
            for i in range(10)
        ])
        r = check_timestamp_gap(df, RUN_ID)
        assert r["status"] == "PASS"
        assert r["failed_records"] == 0

    def test_timestamp_gap_warn(self):
        """Two events with a 10-day gap between them — should warn."""
        ten_days_ms = 10 * 86_400_000
        df = _events([
            {"timestamp": WINDOW_START_MS + 1000},
            {"timestamp": WINDOW_START_MS + ten_days_ms},
        ])
        r = check_timestamp_gap(df, RUN_ID)
        assert r["status"] == "WARN"
        assert r["failed_records"] >= 7  # gap length in days >= 7


# ---------------------------------------------------------------------------
# REFERENTIAL INTEGRITY
# ---------------------------------------------------------------------------

class TestReferentialIntegrity:

    def test_items_in_catalog_pass(self):
        df_events = _events([{"itemid": 100.0}, {"itemid": 200.0}])
        df_items  = _items([100, 200, 300])
        r = check_items_not_in_catalog(df_events, df_items, RUN_ID)
        assert r["status"] == "PASS"
        assert r["failed_records"] == 0

    def test_items_not_in_catalog_fail(self):
        df_events = _events([{"itemid": 100.0}, {"itemid": 999.0}])  # 999 not in catalog
        df_items  = _items([100, 200])
        r = check_items_not_in_catalog(df_events, df_items, RUN_ID)
        assert r["status"] == "FAIL"
        assert r["failed_records"] == 1

    def test_categories_in_tree_pass(self):
        df_items = pd.DataFrame({"itemid": [1.0, 2.0], "categoryid": [10.0, 20.0]})
        df_cats  = _categories([10, 20, 30])
        r = check_categories_not_in_tree(df_items, df_cats, RUN_ID)
        assert r["status"] == "PASS"
        assert r["failed_records"] == 0

    def test_categories_not_in_tree_fail(self):
        df_items = pd.DataFrame({"itemid": [1.0, 2.0], "categoryid": [10.0, 999.0]})  # 999 missing
        df_cats  = _categories([10, 20])
        r = check_categories_not_in_tree(df_items, df_cats, RUN_ID)
        assert r["status"] == "FAIL"
        assert r["failed_records"] == 1

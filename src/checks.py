"""
checks.py
---------
All 16 quality check functions.

Every function:
  - Accepts one or more DataFrames + a run_id string
  - Returns a standardised result dict via _result()
  - Has no side effects (no file I/O, no printing)

Result dict schema:
  run_id          str
  rule_id         str   e.g. "COMP-001"
  rule_desc       str   human-readable description
  dimension       str   completeness | uniqueness | validity |
                        consistency | freshness | referential_integrity
  severity        str   critical | high | medium | low
  status          str   PASS | FAIL | WARN
  total_records   int
  failed_records  int
  failure_pct     float (0.0 - 100.0)

Status logic:
  failed_records == 0            -> PASS
  severity in (critical, high)   -> FAIL
  severity in (medium, low)      -> WARN
"""

import pandas as pd
import numpy as np
from config import VALID_EVENT_TYPES, WINDOW_START_MS, WINDOW_END_MS


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _result(run_id, rule_id, rule_desc, dimension, severity, total, failed):
    """Build a standardised check result dict."""
    failure_pct = round((failed / total * 100), 4) if total > 0 else 0.0

    if failed == 0:
        status = "PASS"
    elif severity in ("critical", "high"):
        status = "FAIL"
    else:
        status = "WARN"

    return {
        "run_id":         run_id,
        "rule_id":        rule_id,
        "rule_desc":      rule_desc,
        "dimension":      dimension,
        "severity":       severity,
        "status":         status,
        "total_records":  int(total),
        "failed_records": int(failed),
        "failure_pct":    failure_pct,
    }


# ---------------------------------------------------------------------------
# COMPLETENESS (4 checks)
# Business context: missing core identifiers break attribution, revenue
# tracking, and funnel analysis.
# ---------------------------------------------------------------------------

def check_null_visitorid(df_events, run_id):
    """
    COMP-001 | Critical
    visitorid must not be null.
    Business risk: user behaviour cannot be attributed to any visitor.
    Marketing funnel and conversion reports become unreliable.
    """
    total  = len(df_events)
    failed = int(df_events["visitorid"].isna().sum())
    return _result(
        run_id, "COMP-001",
        "visitorid must not be null",
        "completeness", "critical", total, failed,
    )


def check_null_itemid(df_events, run_id):
    """
    COMP-002 | Critical
    itemid must not be null.
    Business risk: affected events cannot be linked to any product.
    Catalogue and revenue reports will have gaps.
    """
    total  = len(df_events)
    failed = int(df_events["itemid"].isna().sum())
    return _result(
        run_id, "COMP-002",
        "itemid must not be null",
        "completeness", "critical", total, failed,
    )


def check_null_event(df_events, run_id):
    """
    COMP-003 | Critical
    event type must not be null.
    Business risk: event type is unknown; funnel analysis includes
    unclassifiable rows.
    """
    total  = len(df_events)
    failed = int(df_events["event"].isna().sum())
    return _result(
        run_id, "COMP-003",
        "event type must not be null",
        "completeness", "critical", total, failed,
    )


def check_missing_transactionid_on_transaction(df_events, run_id):
    """
    COMP-004 | Critical
    transactionid must not be null where event = 'transaction'.
    Business risk: purchases have no order reference.
    Fulfilment, refunds, and revenue reconciliation fail.
    """
    txn_rows = df_events[df_events["event"] == "transaction"]
    total    = len(txn_rows)
    failed   = int(txn_rows["transactionid"].isna().sum())
    return _result(
        run_id, "COMP-004",
        "transactionid must not be null on transaction events",
        "completeness", "critical", total, failed,
    )


# ---------------------------------------------------------------------------
# UNIQUENESS (2 checks)
# Business context: duplicates inflate event counts, distort conversion
# rates, and double-count revenue.
# ---------------------------------------------------------------------------

def check_duplicate_transactionid(df_events, run_id):
    """
    UNIQ-001 | Critical
    transactionid must be unique across transaction events.
    Business risk: revenue is double-counted. Finance reports overstate sales.
    """
    txn = df_events[
        (df_events["event"] == "transaction") &
        (df_events["transactionid"].notna())
    ]
    total  = len(txn)
    # A transactionid is a duplicate if it appears more than once
    dup_mask = txn.duplicated(subset=["transactionid"], keep=False)
    failed   = int(dup_mask.sum())
    return _result(
        run_id, "UNIQ-001",
        "transactionid must be unique per transaction event",
        "uniqueness", "critical", total, failed,
    )


def check_duplicate_event_rows(df_events, run_id):
    """
    UNIQ-002 | High
    No fully duplicate rows (all five columns identical).
    Business risk: event counts are inflated; conversion rates are wrong.
    """
    total  = len(df_events)
    failed = int(df_events.duplicated().sum())
    return _result(
        run_id, "UNIQ-002",
        "no fully duplicate rows across all columns",
        "uniqueness", "high", total, failed,
    )


# ---------------------------------------------------------------------------
# VALIDITY (3 checks)
# Business context: invalid field values corrupt categorical aggregations
# and time-series analysis.
# ---------------------------------------------------------------------------

def check_invalid_event_type(df_events, run_id):
    """
    VALID-001 | Critical
    event must be one of: view, addtocart, transaction.
    Business risk: unrecognised event types corrupt funnel metrics
    and recommendation models.
    """
    total    = len(df_events)
    # Null events are caught by COMP-003; exclude them here to avoid double-counting
    non_null = df_events[df_events["event"].notna()]
    failed   = int((~non_null["event"].isin(VALID_EVENT_TYPES)).sum())
    return _result(
        run_id, "VALID-001",
        "event must be one of: view, addtocart, transaction",
        "validity", "critical", total, failed,
    )


def check_timestamp_out_of_range(df_events, run_id):
    """
    VALID-002 | High
    timestamp must fall within the dataset observation window
    (2015-05-01 to 2015-09-30, in Unix ms).
    Business risk: out-of-range timestamps corrupt trend charts
    and time-based aggregations.
    """
    total = len(df_events)
    ts    = df_events["timestamp"]
    # Exclude nulls from the range check (null timestamps are a separate completeness issue)
    non_null_ts = ts.dropna()
    out_of_range = (
        (non_null_ts < WINDOW_START_MS) | (non_null_ts > WINDOW_END_MS)
    ).sum()
    failed = int(out_of_range)
    return _result(
        run_id, "VALID-002",
        "timestamp must fall within dataset observation window (2015-05-01 to 2015-09-30)",
        "validity", "high", total, failed,
    )


def check_invalid_itemid(df_events, run_id):
    """
    VALID-003 | High
    itemid must be a positive number (> 0).
    Business risk: zero or negative item IDs cannot be joined to the
    product catalogue; category and revenue reports break.
    """
    total    = len(df_events)
    non_null = df_events[df_events["itemid"].notna()]
    failed   = int((non_null["itemid"] <= 0).sum())
    return _result(
        run_id, "VALID-003",
        "itemid must be a positive integer",
        "validity", "high", total, failed,
    )


# ---------------------------------------------------------------------------
# CONSISTENCY (3 checks)
# Business context: consistency rules encode business logic — violations
# indicate broken tracking, bad ingestion, or upstream system errors.
# ---------------------------------------------------------------------------

def check_transaction_missing_id(df_events, run_id):
    """
    CONS-001 | Critical
    Every transaction event must have a non-null transactionid.
    Duplicate of COMP-004 by intent? No — COMP-004 checks completeness
    (is the field populated?). CONS-001 checks business consistency
    (does a purchase event make sense without an order ID?).
    The two rules fire together and reinforce each other in the report.
    """
    txn    = df_events[df_events["event"] == "transaction"]
    total  = len(txn)
    failed = int(txn["transactionid"].isna().sum())
    return _result(
        run_id, "CONS-001",
        "transaction event must always have a transactionid",
        "consistency", "critical", total, failed,
    )


def check_non_transaction_has_id(df_events, run_id):
    """
    CONS-002 | High
    view and addtocart events must never have a transactionid.
    Business risk: non-purchase events tagged with order IDs corrupt
    transaction counts and revenue attribution.
    """
    non_txn = df_events[df_events["event"].isin(["view", "addtocart"])]
    total   = len(non_txn)
    failed  = int(non_txn["transactionid"].notna().sum())
    return _result(
        run_id, "CONS-002",
        "view and addtocart events must not have a transactionid",
        "consistency", "high", total, failed,
    )


def check_transaction_without_prior_activity(df_events, run_id):
    """
    CONS-003 | Medium | Heuristic — NOT a definitive failure

    Flags visitors whose first recorded event is a transaction with no
    preceding view or addtocart in the dataset.

    This is a heuristic signal, not a hard rule. Legitimate false positives:
      - Guest checkout: user browsed anonymously then checked out under a
        different session/device, so browse events appear under a different
        visitorid.
      - API-driven orders: orders placed via mobile app or external
        integrations that bypass the web tracking layer entirely.
      - External order import: ERP or POS orders imported into the event
        log without corresponding browse events.
      - Direct purchase flows: deep-linked or affiliate URLs that land
        users on a checkout page, skipping product discovery.

    A WARN here warrants human investigation, not automatic rejection.
    Returns status="WARN" (medium severity) — pipeline continues and the
    issue is surfaced for analyst review.

    Method: sort events per visitor by timestamp, find the first event
    per visitor, flag those where the first event is 'transaction'.
    """
    # Work only on rows with a valid visitorid and valid timestamp
    valid = df_events[
        df_events["visitorid"].notna() & df_events["timestamp"].notna()
    ].copy()

    total = valid["visitorid"].nunique()

    if total == 0:
        return _result(run_id, "CONS-003",
                       "transaction must not be the first event for a visitor",
                       "consistency", "medium", len(df_events), 0)

    # First event per visitor
    first_events = (
        valid.sort_values("timestamp")
             .groupby("visitorid", sort=False)["event"]
             .first()
    )
    failed = int((first_events == "transaction").sum())

    return _result(
        run_id, "CONS-003",
        "transaction must not be the first event for a visitor",
        "consistency", "medium", total, failed,
    )


# ---------------------------------------------------------------------------
# FRESHNESS (2 checks)
# Business context: stale data means dashboards display outdated metrics;
# gaps indicate pipeline outages that may have caused data loss.
# ---------------------------------------------------------------------------

def check_data_freshness(df_events, run_id):
    """
    FRESH-001 | High
    The latest event timestamp must fall within the dataset observation
    window (2015-05-01 to 2015-09-30).
    If the latest event is outside this window, the dataset may be
    stale, misdated, or incorrectly loaded.

    total_records is set to 1 (one "freshness check" result, not a
    per-row count) so failure_pct is meaningful: 0% = fresh, 100% = stale.
    """
    valid_ts = df_events["timestamp"].dropna()

    if valid_ts.empty:
        return _result(run_id, "FRESH-001",
                       "latest event must be within the observation window",
                       "freshness", "high", 1, 1)

    latest_ts = valid_ts.max()
    is_stale  = int(latest_ts < WINDOW_START_MS or latest_ts > WINDOW_END_MS)

    return _result(
        run_id, "FRESH-001",
        "latest event timestamp must be within the observation window",
        "freshness", "high", 1, is_stale,
    )


def check_timestamp_gap(df_events, run_id):
    """
    FRESH-002 | Medium
    No gap of more than 7 consecutive calendar days with zero events.
    A 7-day gap suggests a pipeline outage or missed ingestion window.

    Method: convert timestamps to dates, build a full date range between
    min and max event date, count events per day, find the longest run
    of consecutive zero-event days.

    total_records = number of days in the observation period.
    failed_records = number of zero-event days inside the longest gap
                     (0 if no gap >= 7 days).
    """
    valid_ts = df_events["timestamp"].dropna()

    if valid_ts.empty:
        return _result(run_id, "FRESH-002",
                       "no timestamp gap greater than 7 consecutive days",
                       "freshness", "medium", 1, 0)

    # Convert ms to date
    dates = pd.to_datetime(valid_ts, unit="ms").dt.date
    min_date, max_date = dates.min(), dates.max()

    full_range = pd.date_range(start=min_date, end=max_date, freq="D").date
    total_days = len(full_range)

    events_per_day = dates.value_counts()
    zero_days      = [d for d in full_range if d not in events_per_day.index]

    # Find longest consecutive run of zero-event days
    longest_gap = _longest_consecutive_run(sorted(zero_days))

    failed = longest_gap if longest_gap >= 7 else 0

    result = _result(
        run_id, "FRESH-002",
        "no gap greater than 7 consecutive days with zero events",
        "freshness", "medium", total_days, failed,
    )
    # Extra field for human-readable reporting — not part of the standard contract
    result["gap_days"] = longest_gap
    return result


# ---------------------------------------------------------------------------
# REFERENTIAL INTEGRITY (2 checks)
# Business context: orphaned foreign keys break joins, produce NULL gaps
# in reports, and cause silent under-counting.
# ---------------------------------------------------------------------------

def check_items_not_in_catalog(df_events, df_items, run_id):
    """
    RI-001 | High
    Every itemid in events must exist in item_properties.
    Business risk: events reference products with no catalogue entry.
    Category, revenue, and recommendation reports will have gaps.

    df_items must have an 'itemid' column (the known product catalog).
    """
    total = len(df_events)

    # Work only on rows with a valid itemid
    valid_events = df_events[df_events["itemid"].notna()].copy()

    known_items = set(df_items["itemid"].dropna().unique())
    orphaned    = (~valid_events["itemid"].isin(known_items)).sum()
    failed      = int(orphaned)

    return _result(
        run_id, "RI-001",
        "every itemid in events must exist in the product catalogue",
        "referential_integrity", "high", total, failed,
    )


def check_categories_not_in_tree(df_items, df_categories, run_id):
    """
    RI-002 | High
    Every categoryid in item_properties must exist in category_tree.
    Business risk: products reference categories that do not exist
    in the hierarchy. Category-level revenue rollups are broken.

    df_items must have a 'categoryid' column.
    df_categories must have a 'categoryid' column.
    """
    items_with_cat = df_items[df_items["categoryid"].notna()]
    total          = len(items_with_cat)

    if total == 0:
        return _result(run_id, "RI-002",
                       "every categoryid in item_properties must exist in category_tree",
                       "referential_integrity", "high", 0, 0)

    known_cats = set(df_categories["categoryid"].dropna().unique())
    orphaned   = (~items_with_cat["categoryid"].isin(known_cats)).sum()
    failed     = int(orphaned)

    return _result(
        run_id, "RI-002",
        "every categoryid in item_properties must exist in category_tree",
        "referential_integrity", "high", total, failed,
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_checks(df_events, df_items, df_categories, run_id):
    """
    Execute all 16 checks in order.
    Returns a list of result dicts, one per check.
    """
    results = []

    # Completeness
    results.append(check_null_visitorid(df_events, run_id))
    results.append(check_null_itemid(df_events, run_id))
    results.append(check_null_event(df_events, run_id))
    results.append(check_missing_transactionid_on_transaction(df_events, run_id))

    # Uniqueness
    results.append(check_duplicate_transactionid(df_events, run_id))
    results.append(check_duplicate_event_rows(df_events, run_id))

    # Validity
    results.append(check_invalid_event_type(df_events, run_id))
    results.append(check_timestamp_out_of_range(df_events, run_id))
    results.append(check_invalid_itemid(df_events, run_id))

    # Consistency
    results.append(check_transaction_missing_id(df_events, run_id))
    results.append(check_non_transaction_has_id(df_events, run_id))
    results.append(check_transaction_without_prior_activity(df_events, run_id))

    # Freshness
    results.append(check_data_freshness(df_events, run_id))
    results.append(check_timestamp_gap(df_events, run_id))

    # Referential Integrity
    results.append(check_items_not_in_catalog(df_events, df_items, run_id))
    results.append(check_categories_not_in_tree(df_items, df_categories, run_id))

    return results


# ---------------------------------------------------------------------------
# Private utility
# ---------------------------------------------------------------------------

def _longest_consecutive_run(sorted_dates):
    """Return the length of the longest consecutive sequence in a sorted list of dates."""
    if not sorted_dates:
        return 0

    max_run = 1
    cur_run = 1

    for i in range(1, len(sorted_dates)):
        delta = (sorted_dates[i] - sorted_dates[i - 1]).days
        if delta == 1:
            cur_run += 1
            max_run = max(max_run, cur_run)
        else:
            cur_run = 1

    return max_run

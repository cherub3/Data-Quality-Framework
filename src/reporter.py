"""
reporter.py
-----------
Generates a human-readable plain-text validation report.

Output: reports/validation_report_{dataset}_{timestamp}.txt

Report structure:
  1. Header            — dataset, run time, record count
  2. Quality Score     — numeric score, status, pass/fail/warn counts
  3. Severity Summary  — critical / high / medium / low failure counts
  4. TOP 5 ISSUES      — ranked by severity then failure %, near the top
  5. Dimension Scores  — score per dimension with a visual bar
  6. All Check Results — grouped by dimension, with status and failure %
  7. Recommendations   — one action per failed check
  8. Footer            — data trust verdict
"""

from datetime import datetime
from pathlib import Path
from config import REPORTS_DIR

# ---------------------------------------------------------------------------
# Business impact and recommendation text — one entry per rule_id.
# Keeping these as constants here means the reporter is self-contained.
# ---------------------------------------------------------------------------

BUSINESS_IMPACT = {
    "COMP-001": "User behaviour cannot be attributed. Marketing and funnel reports become unreliable.",
    "COMP-002": "Affected events cannot be linked to any product. Revenue and catalogue reports break.",
    "COMP-003": "Event type is unknown. Funnel analysis includes unclassifiable rows.",
    "COMP-004": "Purchase events have no order reference. Fulfilment, refunds, and revenue tracking fail.",
    "UNIQ-001": "Revenue is double-counted. Finance reports will overstate sales figures.",
    "UNIQ-002": "Duplicate rows inflate event counts and distort conversion rates.",
    "VALID-001": "Unrecognised event types corrupt funnel metrics and recommendation models.",
    "VALID-002": "Out-of-range timestamps corrupt trend charts and time-based aggregations.",
    "VALID-003": "Invalid item IDs cannot be joined to the product catalogue.",
    "CONS-001": "Purchases without order IDs cannot be traced, reconciled, or refunded.",
    "CONS-002": "Non-purchase events incorrectly tagged with order IDs corrupt transaction counts.",
    "CONS-003": "First event is a purchase with no prior browsing — likely a tracking or ingestion error.",
    "FRESH-001": "Dataset is outside its expected date range — may be stale or incorrectly loaded.",
    "FRESH-002": "A gap of 7+ days with no events suggests a pipeline outage or missed ingestion.",
    "RI-001":   "Events reference products that do not exist in the catalogue. Category and revenue rollups will have gaps.",
    "RI-002":   "Products reference categories that do not exist in the hierarchy. Category-level reporting is broken.",
}

RECOMMENDATIONS = {
    "COMP-001": "Investigate upstream event tracking. Ensure visitorid is set before events are fired.",
    "COMP-002": "Check the event collection pipeline for missing itemid fields.",
    "COMP-003": "Validate event payloads at ingestion. Reject records without an event type.",
    "COMP-004": "Ensure the checkout system always writes a transactionid before committing the event.",
    "UNIQ-001": "Deduplicate on transactionid before loading into the reporting layer.",
    "UNIQ-002": "Add a deduplication step at ingestion. Investigate the source of duplicate events.",
    "VALID-001": "Enforce an event type allowlist at the collection layer. Alert on unknown values.",
    "VALID-002": "Validate timestamps at ingestion. Filter or quarantine out-of-range records.",
    "VALID-003": "Validate itemid is a positive integer before writing to the event store.",
    "CONS-001": "Block transaction events from entering the pipeline without a confirmed transactionid.",
    "CONS-002": "Strip transactionid from non-transaction events at the source.",
    "CONS-003": "Investigate affected visitors for session tracking gaps or bot activity.",
    "FRESH-001": "Verify the ingestion job ran for the expected date range. Re-run if data is missing.",
    "FRESH-002": "Check pipeline logs for the gap period. Identify whether data was lost or delayed.",
    "RI-001":   "Backfill missing products in the catalogue or filter orphaned events before reporting.",
    "RI-002":   "Sync the category tree with the product catalogue. Remove or remap orphaned category IDs.",
}

# Severity sort order for ranking
_SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_report(all_results, scored_result, dataset_name, run_timestamp, total_records):
    """
    Write a plain-text validation report to reports/ and return the file path.

    Parameters
    ----------
    all_results    : list of check result dicts (from checks.py)
    scored_result  : dict from scorer.calculate_quality_score()
    dataset_name   : str
    run_timestamp  : datetime
    total_records  : int
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    ts_str    = run_timestamp.strftime("%Y%m%d_%H%M%S")
    filename  = f"validation_report_{dataset_name}_{ts_str}.txt"
    filepath  = REPORTS_DIR / filename

    lines = _build_report(all_results, scored_result, dataset_name, run_timestamp, total_records)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def _build_report(all_results, scored_result, dataset_name, run_timestamp, total_records):
    lines = []
    W = 70  # report width

    def rule():
        lines.append("=" * W)

    def divider():
        lines.append("-" * W)

    def section(title):
        lines.append("")
        lines.append(f"  {title.upper()}")
        divider()

    # ------------------------------------------------------------------
    # 1. Header
    # ------------------------------------------------------------------
    rule()
    lines.append("  DATA QUALITY VALIDATION REPORT")
    rule()
    lines.append(f"  Dataset        : {dataset_name}")
    lines.append(f"  Run Timestamp  : {run_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Total Records  : {total_records:,}")
    lines.append(f"  Report Version : 1.0")

    # ------------------------------------------------------------------
    # 2. Quality Score
    # ------------------------------------------------------------------
    section("Quality Score")
    score  = scored_result["quality_score"]
    status = scored_result["status"]
    status_label = _status_label(status)

    lines.append(f"  Overall Score  : {score:.1f} / 100")
    lines.append(f"  Status         : {status_label}")
    lines.append("")
    lines.append(f"  Checks Passed  : {scored_result['pass_count']}")
    lines.append(f"  Checks Failed  : {scored_result['fail_count']}")
    lines.append(f"  Checks Warned  : {scored_result['warn_count']}")
    lines.append(f"  Total Checks   : {len(all_results)}")

    # ------------------------------------------------------------------
    # 3. Severity Summary
    # ------------------------------------------------------------------
    section("Severity Summary")
    lines.append(f"  Critical Failures : {scored_result['critical_failures']}")
    lines.append(f"  High Failures     : {scored_result['high_failures']}")
    lines.append(f"  Medium Warnings   : {scored_result['medium_failures']}")
    lines.append(f"  Low Warnings      : {scored_result['low_failures']}")

    if scored_result["has_critical_failure"]:
        lines.append("")
        lines.append("  [!] CRITICAL OVERRIDE ACTIVE")
        lines.append("      One or more Critical checks failed. Dataset status has been")
        lines.append("      downgraded regardless of the aggregate numeric score.")
        lines.append("      Do not use this dataset for business reporting until resolved.")

    # ------------------------------------------------------------------
    # 4. Top 5 Most Impactful Issues
    # ------------------------------------------------------------------
    failed_results = [r for r in all_results if r["status"] in ("FAIL", "WARN")]
    if failed_results:
        section("Top 5 Most Impactful Issues")
        ranked = sorted(
            failed_results,
            key=lambda r: (_SEVERITY_RANK.get(r["severity"], 9), -r["failure_pct"]),
        )
        for i, r in enumerate(ranked[:5], 1):
            impact = BUSINESS_IMPACT.get(r["rule_id"], "")
            lines.append(f"  {i}. [{r['severity'].upper()}] {r['rule_id']} — {r['rule_desc']}")
            lines.append(f"     Failed records : {r['failed_records']:,} ({r['failure_pct']:.2f}%)")
            if r["rule_id"] == "FRESH-002" and "gap_days" in r:
                gap = r["gap_days"]
                lines.append(f"     Gap Detected   : {'Yes' if gap >= 7 else 'No'}")
                lines.append(f"     Gap Length     : {gap:,} Days")
            lines.append(f"     Business risk  : {impact}")
            lines.append("")

    # ------------------------------------------------------------------
    # 5. Dimension Scores
    # ------------------------------------------------------------------
    section("Dimension Scores")
    ds = scored_result["dimension_scores"]
    dim_order = [
        ("completeness",          "Completeness         (20%)"),
        ("uniqueness",            "Uniqueness           (20%)"),
        ("validity",              "Validity             (20%)"),
        ("consistency",           "Consistency          (20%)"),
        ("freshness",             "Freshness            (10%)"),
        ("referential_integrity", "Referential Integrity(10%)"),
    ]
    for key, label in dim_order:
        score_d = ds.get(key, 100.0)
        bar     = _score_bar(score_d)
        lines.append(f"  {label}  {score_d:5.1f}  {bar}")

    # ------------------------------------------------------------------
    # 6. All Check Results (grouped by dimension)
    # ------------------------------------------------------------------
    section("All Check Results")
    by_dim = {}
    for r in all_results:
        by_dim.setdefault(r["dimension"], []).append(r)

    dim_display_order = [
        "completeness", "uniqueness", "validity",
        "consistency", "freshness", "referential_integrity",
    ]
    for dim in dim_display_order:
        if dim not in by_dim:
            continue
        lines.append(f"\n  [{dim.upper().replace('_', ' ')}]")
        for r in by_dim[dim]:
            icon = _status_icon(r["status"])
            lines.append(
                f"    {icon} {r['rule_id']:<10}  "
                f"{r['severity']:<8}  "
                f"{r['status']:<4}  "
                f"{r['failed_records']:>8,} failed  "
                f"({r['failure_pct']:.2f}%)"
            )
            lines.append(f"          {r['rule_desc']}")
            # FRESH-002 extra: show gap length in plain language
            if r["rule_id"] == "FRESH-002" and "gap_days" in r:
                gap = r["gap_days"]
                detected = "Yes" if gap >= 7 else "No"
                lines.append(f"          Gap Detected : {detected}")
                lines.append(f"          Gap Length   : {gap:,} Days")

    # ------------------------------------------------------------------
    # 7. Recommendations
    # ------------------------------------------------------------------
    failed_or_warned = [r for r in all_results if r["status"] in ("FAIL", "WARN")]
    if failed_or_warned:
        section("Recommendations")
        ranked_recs = sorted(
            failed_or_warned,
            key=lambda r: (_SEVERITY_RANK.get(r["severity"], 9), -r["failure_pct"]),
        )
        for r in ranked_recs:
            rec = RECOMMENDATIONS.get(r["rule_id"], "Investigate and resolve.")
            lines.append(f"  [{r['severity'].upper()}] {r['rule_id']} — {r['rule_desc']}")
            lines.append(f"    Action : {rec}")
            lines.append("")

    # ------------------------------------------------------------------
    # 8. Footer — Data Trust Verdict
    # ------------------------------------------------------------------
    rule()
    lines.append("  DATA TRUST VERDICT")
    rule()
    verdict = _trust_verdict(scored_result)
    for line in verdict:
        lines.append(f"  {line}")
    lines.append("")
    lines.append(f"  Report generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    rule()

    return lines


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _score_bar(score, width=20):
    """Visual progress bar for a 0–100 score."""
    filled = int(round(score / 100 * width))
    return "[" + "#" * filled + "." * (width - filled) + "]"


def _status_icon(status):
    return {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}.get(status, "[????]")


def _status_label(status):
    labels = {
        "Excellent": "Excellent  -- Data is trustworthy for all reporting",
        "Good":      "Good       -- Data is suitable for most reporting",
        "Warning":   "Warning    -- Data has issues; use with caution",
        "Critical":  "Critical   -- Data should NOT be used for reporting",
    }
    return labels.get(status, status)


def _trust_verdict(scored_result):
    status = scored_result["status"]
    score  = scored_result["quality_score"]
    crit   = scored_result["critical_failures"]

    if status == "Excellent":
        return [
            f"Score {score:.1f}/100 — TRUSTWORTHY",
            "This dataset passes all critical checks and is safe for",
            "business reporting, dashboard refresh, and downstream pipelines.",
        ]
    if status == "Good":
        return [
            f"Score {score:.1f}/100 — MOSTLY TRUSTWORTHY",
            "This dataset is suitable for most analyses. Minor issues were",
            "detected. Review the recommendations and remediate before",
            "publishing to executive dashboards.",
        ]
    if status == "Warning":
        return [
            f"Score {score:.1f}/100 — USE WITH CAUTION",
            f"Critical failures detected: {crit}.",
            "Some metrics derived from this dataset will be incorrect.",
            "Resolve all Critical and High issues before using for reporting.",
        ]
    return [
        f"Score {score:.1f}/100 — DO NOT USE",
        f"Critical failures detected: {crit}.",
        "This dataset has serious data quality problems. Using it for",
        "reporting will produce incorrect business metrics. Block this",
        "dataset from all downstream consumers until issues are resolved.",
    ]

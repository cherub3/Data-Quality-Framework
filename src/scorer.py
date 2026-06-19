"""
scorer.py
---------
Aggregates check results into a quality score.

Scoring logic:
  1. Group check results by dimension
  2. Per dimension: start at 100, subtract SEVERITY_PENALTIES for each
     FAIL or WARN result. Clamp to [0, 100].
  3. Final score = weighted average of all dimension scores
     using DIMENSION_WEIGHTS from config.
  4. Critical override: if any Critical check is FAIL, the dataset
     status cannot be Excellent or Good regardless of numeric score.

Returns a scored_result dict:
  quality_score         float  0–100
  status                str    Excellent | Good | Warning | Critical
  dimension_scores      dict   {dimension: score}
  pass_count            int
  fail_count            int
  warn_count            int
  has_critical_failure  bool
"""

from config import (
    DIMENSION_WEIGHTS,
    SEVERITY_PENALTIES,
    STATUS_EXCELLENT,
    STATUS_GOOD,
    STATUS_WARNING,
)


def calculate_dimension_score(results_for_dimension):
    """
    Given a list of check results for one dimension, return a score 0–100.

    Each FAIL or WARN deducts SEVERITY_PENALTIES[severity] points.
    Score is clamped to 0 (cannot go negative).
    """
    score = 100.0
    for r in results_for_dimension:
        if r["status"] in ("FAIL", "WARN"):
            penalty = SEVERITY_PENALTIES.get(r["severity"], 0)
            score  -= penalty
    return max(0.0, score)


def calculate_quality_score(all_results):
    """
    Given the full list of 16 check results, compute and return a
    scored_result dict.
    """
    # Group results by dimension
    by_dimension = {}
    for r in all_results:
        dim = r["dimension"]
        by_dimension.setdefault(dim, []).append(r)

    # Score each dimension
    dimension_scores = {}
    for dim, results in by_dimension.items():
        dimension_scores[dim] = calculate_dimension_score(results)

    # Ensure every expected dimension has a score (default 100 if no checks ran)
    for dim in DIMENSION_WEIGHTS:
        dimension_scores.setdefault(dim, 100.0)

    # Weighted average
    quality_score = sum(
        dimension_scores[dim] * weight
        for dim, weight in DIMENSION_WEIGHTS.items()
    )
    quality_score = round(quality_score, 2)

    # Count statuses
    pass_count = sum(1 for r in all_results if r["status"] == "PASS")
    fail_count = sum(1 for r in all_results if r["status"] == "FAIL")
    warn_count = sum(1 for r in all_results if r["status"] == "WARN")

    # Severity breakdown counts (failed/warned checks only)
    non_pass = [r for r in all_results if r["status"] in ("FAIL", "WARN")]
    critical_failures = sum(1 for r in non_pass if r["severity"] == "critical")
    high_failures     = sum(1 for r in non_pass if r["severity"] == "high")
    medium_failures   = sum(1 for r in non_pass if r["severity"] == "medium")
    low_failures      = sum(1 for r in non_pass if r["severity"] == "low")

    # Critical override flag
    has_critical_failure = any(
        r["status"] == "FAIL" and r["severity"] == "critical"
        for r in all_results
    )

    status = determine_status(quality_score, has_critical_failure)

    return {
        "quality_score":        quality_score,
        "status":               status,
        "dimension_scores":     dimension_scores,
        "pass_count":           pass_count,
        "fail_count":           fail_count,
        "warn_count":           warn_count,
        "critical_failures":    critical_failures,
        "high_failures":        high_failures,
        "medium_failures":      medium_failures,
        "low_failures":         low_failures,
        "has_critical_failure": has_critical_failure,
    }


def determine_status(score, has_critical_failure):
    """
    Map a numeric score and critical-failure flag to a status label.

    Critical override rule:
      Any critical failure forces status to Warning or worse,
      even if the numeric score is high.

    This mirrors real-world data quality tools where a Critical issue
    always blocks data from being considered trustworthy regardless of
    the aggregate score.
    """
    if has_critical_failure:
        # Critical failure: score decides between Warning and Critical
        if score >= STATUS_WARNING:
            return "Warning"
        return "Critical"

    if score >= STATUS_EXCELLENT:
        return "Excellent"
    if score >= STATUS_GOOD:
        return "Good"
    if score >= STATUS_WARNING:
        return "Warning"
    return "Critical"

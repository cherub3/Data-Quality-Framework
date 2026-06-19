"""
test_scorer.py
--------------
Unit tests for scorer.py.

Run with:
  python -m pytest tests/ -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scorer import calculate_quality_score, calculate_dimension_score, determine_status


def _result(rule_id, dimension, severity, status, failed=0, total=100):
    return {
        "run_id":         "test",
        "rule_id":        rule_id,
        "rule_desc":      rule_id,
        "dimension":      dimension,
        "severity":       severity,
        "status":         status,
        "total_records":  total,
        "failed_records": failed,
        "failure_pct":    round(failed / total * 100, 2) if total > 0 else 0.0,
    }


class TestDimensionScore:

    def test_all_pass_scores_100(self):
        results = [
            _result("COMP-001", "completeness", "critical", "PASS"),
            _result("COMP-002", "completeness", "critical", "PASS"),
        ]
        assert calculate_dimension_score(results) == 100.0

    def test_critical_fail_deducts_25(self):
        results = [_result("COMP-001", "completeness", "critical", "FAIL", failed=5)]
        assert calculate_dimension_score(results) == 75.0

    def test_high_fail_deducts_15(self):
        results = [_result("RI-001", "referential_integrity", "high", "FAIL", failed=10)]
        assert calculate_dimension_score(results) == 85.0

    def test_medium_warn_deducts_8(self):
        results = [_result("CONS-003", "consistency", "medium", "WARN", failed=3)]
        assert calculate_dimension_score(results) == 92.0

    def test_score_clamps_at_zero(self):
        """Multiple critical failures cannot push score below 0."""
        results = [
            _result("COMP-001", "completeness", "critical", "FAIL"),
            _result("COMP-002", "completeness", "critical", "FAIL"),
            _result("COMP-003", "completeness", "critical", "FAIL"),
            _result("COMP-004", "completeness", "critical", "FAIL"),
            _result("UNIQ-001", "completeness", "critical", "FAIL"),
        ]
        assert calculate_dimension_score(results) == 0.0


class TestQualityScore:

    def test_all_pass_gives_100(self):
        dims = ["completeness", "uniqueness", "validity",
                "consistency", "freshness", "referential_integrity"]
        results = [_result(f"R-{i}", d, "high", "PASS") for i, d in enumerate(dims)]
        scored = calculate_quality_score(results)
        assert scored["quality_score"] == 100.0
        assert scored["status"] == "Excellent"
        assert scored["pass_count"] == len(dims)
        assert scored["fail_count"] == 0
        assert scored["critical_failures"] == 0

    def test_critical_failure_overrides_status(self):
        """Even with a high aggregate score, one Critical FAIL forces Warning."""
        dims = ["completeness", "uniqueness", "validity",
                "consistency", "freshness", "referential_integrity"]
        results = [_result(f"R-{i}", d, "high", "PASS") for i, d in enumerate(dims)]
        # Replace one with a Critical FAIL
        results[0] = _result("COMP-001", "completeness", "critical", "FAIL", failed=1)
        scored = calculate_quality_score(results)
        assert scored["has_critical_failure"] is True
        assert scored["status"] in ("Warning", "Critical")

    def test_severity_counts_correct(self):
        results = [
            _result("COMP-001", "completeness",  "critical", "FAIL"),
            _result("UNIQ-001", "uniqueness",     "critical", "FAIL"),
            _result("RI-001",   "referential_integrity", "high", "FAIL"),
            _result("CONS-003", "consistency",    "medium", "WARN"),
            _result("COMP-002", "completeness",   "critical", "PASS"),
        ]
        scored = calculate_quality_score(results)
        assert scored["critical_failures"] == 2
        assert scored["high_failures"]     == 1
        assert scored["medium_failures"]   == 1
        assert scored["low_failures"]      == 0


class TestDetermineStatus:

    def test_score_95_no_critical_is_excellent(self):
        assert determine_status(95.0, False) == "Excellent"

    def test_score_80_no_critical_is_good(self):
        assert determine_status(80.0, False) == "Good"

    def test_score_65_no_critical_is_warning(self):
        assert determine_status(65.0, False) == "Warning"

    def test_score_50_no_critical_is_critical(self):
        assert determine_status(50.0, False) == "Critical"

    def test_score_95_with_critical_is_warning(self):
        """Critical override: high score + critical failure = Warning, not Excellent."""
        assert determine_status(95.0, True) == "Warning"

    def test_score_45_with_critical_is_critical(self):
        assert determine_status(45.0, True) == "Critical"

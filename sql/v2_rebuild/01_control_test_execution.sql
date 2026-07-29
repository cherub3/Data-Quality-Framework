-- 01_control_test_execution.sql
-- Rebuilds the PASS/FAIL classification for every control test from first
-- principles: join each test result to its rule's threshold and compare
-- the measured control_effectiveness against it directly in SQL.
--
-- Expected: 1,350 rows (30 days x ~45 applicable controls/day, varies by
-- which of the 30 controls apply to each of the 13 datasets).

SELECT
    r.test_id,
    r.test_date,
    r.dataset_id,
    di.dataset_name,
    r.rule_id,
    cr.rule_name,
    cr.category,
    r.total_records,
    r.pass_count,
    r.fail_count,
    r.failure_rate,
    r.control_effectiveness,
    cr.threshold,
    CASE
        WHEN r.control_effectiveness >= cr.threshold THEN 'Pass'
        ELSE 'Fail'
    END AS status_v2,
    r.status AS status_v1,
    CASE
        WHEN r.status = CASE WHEN r.control_effectiveness >= cr.threshold THEN 'Pass' ELSE 'Fail' END
        THEN TRUE ELSE FALSE
    END AS reconciled
FROM control_test_results r
JOIN control_rulebook cr ON cr.rule_id = r.rule_id
JOIN data_inventory di ON di.dataset_id = r.dataset_id
ORDER BY r.test_date, r.dataset_id, r.rule_id;

-- Reconciliation check: run this second query to confirm 0 mismatches.
-- SELECT count(*) AS mismatches
-- FROM control_test_results r
-- JOIN control_rulebook cr ON cr.rule_id = r.rule_id
-- WHERE r.status != CASE WHEN r.control_effectiveness >= cr.threshold THEN 'Pass' ELSE 'Fail' END;

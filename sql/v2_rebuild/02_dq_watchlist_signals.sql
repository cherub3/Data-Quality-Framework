-- 02_dq_watchlist_signals.sql
-- Rebuilds the early-warning watchlist classification as a snapshot query
-- (dq_watchlist stores one row per dataset -- a point-in-time snapshot,
-- NOT 30 days of daily history -- so this reproduces that same shape:
-- 13 rows, one per dataset).
--
-- Important, honest limitation: null_rate and duplicate_rate in the source
-- system are simulated per-dataset baselines with random noise -- they are
-- NOT derived from scanning any real column for nulls/duplicates, so they
-- cannot be recomputed from control_test_results or any other table here.
-- This query recomputes the one signal that IS derivable from raw data --
-- control_failure_trend, from the real failure_rate history in
-- control_test_results -- and carries the other two trends through from the
-- stored dq_watchlist snapshot as given inputs. See SQL_COMPARISON.md.
--
-- Expected: 13 rows.

WITH bounds AS (
    SELECT max(test_date) AS max_date FROM control_test_results
),
split AS (
    SELECT r.*, (SELECT max_date FROM bounds) - INTERVAL 15 DAY AS cutoff
    FROM control_test_results r
),
period_agg AS (
    SELECT
        dataset_id,
        avg(failure_rate) FILTER (WHERE test_date <= cutoff)  AS control_failure_rate_early,
        avg(failure_rate) FILTER (WHERE test_date >  cutoff)  AS control_failure_rate_recent
    FROM split
    GROUP BY dataset_id
),
trend AS (
    SELECT
        p.dataset_id,
        p.control_failure_rate_early,
        p.control_failure_rate_recent,
        ((p.control_failure_rate_recent - p.control_failure_rate_early)
            / greatest(p.control_failure_rate_early, 0.01)) * 100 AS control_failure_delta
    FROM period_agg p
),
classified AS (
    SELECT
        t.dataset_id,
        di.dataset_name,
        di.domain,
        di.regulatory_criticality,
        t.control_failure_rate_early,
        t.control_failure_rate_recent,
        CASE
            WHEN t.control_failure_delta > 10 THEN 'Deteriorating'
            WHEN t.control_failure_delta < -10 THEN 'Improving'
            ELSE 'Stable'
        END AS control_failure_trend_v2,
        w.null_rate_trend,
        w.duplicate_rate_trend,
        w.control_failure_trend AS control_failure_trend_v1,
        w.watchlist_status AS watchlist_status_v1
    FROM trend t
    JOIN data_inventory di ON di.dataset_id = t.dataset_id
    JOIN dq_watchlist w ON w.dataset_id = t.dataset_id
),
counted AS (
    SELECT
        *,
        (CASE WHEN null_rate_trend = 'Deteriorating' THEN 1 ELSE 0 END
       + CASE WHEN duplicate_rate_trend = 'Deteriorating' THEN 1 ELSE 0 END
       + CASE WHEN control_failure_trend_v2 = 'Deteriorating' THEN 1 ELSE 0 END) AS det_count,
        (CASE WHEN null_rate_trend = 'Improving' THEN 1 ELSE 0 END
       + CASE WHEN duplicate_rate_trend = 'Improving' THEN 1 ELSE 0 END
       + CASE WHEN control_failure_trend_v2 = 'Improving' THEN 1 ELSE 0 END) AS imp_count
    FROM classified
)
SELECT
    dataset_id,
    dataset_name,
    domain,
    regulatory_criticality,
    control_failure_rate_early,
    control_failure_rate_recent,
    control_failure_trend_v2,
    control_failure_trend_v1,
    det_count,
    imp_count,
    CASE
        WHEN det_count >= 2 THEN 'Watchlist'
        WHEN det_count = 1 THEN 'Monitor'
        WHEN imp_count >= 2 THEN 'Clear'
        ELSE 'Clear'
    END AS watchlist_status_v2,
    watchlist_status_v1,
    CASE
        WHEN (CASE
                WHEN det_count >= 2 THEN 'Watchlist'
                WHEN det_count = 1 THEN 'Monitor'
                WHEN imp_count >= 2 THEN 'Clear'
                ELSE 'Clear'
              END) = watchlist_status_v1
        THEN TRUE ELSE FALSE
    END AS reconciled
FROM counted
ORDER BY dataset_id;

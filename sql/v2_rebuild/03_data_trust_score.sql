-- 03_data_trust_score.sql
-- Rebuilds the Data Trust Score per domain and for the enterprise overall.
-- Formula: trust_score = clamp(avg_control_effectiveness_7d
--                               - 3 * watchlist_count
--                               - 1 * monitor_count, 0, 100)
-- Category: Trusted >= 90, Monitor >= 75, else At Risk.
--
-- Expected: 10 rows (9 domains + 1 "Enterprise (Overall)" summary row).

WITH bounds AS (
    SELECT max(test_date) AS max_date FROM control_test_results
),
recent_tests AS (
    SELECT r.*, di.domain
    FROM control_test_results r
    JOIN data_inventory di ON di.dataset_id = r.dataset_id
    -- NOTE: >= (not >) is deliberate. v1 (pipeline.py) builds its "last 7 days"
    -- window inclusively, giving 8 distinct test_dates. Using > here yields a
    -- 7-date window and shifts every domain score by up to 0.2 points. See
    -- SQL_COMPARISON.md, file 03, for the reconciliation trace.
    WHERE r.test_date >= (SELECT max_date FROM bounds) - INTERVAL 7 DAY
),
domain_eff AS (
    SELECT domain, avg(control_effectiveness) AS avg_control_effectiveness
    FROM recent_tests
    GROUP BY domain
),
domain_watch AS (
    SELECT
        di.domain,
        count(*) FILTER (WHERE w.watchlist_status = 'Watchlist') AS watchlist_count,
        count(*) FILTER (WHERE w.watchlist_status = 'Monitor')   AS monitor_count
    FROM dq_watchlist w
    JOIN data_inventory di ON di.dataset_id = w.dataset_id
    GROUP BY di.domain
),
domain_scores AS (
    SELECT
        e.domain,
        e.avg_control_effectiveness,
        coalesce(wc.watchlist_count, 0) AS watchlist_count,
        coalesce(wc.monitor_count, 0)   AS monitor_count,
        least(greatest(
            e.avg_control_effectiveness
                - 3 * coalesce(wc.watchlist_count, 0)
                - 1 * coalesce(wc.monitor_count, 0),
        0), 100) AS trust_score,
        (SELECT count(*) FROM data_inventory di2 WHERE di2.domain = e.domain) AS dataset_count
    FROM domain_eff e
    LEFT JOIN domain_watch wc ON wc.domain = e.domain
),
enterprise AS (
    SELECT
        'Enterprise (Overall)' AS domain,
        avg(avg_control_effectiveness) AS avg_control_effectiveness,
        NULL::BIGINT AS watchlist_count,
        NULL::BIGINT AS monitor_count,
        avg(trust_score) AS trust_score,
        (SELECT count(*) FROM data_inventory) AS dataset_count
    FROM domain_scores
)
SELECT domain, round(trust_score, 1) AS trust_score,
       CASE
           WHEN trust_score >= 90 THEN 'Trusted'
           WHEN trust_score >= 75 THEN 'Monitor'
           ELSE 'At Risk'
       END AS trust_category,
       round(avg_control_effectiveness, 1) AS avg_control_effectiveness,
       dataset_count
FROM domain_scores
UNION ALL
SELECT domain, round(trust_score, 1),
       CASE
           WHEN trust_score >= 90 THEN 'Trusted'
           WHEN trust_score >= 75 THEN 'Monitor'
           ELSE 'At Risk'
       END,
       round(avg_control_effectiveness, 1),
       dataset_count
FROM enterprise
ORDER BY domain;

-- Reconciliation: compare trust_score/trust_category above row-by-row
-- against the stored domain_trust_scores table.

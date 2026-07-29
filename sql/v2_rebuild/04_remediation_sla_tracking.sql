-- 04_remediation_sla_tracking.sql
-- Rebuilds SLA classification for every remediation ticket from severity
-- alone, then flags currently-open tickets that are past their SLA date.
--
-- SLA days by severity: Critical=1, High=3, Medium=7, Low=14 (default 7).
-- sla_breach = today > sla_date AND status != 'Resolved'.
--
-- Expected: 42 rows (one per remediation ticket).

WITH sla_days AS (
    SELECT
        t.*,
        CASE t.severity
            WHEN 'Critical' THEN 1
            WHEN 'High'     THEN 3
            WHEN 'Medium'   THEN 7
            WHEN 'Low'      THEN 14
            ELSE 7
        END AS sla_threshold_days
    FROM remediation_tickets t
)
SELECT
    ticket_id,
    dataset_id,
    dataset_name,
    severity,
    status,
    open_date,
    sla_date,
    resolution_date,
    sla_threshold_days,
    date_diff('day', open_date::date, current_date) AS days_open,
    CASE
        WHEN status = 'Resolved' THEN 'ON_TIME'
        WHEN current_date > sla_date::date THEN 'OVERDUE'
        ELSE 'OPEN'
    END AS sla_status_v2,
    sla_breach AS sla_breach_v1,
    CASE
        WHEN (current_date > sla_date::date AND status != 'Resolved') = sla_breach
        THEN TRUE ELSE FALSE
    END AS reconciled,
    CASE
        WHEN current_date > sla_date::date AND status != 'Resolved'
        THEN date_diff('day', sla_date::date, current_date)
        ELSE 0
    END AS days_overdue
FROM sla_days
ORDER BY sla_breach DESC, days_overdue DESC, ticket_id;

-- Reconciliation check:
-- SELECT count(*) FROM remediation_tickets
-- WHERE sla_breach != (current_date > sla_date::date AND status != 'Resolved');

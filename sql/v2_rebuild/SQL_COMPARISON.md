# SQL v2 vs. v1: Rebuild & Reconciliation

v1 is the logic embedded in `src/pipeline.py` — Python/pandas/numpy code that simulates and classifies governance data. v2 (`sql/v2_rebuild/`) is the same classification logic rewritten from schema and formula knowledge alone, as pure SQL executed directly against the materialized tables in `data/warehouse/governance.duckdb`, without re-reading `pipeline.py`. Each file was run against the live database to reconcile row-by-row against the original stored columns.

*Figures below are from the live database and are illustrative/synthetic. The pipeline is seeded, so they reproduce exactly on re-run — only absolute dates slide. The one exception is `sla_breach` (file 04 below), which is written once per run and goes stale as real time passes; that behavior is the subject of the file-04 finding.*

## 01_control_test_execution.sql — Control PASS/FAIL

**Approach:** join `control_test_results` to `control_rulebook` on `rule_id`, compare `control_effectiveness` to `threshold` directly in SQL (`>=` → Pass, else Fail).

**Reconciliation result: exact match, 0 mismatches across all 1,350 rows.** v1's Python classification (`status = "Pass" if control_effectiveness >= threshold else "Fail"`) and v2's SQL `CASE` expression are logically identical — this file mainly demonstrates the same rule can be expressed as a single set-based join instead of a per-row Python branch, with no behavioral difference.

## 02_dq_watchlist_signals.sql — Early-Warning Watchlist Status

**Approach:** v2 recomputes the one signal that's actually derivable from raw data — `control_failure_trend`, from real `failure_rate` history in `control_test_results`, split into early/recent periods with a 15-day cutoff via a window/`FILTER` aggregation instead of v1's Python dict-based date slicing. `det_count`/`imp_count` and the final `Watchlist/Monitor/Clear` classification are then reproduced with the same threshold logic (`det_count>=2` → Watchlist, etc.).

**Honest limitation:** `null_rate` and `duplicate_rate` in the source system are *simulated* per-dataset baselines plus random noise — they are not derived from scanning any real column for actual nulls or duplicate keys. There is no table in this warehouse that stores raw row-level nulls/duplicates, so v2 cannot independently recompute those two trends from data; it carries them through from the stored `dq_watchlist` snapshot as given inputs, and only re-derives the third (control-failure) signal from raw data. This is a deliberate, disclosed scope limit, not an oversight.

**Reconciliation result: exact match, 0 mismatches across all 13 dataset rows** for both the re-derived `control_failure_trend` and the resulting `watchlist_status`.

## 03_data_trust_score.sql — Data Trust Score

**Approach:** recomputes `avg_control_effectiveness` over the trailing 7 days per domain (from `control_test_results` joined to `data_inventory`), counts Watchlist/Monitor datasets per domain from `dq_watchlist`, and applies `clamp(avg_eff - 3*watchlist_count - 1*monitor_count, 0, 100)`, plus an `Enterprise (Overall)` row as the mean across domains — using SQL aggregation/window functions instead of v1's per-domain Python loop.

**Reconciliation result: exact match, 0 differences across all 10 rows — but only after fixing a real off-by-one bug this comparison exposed.**

The first version of this query used `WHERE test_date > max_date - INTERVAL 7 DAY`, which selects **7** distinct test dates. v1 (`pipeline.py`) builds its "last 7 days" window **inclusively**, giving **8** distinct dates. That one-day difference moved 7 of the 10 domain scores — Operations by 0.2 (80.8 vs. the stored 81.0), HR/Product/Reference/Risk/Sales and the Enterprise row by 0.1 each. `trust_category` still matched 10/10, so the classification was never wrong, but the underlying scores were.

This is worth being precise about, because "off by 0.1–0.2" is easy to wave away as floating-point noise and it isn't — floating-point disagreement on this data would be on the order of 1e-14, not 1e-1. It was a genuine window-boundary defect in the v2 rewrite. Changing the predicate to `>=` reconciles all 10 rows to **exactly 0.0 difference** on `trust_score`, `trust_category`, and `avg_control_effectiveness`.

That is arguably the single most useful thing this whole rebuild exercise produced: writing the logic a second time from the schema alone surfaced an ambiguity ("what does *last 7 days* mean — 7 dates or 8?") that reading the original code would have silently carried over.

## 04_remediation_sla_tracking.sql — Remediation SLA Status

**Approach:** classify each ticket's SLA status from its severity-based threshold (Critical=1 day, High=3, Medium=7, Low=14) and compare against `sla_date`.

**Reconciliation result: 11 of 42 rows disagree with the stored `sla_breach` flag — a real, understood difference, not a bug.** v1's `sla_breach` was computed once, at the moment `pipeline.py` last ran, using Python's `datetime.today()` frozen at that instant. v2's SQL evaluates `current_date > sla_date` live, against whatever "now" is when the query runs. Every one of the 11 mismatched tickets (e.g. `REM-0002`, `REM-0026`, `REM-0031`, `REM-0008`, `REM-0014`, `REM-0029`, `REM-0023`, `REM-0033`, `REM-0018`, `REM-0017`, `REM-0030`) was **not yet overdue** at pipeline-run-time (`sla_breach = False` stored) but **has since crossed its `sla_date`** by the time this reconciliation query was executed — days-open in the v2 output for these rows is 40–47 days, all past their 1–14 day SLA windows, and none are `Resolved`. In other words: v1's flag is a point-in-time snapshot that goes stale as real time passes; v2's live recomputation is arguably the more correct approach for anything that needs to reflect "is this actually overdue right now" rather than "was this overdue when the pipeline last ran." This is exactly the kind of drift a scheduled daily pipeline run is supposed to catch on its next execution — it hasn't been rerun since, so the stored flags are 40+ days stale.

## Summary

| File | Rows | Mismatches | Verdict |
|---|---|---|---|
| 01_control_test_execution.sql | 1,350 | 0 | Exact match |
| 02_dq_watchlist_signals.sql | 13 | 0 | Exact match (control-failure signal only; null/dup trends are inherited as simulated inputs) |
| 03_data_trust_score.sql | 10 | 0 (after fix) | Exact match — but only after correcting a real off-by-one window-boundary bug the comparison exposed; see below |
| 04_remediation_sla_tracking.sql | 42 | 11 | Disagreement fully explained: `sla_breach` is a frozen snapshot from the last pipeline run, not live-evaluated |

## Edge Cases Investigated

Beyond straight reconciliation, four specific edge cases in the underlying formulas were tested directly against live data.

### Edge Case 1 — Percentage change on a near-zero baseline (the "too strict" failure mode)

The watchlist trend formula is `delta = (recent - early) / max(early, 0.01) * 100`. When `early` is very small, an operationally trivial absolute move produces an enormous percentage.

Confirmed on live data: **DS-012 (Branch Reference)** carries the watchlist reason *"Duplicate rate increased 1192.9%"* — by far the largest single movement in the framework — on a real absolute change of **0.129 percentage points** (0.0108% → 0.14%). A dataset refreshed monthly moved by roughly a tenth of a percentage point and generated the loudest alert on the board.

**Two corrections worth recording here, because the first analysis of this got both wrong:**

1. *The figure is 1,192.9%, not 1,300%.* Recomputing from the stored `duplicate_rate_early` column gives 1,300%, but that column is **rounded to 2dp for display** (0.01). The pipeline's own `watchlist_reason` — computed from the unrounded value — says 1,192.9%, and that is the authoritative number. Working back from it, the true baseline is 0.01083. This is a live example of a real analytical hazard: recomputing a derived metric from a rounded intermediate rather than from source, and getting an answer that silently disagrees with the system's own output by ~107 percentage points.
2. *The `max(early, 0.01)` floor never fired.* The true baseline (0.01083) is **above** the 0.01 floor, so the floor was not the binding term — and in fact, checking all three signals across all 13 datasets, the minimum `early` values are 0.01 (duplicate), 0.25 (null) and 0.67 (control-failure), so **the floor does not engage anywhere in this dataset**. The behavior is caused by percentage-change-against-a-near-zero-baseline generally, not by the floor guard specifically. The floor remains a latent version of the same hazard for any future value below 0.01, but attributing this particular alert to it would be wrong.

This is the direct counterpart to the DS-003 finding: where DS-003 shows the framework being too *lenient* (masking a total failure behind a passing average), DS-012 shows it being too *strict* (amplifying a trivial move into the loudest alert in the system). Both are real, verified behaviors of the same class of formula, not two unrelated bugs.

### Edge Case 2 — Trust score recompute

Already covered by `03_data_trust_score.sql`'s reconciliation above — no separate finding beyond what's in the Summary table.

### Edge Case 3 — Calendar/day-of-week SLA breach pattern

Checked whether tickets opened on certain days of the week breach SLA more often (e.g. a Friday-opened ticket having less working time before a weekend). Query: `SELECT dayofweek(open_date::date), count(*), sum(sla_breach), breach_rate ... GROUP BY dayofweek`. Result: breach rates ranged 28.6%–66.7% across the 7 days, but with only 3–10 tickets per day-of-week bucket, this is **not a material pattern** — it's noise from small sample sizes, not a calendar effect. Reported here as "checked, inconclusive" rather than forced into a finding, since the honest answer matters as much as the positive ones.

### Edge Case 4 — Chronic failure vs. remediation ticket count

Checked whether a control that fails every single day of the 30-day window is treated any differently from one that fails once. Query: group `control_test_results` by `(dataset_id, rule_id)` where `status='Fail'`, `HAVING count(*) >= 27` (i.e. failed nearly or all 30 days), then left-join to `remediation_tickets` on the same key.

Result: **25 dataset-rule pairs failed literally every one of the 30 days in the window** (e.g. `DS-003`/`COMP-004`, `DS-006`/`COMP-006`, `DS-002`/`ACCU-001`, `DS-001`/`CONS-001`, and 21 others). Of those 25, **22 have exactly one remediation ticket total**; only 3 (`DS-002`/`COMP-002`, `DS-003`/`COMP-004`, `DS-001`/`COMP-001`) have two. This is a real, named design gap: the existing "Repeated Control Failure" exception type triggers on ≥3-of-5 *recent* tests failing, but nothing in the framework distinguishes a rule that failed once from one that has failed continuously for a month — both currently generate the same single ticket, with no escalation tied to failure duration. This is the evidence behind the "failure-streak escalation" fix proposed in the recommendation memo and demonstrated directly in `notebooks/01_governance_analysis.ipynb`.

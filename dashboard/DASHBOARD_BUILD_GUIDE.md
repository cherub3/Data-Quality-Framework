# Power BI Dashboard Build Guide

**Scope note:** this is a complete build spec plus a static HTML preview (`dashboard_preview.html`) — no Power BI Desktop is available in the build environment, so no `.pbix` was built or tested here. Follow these steps in your own Power BI Desktop install to produce the real file.

All numbers below are computed live from `data/warehouse/governance.duckdb` at the time this guide was written and are illustrative/synthetic — expect them to differ slightly if you re-export.

## 1. Data setup

1. Export 5 CSVs from the warehouse (already done, see `dashboard/data/`):
   - `domain_trust_scores.csv`
   - `control_test_results.csv`
   - `remediation_tickets.csv`
   - `dq_watchlist.csv`
   - `data_inventory.csv`
2. In Power BI Desktop: **Get Data → Text/CSV**, load all 5 files from `dashboard/data/`.
3. Verify types on load: `test_date`, `open_date`, `sla_date`, `resolution_date`, `review_date` → **Date**; `control_effectiveness`, `failure_rate`, `trust_score`, `avg_control_effectiveness` → **Decimal Number**; `sla_breach` → **True/False**; `dataset_id`, `rule_id`, `ticket_id` → **Text** (not Whole Number — they're formatted IDs like `DS-001`).
4. Create relationships (Model view): `control_test_results[dataset_id]` → `data_inventory[dataset_id]` (many-to-one); `remediation_tickets[dataset_id]` → `data_inventory[dataset_id]` (many-to-one); `dq_watchlist[dataset_id]` → `data_inventory[dataset_id]` (one-to-one).

## 2. DAX measures

```dax
Control Pass Rate % =
DIVIDE(
    CALCULATE(COUNTROWS(control_test_results), control_test_results[status] = "Pass"),
    COUNTROWS(control_test_results)
)
```

```dax
Avg Trust Score =
CALCULATE(
    AVERAGE(domain_trust_scores[trust_score]),
    domain_trust_scores[domain] <> "Enterprise (Overall)"
)
```

```dax
Critical Issues Count =
CALCULATE(
    COUNTROWS(remediation_tickets),
    remediation_tickets[severity] = "Critical"
)
```

```dax
Overdue Tickets =
CALCULATE(
    COUNTROWS(remediation_tickets),
    remediation_tickets[sla_breach] = TRUE
)
```

```dax
Watchlist Count =
CALCULATE(
    COUNTROWS(dq_watchlist),
    dq_watchlist[watchlist_status] = "Watchlist"
)
```

## 3. Charts

### Chart 1 — Data Trust Score Gauge
- Visual: **Gauge**
- Value: `Avg Trust Score` (or filter to `domain = "Enterprise (Overall)"` and use `trust_score` directly for the single enterprise figure)
- Min: 0, Max: 100, Target: 85
- Color bands: 0–74 red (At Risk), 75–89 amber (Monitor), 90–100 green (Trusted) — matches the stored `trust_category` thresholds exactly, don't invent new cutoffs
- Title: "Enterprise Data Trust Score"
- Takeaway (live number): **"Enterprise Trust Score: 90.6/100 (Trusted) — composed of 93.9 avg control effectiveness minus watchlist/monitor penalties."**

### Chart 2 — Control Pass Rate Trend (30-day line)
- Visual: **Line chart**
- Axis: `control_test_results[test_date]`
- Values: `Control Pass Rate %`
- Color: single line, use the amber/red band color since the series sits below target throughout
- Add a constant reference line at 85% (target)
- Title: "30-Day Control Pass Rate Trend"
- Takeaway (live number, computed from the actual daily series): **"Control pass rate ranged 15.6%–26.7% over 30 days (avg 20.1%, 272/1,350 tests) — never approached the 85% target; no clear improving trend, flat/noisy around 20%."**

### Chart 3 — Remediation SLA Compliance (stacked bar by severity)
- Visual: **Stacked bar chart**
- Axis: `remediation_tickets[severity]`
- Values (three measures, one per segment): tickets Resolved on time, tickets currently Overdue (`sla_breach = TRUE`), tickets still Open/In Progress but not yet breached
- Color: green (on-time/resolved), red (overdue), grey (open, on track)
- Title: "Remediation SLA Compliance by Severity"
- Takeaway (live numbers): **"Critical: 6 resolved, 10 overdue, 3 open on-track. High: 2 resolved, 11 overdue, 2 open on-track. Medium: 2 resolved, 0 overdue, 6 open on-track. Overdue concentration is worst in Critical/High severity — exactly where SLA enforcement matters most."**

## 4. Layout & formatting

- Page size: 16:9 (1280×720), single page
- Layout: Chart 1 (gauge) top-left quadrant, Chart 2 (trend line) top-right/full-width below the gauge, Chart 3 (stacked bar) bottom half
- Slicers: `data_inventory[domain]`, `data_inventory[regulatory_criticality]` — placed as a slicer panel on the left edge
- Font: consistent sans-serif (Segoe UI default), title bar dark navy background matching a governance/compliance visual tone, KPI cards above the charts row for Overdue Tickets and Watchlist Count using card visuals bound to those two measures

## 5. Testing checklist

- [ ] All 5 CSVs load with 0 type-conversion errors
- [ ] Relationships show as expected cardinality in Model view (no "many-to-many" surprises)
- [ ] Gauge reads current enterprise trust score correctly when no slicers applied
- [ ] Trend line shows exactly 30 data points (one per `test_date`)
- [ ] Stacked bar totals per severity sum to the correct ticket count (Critical=19, High=15, Medium=8 per current data)
- [ ] Slicers filter all three visuals simultaneously (cross-filtering enabled)

## 6. Save & export

- Save as `governance_dashboard.pbix` in `dashboard/`
- File → Export → Export to PDF for a static snapshot to attach to the recommendation memo
- Publish to Power BI Service only if sharing is actually needed — not required for interview purposes; the local `.pbix` plus `dashboard_preview.html` is sufficient to walk through live.

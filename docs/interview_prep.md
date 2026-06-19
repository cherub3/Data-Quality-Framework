# Interview Preparation Guide
## Automated Data Quality Monitoring Framework

---

## How to Use This Guide

Each question is followed by a concise, confident answer written the way you should speak it — not read it. Practice saying these out loud. The goal is to sound like someone who built this and understood every decision, not someone who memorised a script.

---

## SECTION 1 — The Project and Dataset

---

**Q1. Walk me through this project.**

> I built an automated data quality framework on the Retail Rocket ecommerce dataset — 2.75 million event records spanning a customer journey from product views to purchases. The framework runs 16 validation checks across six quality dimensions, scores the dataset from 0 to 100, writes results to a DuckDB warehouse, generates a plain-English report, and surfaces everything through a Streamlit dashboard. The interesting part is that before I introduced any synthetic problems, the framework had already flagged 67 duplicate transaction IDs and 18,430 orphaned product references in the real data. That's the value proposition: you run it on real data and it tells you things your analysts didn't know.

---

**Q2. Why the Retail Rocket dataset specifically?**

> It has several properties that make it ideal for a data quality framework. It has a natural, testable business funnel — view, add-to-cart, transaction — so consistency rules are obvious. It has referential relationships between three tables, so foreign key checks are meaningful. It's large enough to be realistic at 2.75 million rows but small enough to run locally without any distributed infrastructure. And critically, it has real-world messiness — I didn't need to invent problems. The raw data had them already.

---

**Q3. What real issues did you find in the data?**

> Four. First, 67 duplicate transaction IDs — the same order ID appears twice in the event log, which means any revenue aggregation would double-count those purchases. Second, 3 fully duplicated event rows — byte-for-byte identical records from what appears to be an ingestion issue. Third, and most impactful: 18,430 events referencing products that don't exist in the product catalogue — that's 9.2% of the clean sample. Any category-level or product-level report would silently drop those rows. Fourth, 132 products assigned to category IDs that don't exist in the category hierarchy, which breaks any category rollup.

---

**Q4. Why does the clean dataset score 95.4 instead of 100?**

> Because I deliberately didn't remove the referential integrity issues. The clean dataset was built by stripping structural problems — duplicates, invalid event types, out-of-range timestamps — but the orphaned product references and category mismatches are genuinely present in the source data. Removing them would misrepresent reality. A score of 95.4 means: all critical checks pass, but there are known catalogue gaps affecting category-level reporting. That's an honest, actionable result. A score of 100 would be a lie.

---

**Q5. Describe the dataset schema and how the tables relate.**

> Three tables. Events is the core — one row per user interaction, with timestamp, visitor ID, event type, item ID, and an optional transaction ID that's only populated on purchase events. Item properties is a wide-to-long formatted product catalogue — one row per property per item, so a single product might have 20 rows covering its category, price, availability, and various attributes. I extract just the categoryid rows and deduplicate to get one row per product. Category tree is a simple parent-child hierarchy with two columns — category ID and parent ID. The relationships are: events join to item properties on itemid, and item properties join to category tree on categoryid. Those two joins are where the referential integrity checks fire.

---

## SECTION 2 — Architecture and Design

---

**Q6. Explain your architecture.**

> It's a linear pipeline with a clear separation of concerns. Ingestion loads data and builds the sample. Checks runs 16 validation functions — each one does exactly one thing and returns a standardised result dict. The scorer aggregates those results into dimension scores and a weighted final score. The warehouse writes everything to DuckDB. The reporter generates a plain-text report. The dashboard reads from the warehouse. The whole pipeline is triggered by one command — `python run_pipeline.py`. Every file has one responsibility. I can describe any file in one sentence.

---

**Q7. Why DuckDB instead of SQLite or Postgres?**

> Three reasons. First, DuckDB is an analytical database — it handles aggregations and window functions that SQLite struggles with at scale. Second, it reads CSV files directly with SQL, which is genuinely useful when checking referential integrity across two DataFrames — I can write `SELECT * FROM events WHERE itemid NOT IN (SELECT itemid FROM items)` without loading anything into a separate table. Third, it runs as a single file, zero config, zero server. For a local portfolio project, that's exactly right. SQLite is for transactional workloads. Postgres requires a running server. DuckDB gives analytical SQL locally with no overhead.

---

**Q8. Why does your config.py exist and why does everything import from it?**

> Single source of truth. If the freshness threshold is defined in three places and I change it in one, the other two silently produce wrong results. Config centralises every magic number — severity penalties, dimension weights, timestamp boundaries, sample size — so changing a threshold means editing one line. It also documents intent: `FRESHNESS_MAX_AGE_DAYS = 30` is self-explanatory; the number 30 scattered across five files is not. It's the same principle as environment variables in production systems.

---

**Q9. Why sample at 200,000 rows instead of using all 2.75 million?**

> Speed of iteration during development. A check that takes 2 seconds on 200k rows might take 25 seconds on 2.75 million. When you're debugging a single check function and running it 30 times, that's 12 minutes versus 1 minute. The sampling is reproducible — fixed random seed — so results are consistent across runs. The logic is identical on both sizes. The full dataset run in Phase 2 is a validation step, not a code change. This mirrors how real data engineers work: prototype on a representative sample, validate on full data.

---

**Q10. How does your check function contract work?**

> Every check function takes one or more DataFrames plus a run ID, and returns a dict with exactly nine fields: run_id, rule_id, rule_desc, dimension, severity, status, total_records, failed_records, failure_pct. No exceptions. This contract is enforced by the `_result()` helper — individual check functions never build their own dict, they call `_result()`. This means the scorer and reporter can process any check result without knowing what the check actually did. It's the same principle as an interface in typed languages.

---

## SECTION 3 — Scoring and Quality Logic

---

**Q11. Explain how the quality score is calculated.**

> Each of the six dimensions starts at 100. For every check within a dimension that fails or warns, I subtract a severity penalty: 25 for Critical, 15 for High, 8 for Medium, 3 for Low. The dimension score is clamped at zero — it can't go negative. Then I take a weighted average: completeness, uniqueness, validity, and consistency each get 20%, freshness and referential integrity get 10%. The sum is the final score from 0 to 100. It's transparent, reproducible, and every number traces back to a specific failed rule.

---

**Q12. What is the Critical Override and why is it necessary?**

> The numeric score is an aggregate — it can mask a single catastrophic failure. A dataset could score 85 because it passes most checks, but if visitor IDs are null for 5% of rows, marketing attribution is completely broken. The critical override says: if any Critical check fails, the status label cannot be Excellent or Good, regardless of the aggregate score. It forces the status to Warning or Critical. In practice this means a dataset with null visitor IDs that scores 82 is still labelled Warning — not Good — because 82 doesn't capture the severity of that specific failure. It mirrors how real data quality platforms work: blocking rules that override overall scores.

---

**Q13. Why are COMP-001 and CONS-001 both checking that transaction events have a transaction ID?**

> They're checking different things. COMP-004 is a completeness check — it's asking "is the field populated?" It operates at the field level. CONS-001 is a consistency check — it's asking "does this record make business sense?" A transaction event without a transaction ID is not just missing a field; it's a logical contradiction. These two rules fire together and reinforce each other in the report, which is intentional — it signals to the reader that this is both a data completeness problem AND a business logic violation. The distinction matters for downstream remediation: completeness failures are fixed at the ingestion layer; consistency failures are fixed at the business logic layer.

---

**Q14. Why did you build four corruption tiers instead of just clean and corrupted?**

> Two datasets only demonstrate a binary — it works or it doesn't. Four tiers demonstrate a spectrum and tell a story. The dashboard trend chart shows a realistic improvement journey: a team discovers their pipeline is severely broken (score 55), starts fixing issues (63, 82), and eventually reaches a stable clean state (95). That's a narrative recruiters and hiring managers recognise from real projects. A single clean/corrupted comparison is a lab demonstration. Four tiers over simulated time looks like actual data engineering work.

---

## SECTION 4 — Quality Dimensions Deep Dive

---

**Q15. Which quality dimension is most business-critical for this dataset, and why?**

> Completeness, specifically the transaction ID check. The entire business value of the dataset is tracking the purchase funnel. If transaction events don't have transaction IDs, purchases cannot be attributed, reconciled, or refunded. Revenue figures become guesses. That's a company-stopping problem — it affects finance, operations, and customer support simultaneously. Every other dimension failure has a workaround or a limited blast radius. Missing transaction IDs on purchase events is a fundamental data integrity failure with no workaround.

---

**Q16. Explain your referential integrity checks.**

> Two checks. RI-001 checks that every item ID in the events table exists in the product catalogue — I use `.isin()` on the set of known item IDs, which is O(1) per lookup and fast on 200k rows. RI-002 checks that every category ID in the product catalogue exists in the category tree. Both checks work by extracting the known universe of valid IDs from the reference table and flagging any event or product row where the foreign key is absent. The result is a count of orphaned records — rows that exist but cannot be joined. On the clean dataset, RI-001 finds 18,430 orphans — that's real, not injected.

---

**Q17. How does your freshness check work?**

> Two rules. FRESH-001 checks that the latest event timestamp falls within the known observation window of the dataset — May to September 2015. If the latest timestamp is outside this window, the data has either been stale for a long time or was loaded incorrectly. FRESH-002 looks for gaps — I convert all timestamps to dates, build a full calendar between the first and last event date, and find the longest consecutive run of days with zero events. If that run is 7 days or more, it flags a gap. Both checks use the dataset's own window rather than today's date — because this is historical data, comparing to today would always produce a false freshness failure.

---

**Q18. What does CONS-003 check and how is it implemented? And how do you handle false positives?**

> CONS-003 flags visitors whose very first recorded event is a transaction — no preceding view or add-to-cart. A real purchase journey should start with product discovery. A bare transaction as the first event is a heuristic signal for a tracking gap, bot activity, or broken session stitching.
>
> Implementation: filter to rows with valid visitor IDs and timestamps, sort by timestamp within each visitor group, extract the first event per visitor using `groupby().first()`, then count how many visitors have `event == 'transaction'` as their first event. One groupby, no loops.
>
> **On the false positive question:** I explicitly designed this check to return `WARN` (medium severity, −8 points) rather than `FAIL`. That was a deliberate decision because there are legitimate reasons a visitor's first recorded event is a transaction:
> - **Guest checkout** — the visitor browsed under an anonymous session ID, then checked out under a different authenticated session. The browse events exist but are tied to a different visitorid.
> - **API-driven orders** — mobile apps and external integrations often send transactions directly to the data layer without triggering the web tracking events that generate view records.
> - **External order import** — ERP or POS orders pulled into the event log carry no browse history.
> - **Affiliate deep-links** — a referral URL lands the user directly on checkout, skipping the product page entirely.
>
> In all four cases, CONS-003 fires but the data is not corrupt — it is legitimately incomplete. The framework surfaces the WARN for an analyst to investigate the affected visitor IDs in context. Automatic rejection would cause false negatives on real orders. That is why I chose medium severity and WARN status: it is a signal for human review, not an automated gate.
>
> On the clean dataset, CONS-003 finds approximately 705 visitors (0.4%) whose session starts at a transaction. That rate is consistent with normal guest-checkout and mobile-app behaviour in ecommerce.

---

## SECTION 5 — Technical and Design Decisions

---

**Q19. How would you extend this framework to handle a new dataset?**

> The config-driven design makes extension straightforward. You'd update `config.py` with the new window dates, valid domain values, and file paths. You'd add new check functions to `checks.py` following the same contract — one function, one rule, returns a standard dict. You'd add them to `run_all_checks()`. The scorer, reporter, warehouse, and dashboard don't need to change at all — they operate on the check result contract, not on the specific checks. The framework is not tightly coupled to the Retail Rocket schema; it's coupled to the result dict format.

---

**Q20. What would you do differently if this were a production system?**

> Three things. First, I'd make the check configuration data-driven — define rules in a YAML file rather than code, so a data engineer can add a new check without touching Python. Second, I'd add alerting — write a simple notification when a Critical check fails or the quality score drops below a threshold. Third, I'd add proper test fixtures with known-bad and known-good DataFrames so every check function is tested against its exact failure case. The unit test skeletons are in place; I'd fill them all in production.

---

**Q21. Walk me through what happens when I run `python run_pipeline.py --dataset severe`.**

> The CLI parses the argument and resolves it to `data/processed/severe_dataset.csv`. `load_events()` reads it into a Pandas DataFrame — 201,030 rows. `load_item_properties()` loads the item catalogue from the sample — 417,053 items. `load_category_tree()` loads 1,669 categories. `run_all_checks()` executes all 16 check functions and collects their result dicts. `calculate_quality_score()` groups the results by dimension, calculates dimension scores, takes the weighted average, checks for Critical failures, and returns a scored_result dict with score 55.6 and status Critical. `write_run_log()`, `write_results()`, and `write_summary()` insert rows into DuckDB. `generate_report()` writes a plain-text file to `reports/` with the top 5 issues, all check results, recommendations, and a verdict. The terminal prints the summary. Total elapsed time: approximately 3 seconds on a modern laptop.

---

**Q22. Why did you choose Streamlit over a BI tool like Tableau?**

> Streamlit runs entirely in Python, which means it integrates directly with the DuckDB warehouse without any connectors, drivers, or export steps. It version-controls with the rest of the codebase. A recruiter can clone the repo and run `streamlit run dashboard/app.py` — they don't need a Tableau or Power BI licence. For a portfolio project, reproducibility matters more than visual polish. And Streamlit is increasingly common in data engineering and ML engineering roles — demonstrating it is directly relevant.

---

**Q23. What is the most technically interesting check you implemented?**

> FRESH-002 — the gap detection check. The naive approach would be to loop through the dates and compare consecutive pairs, which works but is slow and hard to read. My implementation converts all timestamps to date objects, builds a complete calendar between the first and last event date using `pd.date_range`, computes events per day as a dictionary lookup, identifies zero-event days, sorts them, and then finds the longest consecutive run of those zero days using a single pass through the sorted list. The result is an O(n) implementation that's also readable. The gap length is stored separately from the standard failed_records count, which is an exception to the contract — I added a `gap_days` field to make the report human-readable: "Gap Detected: Yes, Gap Length: 5,600 Days."

---

**Q24. If a hiring manager asked "how do I know this framework actually works?", what would you say?**

> Three things. First, it found real problems in the Retail Rocket dataset before I injected any synthetic issues — 67 duplicate transaction IDs, 18,430 orphaned item references. A framework that doesn't work wouldn't find those. Second, the four corruption tiers produce predictable, verifiable score progressions: 55.6, 63.6, 82.4, 95.4. Each injected issue maps to a specific check that fires and a specific penalty that reduces the score. You can trace any score to its exact cause. Third, the clean dataset scores 95.4, not 100, because the framework is honest — it flags the genuine referential integrity issues in the source data rather than reporting a misleadingly perfect score.

---

**Q25. What's the biggest limitation of this framework?**

> The referential integrity check only tells you how many events reference unknown items — it doesn't tell you which items are missing or why. In production you'd want a separate reconciliation process to identify the missing products and either backfill them from a source system or flag them as permanently deleted. The current framework surfaces the problem clearly but the resolution path requires additional data pipeline work that's outside the framework's scope.

---

## Common Follow-Up Questions

**"Could you scale this to 100M rows?"**
> With DuckDB, likely yes without code changes — DuckDB handles out-of-core analytical queries well. The Pandas-based checks would need to be rewritten using DuckDB SQL or a chunked processing pattern. The architecture (config, checks, scorer, warehouse, reporter) stays the same; only the computation layer inside checks.py changes.

**"What's the difference between COMP-004 and CONS-001?"**
> See Q13 above. COMP-004 is a field-level completeness check. CONS-001 is a business-logic consistency check. They fire on the same data condition but from different analytical perspectives.

**"How long did this take to build?"**
> Approximately 3 weeks from dataset exploration to a working dashboard. The first week was data understanding and architecture design. The second week was the check engine and scoring. The third week was the warehouse, reporter, dashboard, and historical simulation.

**"Have you used Great Expectations?"**
> I evaluated it and chose not to use it. For a project of this scope, the abstraction overhead of Great Expectations is higher than the benefit. Writing explicit check functions in Python is more transparent, easier to explain in an interview, and produces a result that I can fully understand and modify. In a team context with many data sources and engineers, Great Expectations' managed validation store and data docs would add real value.

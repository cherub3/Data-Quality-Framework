# Interview Notes — Enterprise Data Quality & Governance Framework

Use these answers for competency-based interviews, business analysis rounds, and technical
governance discussions. Each section follows the structure: Business Question → Solution →
Business Value → 30-Second Explanation.

---

## Layer 1 — Data Inventory

**Business Question**
"How do you know which data assets your organization has and who is responsible for them?"

**Solution**
Built a Data Inventory registering all 13 datasets with Dataset ID, Name, Domain, Owner, Steward,
Refresh Frequency, Source System, and Regulatory Criticality. Datasets are categorized into four
tiers: Regulatory Critical, Business Critical, Operational Critical, and Reference Data.

**Business Value**
Without a data inventory, governance is impossible. You cannot govern data you do not know you have.
The inventory creates the foundation for everything else in the framework — controls, scoring,
watchlists, and reporting all trace back to a registered dataset.

**30-Second Explanation**
"Before we can govern data, we need to know what data we have. I created a data inventory for 13
datasets covering the key domains of a bank — customer, transaction, risk, finance, operations, and
reference data. Each dataset has a named owner, a named steward, a defined refresh schedule, and a
regulatory criticality rating. This means that when something goes wrong, we immediately know whose
responsibility it is and how urgent the fix needs to be."

---

## Layer 2 — Control Rulebook

**Business Question**
"How do you define what 'good data' looks like for a bank?"

**Solution**
Designed a Control Rulebook with 30 controls across four quality dimensions: Completeness (8),
Accuracy (8), Consistency (7), and Timeliness (7). Each control has a defined threshold, a severity
rating, and a business description of what it tests.

**Business Value**
The rulebook transforms subjective quality judgements into objective, testable standards. When an
auditor asks "how do you ensure your data is accurate?", the answer is a documented set of controls
with defined thresholds — not a verbal assurance.

**30-Second Explanation**
"I defined 30 governance controls covering the four key data quality dimensions that regulators and
internal audit care about: completeness, accuracy, consistency, and timeliness. For example, a
completeness control checks that every customer record has a non-null Customer ID — the threshold
is 100%, and severity is Critical. This means the framework knows exactly what to test, what
constitutes a pass or fail, and how urgently to escalate a failure."

---

## Layer 3 — Control Testing

**Business Question**
"How do you measure data quality over time rather than just at a single point in time?"

**Solution**
Implemented automated daily control testing across all dataset-control pairs, generating a 30-day
testing history stored in DuckDB. Each test captures pass count, fail count, failure rate, and
control effectiveness percentage.

**Business Value**
Point-in-time quality checks miss trends. A dataset that is 97% effective today but has declined
from 99.5% over the past 30 days is showing a warning signal that a single snapshot would miss.
Historical testing enables trend detection, SLA reporting, and audit evidence.

**30-Second Explanation**
"I run all 30 controls across all 13 datasets every day and store 30 days of results. This means I
can see whether quality is improving, stable, or declining. For audit purposes, I can show a
regulator the complete control testing history for any dataset. And for the operations team, the
trend data feeds directly into the early-warning watchlist before problems become critical."

---

## Layer 4 — Exception Detection

**Business Question**
"How do you prioritize which data quality issues require immediate attention?"

**Solution**
Built an exception detection engine that classifies failures into three types: Critical Control
Failures (Critical-severity rules failing), Repeated Control Failures (3+ consecutive fails), and
Regulatory Critical Issues (any failure in a High-criticality dataset). Each exception gets a
severity rating, a priority score, and a recommended action.

**Business Value**
Not all data quality failures are equally urgent. A missing email address is low priority; a failing
balance check on the General Ledger is critical. The exception detection engine automates the
triage, so the governance team can focus attention where it matters most.

**30-Second Explanation**
"When control testing detects a failure, not all failures are equal. My exception engine
automatically classifies failures into three types. Critical Control Failures on rules like GL
Balance Accuracy trigger immediate escalation. Repeated failures trigger a remediation ticket within
24 hours. And any failure on a regulatory-critical dataset — Transaction Ledger, Risk Exposure,
General Ledger — gets flagged immediately to the Chief Data Officer. The system does the triage so
humans can focus on resolution."

---

## Layer 5 — Data Quality Watchlist

**Business Question**
"How do you catch data quality deterioration before it affects reporting?"

**Solution**
Built a Watchlist that monitors three trend signals for each dataset over a rolling 30-day window:
Null Rate Trend, Duplicate Rate Trend, and Control Failure Rate Trend. Datasets are classified as
Watchlist (2+ deteriorating trends), Monitor (1 deteriorating trend), or Clear. The watchlist
generates a watchlist reason and a recommended action for every flagged dataset.

**Business Value**
This is the most valuable layer in the framework. Traditional monitoring catches failures after they
happen. The watchlist catches the signal 5–10 days before a failure occurs, giving the team time to
investigate and remediate before the issue reaches a regulatory report or executive dashboard.

**30-Second Explanation**
"The Data Quality Watchlist is an early-warning system. Instead of waiting for a control to fail,
it monitors three trend signals: null rate, duplicate rate, and control failure rate. If two or
more of these signals are deteriorating over the last 30 days, the dataset goes on the Watchlist —
with a specific reason and a recommended action. In testing, the watchlist caught issues 5 to 7
days before they would have triggered a traditional control failure. That is the difference between
a proactive fix and a reactive crisis."

---

## Layer 6 — Remediation Workflow

**Business Question**
"How do you ensure data quality issues are actually fixed, and not just reported?"

**Solution**
Built a remediation workflow that creates a ticket for every detected exception. Each ticket tracks
Status (Open → Assigned → In Progress → Escalated → Resolved), Owner, SLA date, Root Cause, and
Resolution Date. SLA breaches are automatically flagged. Five root cause categories are tracked:
Source System Failure, ETL Failure, Manual Entry Error, Mapping Issue, Feed Delay.

**Business Value**
Detection without resolution is noise. The remediation workflow closes the loop from detection to
fix, with accountability (named owner) and urgency (SLA) built in. The SLA breach flag ensures
that tickets approaching overdue status are visible before they breach, not after.

**30-Second Explanation**
"Detecting a problem is only half the job. The remediation workflow creates a tracked ticket for
every exception, assigns it to the right team with a named SLA, and tracks it through five statuses
to verified resolution. Root cause is captured — whether it was a source system failure, an ETL
issue, or a manual entry error — so we can identify systemic patterns. When I show this to a hiring
manager, they see that the framework completes the full governance cycle, not just the detection
part."

---

## Layer 7 — Governance Reporting

**Business Question**
"How do you summarize the health of your data to a non-technical executive?"

**Solution**
Created two hero KPIs: the Data Trust Score (0–100, with Trusted / Monitor / At Risk categories)
computed per domain and at enterprise level, and the Governance Maturity Score (Initial / Developing
/ Managed / Optimized) based on control coverage, automation, SLA compliance, and audit
completeness.

**Business Value**
A CDO does not need to read 30 control results. They need one number that summarizes data health and
tells them if they need to act. The Data Trust Score provides this. The Maturity Score gives the
governance team a measure of how well the overall framework is operating.

**30-Second Explanation**
"The Data Trust Score is the main KPI. It is a 0-to-100 score for each business domain and for
the enterprise as a whole. A score of 90 or above is Trusted, 75 to 89 is Monitor, and below 75
is At Risk. It is derived from control testing results, watchlist status, and exception severity.
It gives the CDO and the board a single clear answer to the question: 'Can we trust our data today?'"

---

## Layer 8 — Monthly Governance Review

**Business Question**
"How do you report data governance outcomes to senior management?"

**Solution**
Generated a structured Monthly Governance Review with five sections: What Happened, Why It Happened,
Business Risk, Recommended Actions, and Expected Impact. The review uses governance language —
audit risk, compliance readiness, reporting reliability, decision confidence — rather than technical
jargon or made-up ROI numbers.

**Business Value**
Monthly governance reviews are a standard requirement in regulated industries. Having a
framework that auto-generates this narrative from live data demonstrates production-grade thinking
and an understanding of how governance operates at the organizational level.

**30-Second Explanation**
"Every month I generate a structured board-level governance review. It has five sections: what
happened with data quality this month, why it happened based on root cause analysis, what the
business risk is, what actions I recommend, and what the expected impact of those actions is. It
avoids made-up cost savings. Instead it speaks the language that regulators and audit committees
understand: audit readiness, compliance posture, reporting confidence, and decision integrity."

---

## Portfolio Positioning

**Question: "How does this project fit into your portfolio?"**

"My three portfolio projects tell a connected story about risk management in banking.

Project 1 — Customer Intelligence: I built a customer risk and portfolio management platform
to identify which customers pose credit and behavioural risk.

Project 2 — Fraud Detection: I built a fraud detection and risk operations platform to identify
anomalous transactions and operational failures in real time.

Project 3 — Data Governance: I built this framework, which governs the underlying data that feeds
both of the first two projects. If the customer data or transaction data has quality problems, the
risk models in Projects 1 and 2 produce unreliable outputs.

Together they address the complete risk lifecycle: Customer Risk, Fraud and Operational Risk, and
Data Risk. This is the sequence that a Head of Data at a bank cares about."

---

## Common Difficult Questions

**"You are a fresher — how can you explain banking governance experience?"**

"I do not claim banking experience. I claim that I studied how banking governance works — reading
Basel III data quality requirements, FCA data governance expectations, and standard frameworks like
DAMA-DMBOK — and I built a project that implements the same governance principles at a
demonstrable scale. The concepts are transferable: control frameworks, exception management, SLA
tracking, audit evidence, and executive reporting exist in every regulated organization. I am
showing you that I understand the WHY behind governance, not just the technical tools."

**"Why DuckDB instead of a proper data warehouse?"**

"For a portfolio project, DuckDB is the right choice. It is SQL-compliant, requires no server setup,
handles analytical workloads efficiently, and keeps the project self-contained and reproducible. In
a production environment I would use Snowflake, BigQuery, or a Databricks lakehouse depending on
the scale and existing infrastructure. The query patterns I use here translate directly to those
platforms."

**"How would this scale to a real bank with thousands of datasets?"**

"The architecture already supports scaling. The data inventory table and control rulebook are the
extensible layers — adding a new dataset means adding a row to the inventory and mapping applicable
controls. The testing engine loops over dataset-control pairs automatically. The watchlist and
exception detection are rule-based and dataset-agnostic. For production scale I would add
orchestration with Airflow or Prefect, a proper warehouse, and integration with the bank's existing
data catalog. The core governance logic remains the same."

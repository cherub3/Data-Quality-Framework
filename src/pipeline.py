"""
Enterprise Data Quality & Governance Framework -- Master Pipeline
Generates all synthetic data, runs all 8 layers, and populates DuckDB.
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "warehouse", "governance.duckdb")

random.seed(42)
np.random.seed(42)

# -------------------------------------------------------
# LAYER 1 -- DATA INVENTORY (13 datasets)
# -------------------------------------------------------

DATA_INVENTORY = [
    # Regulatory Critical
    {"dataset_id": "DS-001", "dataset_name": "Customer Master",      "domain": "Customer",    "category": "Regulatory Critical",  "owner": "Head of Customer Data",  "steward": "Customer Data Steward", "refresh_frequency": "Daily",    "source_system": "CRM",          "regulatory_criticality": "High"},
    {"dataset_id": "DS-002", "dataset_name": "Transaction Ledger",   "domain": "Transaction", "category": "Regulatory Critical",  "owner": "Head of Finance",        "steward": "Finance Data Steward",  "refresh_frequency": "Intraday", "source_system": "Core Banking", "regulatory_criticality": "High"},
    {"dataset_id": "DS-003", "dataset_name": "Risk Exposure",        "domain": "Risk",        "category": "Regulatory Critical",  "owner": "Chief Risk Officer",     "steward": "Risk Data Steward",     "refresh_frequency": "Daily",    "source_system": "Risk Engine",  "regulatory_criticality": "High"},
    {"dataset_id": "DS-004", "dataset_name": "General Ledger",       "domain": "Finance",     "category": "Regulatory Critical",  "owner": "CFO",                    "steward": "GL Data Steward",       "refresh_frequency": "Daily",    "source_system": "ERP",          "regulatory_criticality": "High"},
    # Business Critical
    {"dataset_id": "DS-005", "dataset_name": "Product Master",       "domain": "Product",     "category": "Business Critical",    "owner": "Head of Product",        "steward": "Product Data Steward",  "refresh_frequency": "Weekly",   "source_system": "PMS",          "regulatory_criticality": "Medium"},
    {"dataset_id": "DS-006", "dataset_name": "Sales Performance",    "domain": "Sales",       "category": "Business Critical",    "owner": "Head of Sales",          "steward": "Sales Data Steward",    "refresh_frequency": "Daily",    "source_system": "Salesforce",   "regulatory_criticality": "Medium"},
    {"dataset_id": "DS-007", "dataset_name": "Customer Channels",    "domain": "Customer",    "category": "Business Critical",    "owner": "Head of Digital",        "steward": "Digital Data Steward",  "refresh_frequency": "Daily",    "source_system": "Digital Hub",  "regulatory_criticality": "Medium"},
    {"dataset_id": "DS-008", "dataset_name": "Branch Performance",   "domain": "Operations",  "category": "Business Critical",    "owner": "Head of Retail Banking", "steward": "Branch Data Steward",   "refresh_frequency": "Weekly",   "source_system": "Branch MIS",   "regulatory_criticality": "Medium"},
    # Operational Critical
    {"dataset_id": "DS-009", "dataset_name": "Inventory",            "domain": "Operations",  "category": "Operational Critical", "owner": "Operations Manager",     "steward": "Ops Data Steward",      "refresh_frequency": "Daily",    "source_system": "OMS",          "regulatory_criticality": "Low"},
    {"dataset_id": "DS-010", "dataset_name": "Orders",               "domain": "Operations",  "category": "Operational Critical", "owner": "Operations Manager",     "steward": "Ops Data Steward",      "refresh_frequency": "Daily",    "source_system": "OMS",          "regulatory_criticality": "Low"},
    {"dataset_id": "DS-011", "dataset_name": "Resource Allocation",  "domain": "HR",          "category": "Operational Critical", "owner": "Head of HR",             "steward": "HR Data Steward",       "refresh_frequency": "Weekly",   "source_system": "HRMS",         "regulatory_criticality": "Low"},
    # Reference Data
    {"dataset_id": "DS-012", "dataset_name": "Branch Reference",     "domain": "Reference",   "category": "Reference Data",       "owner": "Data Governance Office", "steward": "Ref Data Steward",      "refresh_frequency": "Monthly",  "source_system": "MDM",          "regulatory_criticality": "Low"},
    {"dataset_id": "DS-013", "dataset_name": "Product Reference",    "domain": "Reference",   "category": "Reference Data",       "owner": "Data Governance Office", "steward": "Ref Data Steward",      "refresh_frequency": "Monthly",  "source_system": "MDM",          "regulatory_criticality": "Low"},
]

# -------------------------------------------------------
# LAYER 2 -- CONTROL RULEBOOK (30 controls)
# -------------------------------------------------------

CONTROL_RULEBOOK = [
    # COMPLETENESS (8)
    {"rule_id": "COMP-001", "rule_name": "Customer ID Not Null",         "category": "Completeness", "description": "All customer records must have a non-null Customer ID.",                    "threshold": 100.0, "severity": "Critical"},
    {"rule_id": "COMP-002", "rule_name": "Transaction Amount Not Null",  "category": "Completeness", "description": "All transaction records must have a non-null Amount field.",               "threshold": 100.0, "severity": "Critical"},
    {"rule_id": "COMP-003", "rule_name": "Account Number Completeness",  "category": "Completeness", "description": "Account number must be populated for all customer records.",               "threshold": 99.5,  "severity": "High"},
    {"rule_id": "COMP-004", "rule_name": "Risk Rating Populated",        "category": "Completeness", "description": "Risk rating field must be populated for all risk exposure records.",       "threshold": 98.0,  "severity": "High"},
    {"rule_id": "COMP-005", "rule_name": "Product Code Completeness",    "category": "Completeness", "description": "Product code must be present for all product master records.",            "threshold": 100.0, "severity": "High"},
    {"rule_id": "COMP-006", "rule_name": "Branch Code Populated",        "category": "Completeness", "description": "Branch code must be populated in all branch performance records.",        "threshold": 100.0, "severity": "Medium"},
    {"rule_id": "COMP-007", "rule_name": "GL Account Code Completeness", "category": "Completeness", "description": "General Ledger account code must be present for all GL entries.",         "threshold": 100.0, "severity": "Critical"},
    {"rule_id": "COMP-008", "rule_name": "Contact Email Completeness",   "category": "Completeness", "description": "Customer email address must be populated for all active customers.",      "threshold": 95.0,  "severity": "Medium"},
    # ACCURACY (8)
    {"rule_id": "ACCU-001", "rule_name": "Transaction Amount Positive",  "category": "Accuracy",     "description": "Transaction amount must be greater than zero for debit/credit entries.",   "threshold": 99.0,  "severity": "Critical"},
    {"rule_id": "ACCU-002", "rule_name": "Date Range Validity",          "category": "Accuracy",     "description": "All transaction dates must fall within the valid operational date range.", "threshold": 99.5,  "severity": "High"},
    {"rule_id": "ACCU-003", "rule_name": "Customer Age Valid Range",     "category": "Accuracy",     "description": "Customer age must be between 18 and 120 years.",                           "threshold": 99.0,  "severity": "Medium"},
    {"rule_id": "ACCU-004", "rule_name": "Risk Score Valid Range",       "category": "Accuracy",     "description": "Risk score must fall between 0 and 1000 per the risk model specification.","threshold": 99.5,  "severity": "High"},
    {"rule_id": "ACCU-005", "rule_name": "Interest Rate Accuracy",       "category": "Accuracy",     "description": "Interest rate must be between 0% and 30% for retail products.",            "threshold": 99.9,  "severity": "Critical"},
    {"rule_id": "ACCU-006", "rule_name": "Postcode Format Accuracy",     "category": "Accuracy",     "description": "Customer postcode must conform to the standard 6-digit format.",           "threshold": 97.0,  "severity": "Low"},
    {"rule_id": "ACCU-007", "rule_name": "GL Balance Accuracy",          "category": "Accuracy",     "description": "GL debit and credit totals must balance within a tolerance of +/-0.01.",   "threshold": 100.0, "severity": "Critical"},
    {"rule_id": "ACCU-008", "rule_name": "Product Price Positive",       "category": "Accuracy",     "description": "Product price must be greater than zero for all active products.",          "threshold": 100.0, "severity": "High"},
    # CONSISTENCY (7)
    {"rule_id": "CONS-001", "rule_name": "Customer-Account Referential Integrity", "category": "Consistency", "description": "Every account must reference a valid Customer ID in Customer Master.",   "threshold": 100.0, "severity": "Critical"},
    {"rule_id": "CONS-002", "rule_name": "Transaction-Account Consistency",        "category": "Consistency", "description": "Every transaction must reference a valid account number.",               "threshold": 100.0, "severity": "Critical"},
    {"rule_id": "CONS-003", "rule_name": "Branch Code Cross-Dataset Consistency",  "category": "Consistency", "description": "Branch codes in transactions must match Branch Reference data.",          "threshold": 99.0,  "severity": "High"},
    {"rule_id": "CONS-004", "rule_name": "Product Code Cross-Dataset Consistency", "category": "Consistency", "description": "Product codes in orders must reference valid Product Master entries.",     "threshold": 99.5,  "severity": "High"},
    {"rule_id": "CONS-005", "rule_name": "Risk Tier Consistency",                  "category": "Consistency", "description": "Risk tier classification must be consistent with risk score bands.",      "threshold": 98.0,  "severity": "High"},
    {"rule_id": "CONS-006", "rule_name": "GL-Transaction Reconciliation",          "category": "Consistency", "description": "GL totals must reconcile with aggregated transaction amounts +/-0.1%.",   "threshold": 99.9,  "severity": "Critical"},
    {"rule_id": "CONS-007", "rule_name": "Customer Status Consistency",            "category": "Consistency", "description": "Active/Inactive status must be consistent across all customer datasets.","threshold": 99.0,  "severity": "Medium"},
    # TIMELINESS (7)
    {"rule_id": "TIME-001", "rule_name": "Customer Master Freshness",    "category": "Timeliness",   "description": "Customer Master must be refreshed within 24 hours of the reference date.",   "threshold": 98.0,  "severity": "High"},
    {"rule_id": "TIME-002", "rule_name": "Transaction Feed SLA",         "category": "Timeliness",   "description": "Intraday transaction feed must arrive within 15 minutes of batch cut-off.",  "threshold": 99.0,  "severity": "Critical"},
    {"rule_id": "TIME-003", "rule_name": "Risk Exposure Daily Refresh",  "category": "Timeliness",   "description": "Risk exposure data must be refreshed by 08:00 AM each business day.",        "threshold": 99.5,  "severity": "Critical"},
    {"rule_id": "TIME-004", "rule_name": "GL Close Timeliness",          "category": "Timeliness",   "description": "General Ledger must close and post within 2 hours of business day end.",     "threshold": 98.0,  "severity": "High"},
    {"rule_id": "TIME-005", "rule_name": "Sales Performance Refresh",    "category": "Timeliness",   "description": "Sales performance data must be available by 07:00 AM the following day.",    "threshold": 97.0,  "severity": "Medium"},
    {"rule_id": "TIME-006", "rule_name": "Reference Data Currency",      "category": "Timeliness",   "description": "Branch and Product reference data must be updated within the monthly cycle.", "threshold": 95.0,  "severity": "Medium"},
    {"rule_id": "TIME-007", "rule_name": "Risk Report Delivery SLA",     "category": "Timeliness",   "description": "Risk reports must be delivered to regulators by 09:00 AM on T+1.",           "threshold": 100.0, "severity": "Critical"},
]

# Dataset -> applicable controls mapping
DATASET_CONTROLS = {
    "DS-001": ["COMP-001", "COMP-003", "COMP-008", "ACCU-003", "ACCU-006", "CONS-001", "CONS-007", "TIME-001"],
    "DS-002": ["COMP-002", "ACCU-001", "ACCU-002", "CONS-002", "CONS-006", "TIME-002"],
    "DS-003": ["COMP-004", "ACCU-004", "CONS-005", "TIME-003", "TIME-007"],
    "DS-004": ["COMP-007", "ACCU-007", "CONS-006", "TIME-004"],
    "DS-005": ["COMP-005", "ACCU-008", "CONS-004"],
    "DS-006": ["COMP-006", "ACCU-001", "TIME-005"],
    "DS-007": ["COMP-008", "CONS-007", "TIME-001"],
    "DS-008": ["COMP-006", "TIME-005"],
    "DS-009": ["COMP-005", "ACCU-008"],
    "DS-010": ["COMP-002", "CONS-004", "TIME-002"],
    "DS-011": ["COMP-001", "COMP-008"],
    "DS-012": ["CONS-003", "TIME-006"],
    "DS-013": ["CONS-004", "TIME-006"],
}

ROOT_CAUSES = [
    "Source System Failure",
    "ETL Failure",
    "Manual Entry Error",
    "Mapping Issue",
    "Feed Delay",
]

REMEDIATION_OWNERS = [
    "Data Engineering Team",
    "Source System Team",
    "Data Governance Office",
    "Finance Operations",
    "Risk Technology",
    "CRM Team",
]


def get_rule_by_id(rule_id):
    return next(r for r in CONTROL_RULEBOOK if r["rule_id"] == rule_id)


def get_dataset_by_id(ds_id):
    return next(d for d in DATA_INVENTORY if d["dataset_id"] == ds_id)


# -------------------------------------------------------
# LAYER 3 -- CONTROL TESTING (30-day history)
# -------------------------------------------------------

def generate_control_test_results():
    rows = []
    today = datetime.today().date()

    dataset_health = {
        "DS-001": {"base_pass_rate": 0.97, "trend": "stable"},
        "DS-002": {"base_pass_rate": 0.91, "trend": "deteriorating"},
        "DS-003": {"base_pass_rate": 0.95, "trend": "stable"},
        "DS-004": {"base_pass_rate": 0.99, "trend": "improving"},
        "DS-005": {"base_pass_rate": 0.98, "trend": "stable"},
        "DS-006": {"base_pass_rate": 0.88, "trend": "deteriorating"},
        "DS-007": {"base_pass_rate": 0.93, "trend": "stable"},
        "DS-008": {"base_pass_rate": 0.97, "trend": "stable"},
        "DS-009": {"base_pass_rate": 0.85, "trend": "deteriorating"},
        "DS-010": {"base_pass_rate": 0.92, "trend": "stable"},
        "DS-011": {"base_pass_rate": 0.96, "trend": "improving"},
        "DS-012": {"base_pass_rate": 0.99, "trend": "stable"},
        "DS-013": {"base_pass_rate": 0.98, "trend": "stable"},
    }

    test_id = 1
    for day_offset in range(29, -1, -1):
        test_date = today - timedelta(days=day_offset)
        for ds_id, controls in DATASET_CONTROLS.items():
            health = dataset_health[ds_id]
            for rule_id in controls:
                rule = get_rule_by_id(rule_id)
                total_records = random.randint(8000, 50000)

                base = health["base_pass_rate"]
                if health["trend"] == "deteriorating":
                    trend_adj = -0.002 * (29 - day_offset)
                elif health["trend"] == "improving":
                    trend_adj = 0.001 * (29 - day_offset)
                else:
                    trend_adj = random.uniform(-0.01, 0.01)

                pass_rate = min(1.0, max(0.5, base + trend_adj + random.uniform(-0.02, 0.02)))
                pass_count = int(total_records * pass_rate)
                fail_count = total_records - pass_count
                failure_rate = round((fail_count / total_records) * 100, 2)
                control_effectiveness = round(pass_rate * 100, 2)
                status = "Pass" if control_effectiveness >= rule["threshold"] else "Fail"

                rows.append({
                    "test_id": "TEST-%05d" % test_id,
                    "test_date": test_date.isoformat(),
                    "dataset_id": ds_id,
                    "rule_id": rule_id,
                    "total_records": total_records,
                    "pass_count": pass_count,
                    "fail_count": fail_count,
                    "failure_rate": failure_rate,
                    "control_effectiveness": control_effectiveness,
                    "status": status,
                })
                test_id += 1

    return pd.DataFrame(rows)


# -------------------------------------------------------
# LAYER 4 -- EXCEPTION DETECTION
# -------------------------------------------------------

def generate_exceptions(test_df):
    today = datetime.today().date()
    recent = test_df[test_df["test_date"] >= (today - timedelta(days=7)).isoformat()]
    exceptions = []
    exc_id = 1

    # Critical rule failures
    critical_rules = [r["rule_id"] for r in CONTROL_RULEBOOK if r["severity"] == "Critical"]
    critical_fails = recent[(recent["rule_id"].isin(critical_rules)) & (recent["status"] == "Fail")]
    for _, row in critical_fails.drop_duplicates(subset=["dataset_id", "rule_id"]).iterrows():
        ds = get_dataset_by_id(row["dataset_id"])
        rule = get_rule_by_id(row["rule_id"])
        exceptions.append({
            "exception_id": "EXC-%04d" % exc_id,
            "exception_type": "Critical Control Failure",
            "dataset_id": row["dataset_id"],
            "dataset_name": ds["dataset_name"],
            "rule_id": row["rule_id"],
            "rule_name": rule["rule_name"],
            "severity": "Critical",
            "priority": 1,
            "detected_date": today.isoformat(),
            "failure_rate": row["failure_rate"],
            "regulatory_criticality": ds["regulatory_criticality"],
            "recommended_action": "Immediately escalate to " + ds["owner"] + ". Halt downstream reporting until resolved.",
        })
        exc_id += 1

    # Repeated failures (3+ consecutive days)
    for ds_id in test_df["dataset_id"].unique():
        for rule_id in DATASET_CONTROLS.get(ds_id, []):
            subset = test_df[
                (test_df["dataset_id"] == ds_id) & (test_df["rule_id"] == rule_id)
            ].sort_values("test_date", ascending=False).head(5)
            if len(subset) >= 3 and (subset["status"] == "Fail").sum() >= 3:
                ds = get_dataset_by_id(ds_id)
                rule = get_rule_by_id(rule_id)
                if not any(e["dataset_id"] == ds_id and e["rule_id"] == rule_id for e in exceptions):
                    exceptions.append({
                        "exception_id": "EXC-%04d" % exc_id,
                        "exception_type": "Repeated Control Failure",
                        "dataset_id": ds_id,
                        "dataset_name": ds["dataset_name"],
                        "rule_id": rule_id,
                        "rule_name": rule["rule_name"],
                        "severity": "High" if rule["severity"] in ["Critical", "High"] else "Medium",
                        "priority": 2,
                        "detected_date": today.isoformat(),
                        "failure_rate": round(float(subset["failure_rate"].mean()), 2),
                        "regulatory_criticality": ds["regulatory_criticality"],
                        "recommended_action": "Assign to " + ds["steward"] + " for root cause investigation. Target resolution within 48 hours.",
                    })
                    exc_id += 1

    # Regulatory critical issues
    reg_ds_ids = [d["dataset_id"] for d in DATA_INVENTORY if d["regulatory_criticality"] == "High"]
    reg_fails = recent[(recent["status"] == "Fail") & (recent["dataset_id"].isin(reg_ds_ids))]
    for _, row in reg_fails.drop_duplicates(subset=["dataset_id"]).iterrows():
        ds = get_dataset_by_id(row["dataset_id"])
        rule = get_rule_by_id(row["rule_id"])
        if not any(e["dataset_id"] == row["dataset_id"] and e["exception_type"] == "Regulatory Critical Issue" for e in exceptions):
            exceptions.append({
                "exception_id": "EXC-%04d" % exc_id,
                "exception_type": "Regulatory Critical Issue",
                "dataset_id": row["dataset_id"],
                "dataset_name": ds["dataset_name"],
                "rule_id": row["rule_id"],
                "rule_name": rule["rule_name"],
                "severity": "Critical",
                "priority": 1,
                "detected_date": today.isoformat(),
                "failure_rate": row["failure_rate"],
                "regulatory_criticality": ds["regulatory_criticality"],
                "recommended_action": "Notify Data Governance Office and Chief Risk Officer. Document for regulatory audit log.",
            })
            exc_id += 1

    return pd.DataFrame(exceptions)


# -------------------------------------------------------
# LAYER 5 -- DATA QUALITY WATCHLIST
# -------------------------------------------------------

def generate_watchlist(test_df):
    today = datetime.today().date()
    watchlist = []
    wl_id = 1

    base_null = {"DS-001": 1.2, "DS-002": 0.8, "DS-003": 2.1, "DS-004": 0.5,
                 "DS-005": 0.9, "DS-006": 3.4, "DS-007": 1.8, "DS-008": 0.7,
                 "DS-009": 4.2, "DS-010": 1.5, "DS-011": 0.6, "DS-012": 0.3, "DS-013": 0.4}
    base_dup  = {"DS-001": 0.3, "DS-002": 0.1, "DS-003": 0.5, "DS-004": 0.2,
                 "DS-005": 0.8, "DS-006": 1.2, "DS-007": 0.4, "DS-008": 0.3,
                 "DS-009": 2.1, "DS-010": 0.6, "DS-011": 0.2, "DS-012": 0.1, "DS-013": 0.1}

    cutoff = (today - timedelta(days=15)).isoformat()

    for ds_id in test_df["dataset_id"].unique():
        ds = get_dataset_by_id(ds_id)
        ds_tests = test_df[test_df["dataset_id"] == ds_id].sort_values("test_date")
        early = ds_tests[ds_tests["test_date"] <= cutoff]
        recent = ds_tests[ds_tests["test_date"] > cutoff]

        if len(early) == 0 or len(recent) == 0:
            continue

        early_fail_rate  = float(early["failure_rate"].mean())
        recent_fail_rate = float(recent["failure_rate"].mean())

        early_null  = base_null.get(ds_id, 1.0) + random.uniform(-0.2, 0.2)
        recent_null = base_null.get(ds_id, 1.0) * random.uniform(0.8, 1.4)
        early_dup   = base_dup.get(ds_id, 0.5) + random.uniform(-0.1, 0.1)
        recent_dup  = base_dup.get(ds_id, 0.5) * random.uniform(0.8, 1.5)

        def trend(ev, rv):
            delta = ((rv - ev) / max(ev, 0.01)) * 100
            if delta > 10:
                return "Deteriorating", delta
            elif delta < -10:
                return "Improving", delta
            else:
                return "Stable", delta

        null_trend, null_delta = trend(early_null, recent_null)
        dup_trend,  dup_delta  = trend(early_dup,  recent_dup)
        fail_trend, fail_delta = trend(early_fail_rate, recent_fail_rate)

        det_count = sum(1 for t in [null_trend, dup_trend, fail_trend] if t == "Deteriorating")
        imp_count = sum(1 for t in [null_trend, dup_trend, fail_trend] if t == "Improving")

        if det_count >= 2:
            wl_status = "Watchlist"
            risk_trend = "Deteriorating"
            priority = "High" if ds["regulatory_criticality"] == "High" else "Medium"
            reasons = []
            if null_trend == "Deteriorating":
                reasons.append("Null rate increased %.1f%%" % null_delta)
            if dup_trend == "Deteriorating":
                reasons.append("Duplicate rate increased %.1f%%" % dup_delta)
            if fail_trend == "Deteriorating":
                reasons.append("Control failure rate worsening (%.1f%%)" % fail_delta)
            wl_reason = "; ".join(reasons)
            recommended_action = "Escalate to Data Steward for investigation. Review source system feeds."
        elif det_count == 1:
            wl_status = "Monitor"
            risk_trend = "Caution"
            priority = "Medium" if ds["regulatory_criticality"] == "High" else "Low"
            wl_reason = "One metric showing deteriorating trend. Monitor for 5 business days."
            recommended_action = "Assign to Data Steward for monitoring. No immediate escalation required."
        elif imp_count >= 2:
            wl_status = "Clear"
            risk_trend = "Improving"
            priority = "Low"
            wl_reason = "Multiple metrics showing improvement trend."
            recommended_action = "Continue monitoring. No action required."
        else:
            wl_status = "Clear"
            risk_trend = "Stable"
            priority = "Low"
            wl_reason = "All metrics within acceptable range."
            recommended_action = "No action required. Schedule next review in 30 days."

        watchlist.append({
            "watchlist_id": "WL-%04d" % wl_id,
            "dataset_id": ds_id,
            "dataset_name": ds["dataset_name"],
            "domain": ds["domain"],
            "regulatory_criticality": ds["regulatory_criticality"],
            "null_rate_early": round(early_null, 2),
            "null_rate_recent": round(recent_null, 2),
            "null_rate_trend": null_trend,
            "duplicate_rate_early": round(early_dup, 2),
            "duplicate_rate_recent": round(recent_dup, 2),
            "duplicate_rate_trend": dup_trend,
            "control_failure_rate_early": round(early_fail_rate, 2),
            "control_failure_rate_recent": round(recent_fail_rate, 2),
            "control_failure_trend": fail_trend,
            "watchlist_status": wl_status,
            "risk_trend": risk_trend,
            "watchlist_reason": wl_reason,
            "priority": priority,
            "recommended_action": recommended_action,
            "review_date": today.isoformat(),
        })
        wl_id += 1

    return pd.DataFrame(watchlist)


# -------------------------------------------------------
# LAYER 6 -- REMEDIATION WORKFLOW
# -------------------------------------------------------

def generate_remediation(exceptions_df, test_df):
    today = datetime.today().date()
    tickets = []
    ticket_id = 1

    if len(exceptions_df) == 0:
        return pd.DataFrame()

    statuses = ["Open", "Assigned", "In Progress", "Escalated", "Resolved"]

    for _, exc in exceptions_df.iterrows():
        sla_days = {"Critical": 1, "High": 3, "Medium": 7, "Low": 14}
        sla = sla_days.get(exc["severity"], 7)
        open_date = today - timedelta(days=random.randint(0, 10))
        sla_date  = open_date + timedelta(days=sla)
        days_open = (today - open_date).days

        if days_open == 0:
            status = "Open"
        elif today > sla_date:
            status = random.choice(["Escalated", "In Progress", "Resolved"])
        else:
            status = random.choice(statuses)

        resolution_date = None
        if status == "Resolved":
            resolution_date = (open_date + timedelta(days=random.randint(1, max(sla, 1)))).isoformat()

        tickets.append({
            "ticket_id": "REM-%04d" % ticket_id,
            "exception_id": exc["exception_id"],
            "dataset_id": exc["dataset_id"],
            "dataset_name": exc["dataset_name"],
            "rule_id": exc["rule_id"],
            "rule_name": exc["rule_name"],
            "severity": exc["severity"],
            "status": status,
            "owner": random.choice(REMEDIATION_OWNERS),
            "open_date": open_date.isoformat(),
            "sla_date": sla_date.isoformat(),
            "sla_breach": bool(today > sla_date and status != "Resolved"),
            "root_cause": random.choice(ROOT_CAUSES),
            "resolution_date": resolution_date,
            "verification_status": "Verified" if status == "Resolved" else "Pending",
            "notes": "Ticket raised for " + exc["exception_type"] + " on " + exc["dataset_name"] + ".",
        })
        ticket_id += 1

    return pd.DataFrame(tickets)


# -------------------------------------------------------
# LAYER 7 -- GOVERNANCE REPORTING
# -------------------------------------------------------

def compute_data_trust_scores(test_df, watchlist_df):
    today = datetime.today().date()
    recent = test_df[test_df["test_date"] >= (today - timedelta(days=7)).isoformat()]
    domain_scores = []

    domains = list(set(d["domain"] for d in DATA_INVENTORY))
    for domain in domains:
        domain_ds = [d["dataset_id"] for d in DATA_INVENTORY if d["domain"] == domain]
        domain_tests = recent[recent["dataset_id"].isin(domain_ds)]
        if len(domain_tests) == 0:
            continue

        avg_eff = float(domain_tests["control_effectiveness"].mean())

        watchlist_penalty = 0
        monitor_penalty = 0
        if watchlist_df is not None and len(watchlist_df) > 0:
            wl_dom = watchlist_df[watchlist_df["domain"] == domain]
            watchlist_penalty = len(wl_dom[wl_dom["watchlist_status"] == "Watchlist"]) * 3
            monitor_penalty   = len(wl_dom[wl_dom["watchlist_status"] == "Monitor"]) * 1

        trust_score = max(0, min(100, avg_eff - watchlist_penalty - monitor_penalty))
        trust_cat   = "Trusted" if trust_score >= 90 else "Monitor" if trust_score >= 75 else "At Risk"

        domain_scores.append({
            "domain": domain,
            "trust_score": round(trust_score, 1),
            "trust_category": trust_cat,
            "avg_control_effectiveness": round(avg_eff, 1),
            "dataset_count": len(domain_ds),
        })

    if domain_scores:
        overall = float(np.mean([d["trust_score"] for d in domain_scores]))
        overall_cat = "Trusted" if overall >= 90 else "Monitor" if overall >= 75 else "At Risk"
        domain_scores.append({
            "domain": "Enterprise (Overall)",
            "trust_score": round(overall, 1),
            "trust_category": overall_cat,
            "avg_control_effectiveness": round(float(np.mean([d["avg_control_effectiveness"] for d in domain_scores])), 1),
            "dataset_count": len(DATA_INVENTORY),
        })

    return pd.DataFrame(domain_scores)


def compute_governance_maturity(test_df, remediation_df):
    control_coverage  = round((len(DATASET_CONTROLS) / len(DATA_INVENTORY)) * 100, 1)
    automation_pct    = 85.0
    audit_completeness = 100.0

    if len(remediation_df) > 0:
        sla_breached   = len(remediation_df[remediation_df["sla_breach"] == True])
        sla_compliance = round(((len(remediation_df) - sla_breached) / max(len(remediation_df), 1)) * 100, 1)
    else:
        sla_compliance = 95.0

    maturity_score = (
        control_coverage   * 0.30 +
        automation_pct     * 0.30 +
        sla_compliance     * 0.25 +
        audit_completeness * 0.15
    )

    maturity_level = (
        "Optimized"  if maturity_score >= 90 else
        "Managed"    if maturity_score >= 75 else
        "Developing" if maturity_score >= 60 else
        "Initial"
    )

    return {
        "maturity_score":      round(maturity_score, 1),
        "maturity_level":      maturity_level,
        "control_coverage":    control_coverage,
        "automation_pct":      automation_pct,
        "sla_compliance":      sla_compliance,
        "audit_completeness":  audit_completeness,
    }


# -------------------------------------------------------
# MAIN PIPELINE
# -------------------------------------------------------

def run_pipeline():
    print("=" * 60)
    print("Enterprise Data Quality & Governance Framework")
    print("Running Full Pipeline...")
    print("=" * 60)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = duckdb.connect(DB_PATH)

    for tbl in ["data_inventory", "control_rulebook", "control_test_results",
                "exceptions", "dq_watchlist", "remediation_tickets",
                "domain_trust_scores", "governance_maturity"]:
        con.execute("DROP TABLE IF EXISTS " + tbl)

    print("\n[Layer 1] Building Data Inventory...")
    inv_df = pd.DataFrame(DATA_INVENTORY)
    con.execute("CREATE TABLE data_inventory AS SELECT * FROM inv_df")
    print("  -> %d datasets registered" % len(inv_df))

    print("[Layer 2] Loading Control Rulebook...")
    rule_df = pd.DataFrame(CONTROL_RULEBOOK)
    con.execute("CREATE TABLE control_rulebook AS SELECT * FROM rule_df")
    print("  -> %d controls defined" % len(rule_df))

    print("[Layer 3] Running Control Tests (30-day history)...")
    test_df = generate_control_test_results()
    con.execute("CREATE TABLE control_test_results AS SELECT * FROM test_df")
    print("  -> %d test results generated" % len(test_df))

    print("[Layer 4] Detecting Exceptions...")
    exc_df = generate_exceptions(test_df)
    if len(exc_df) > 0:
        con.execute("CREATE TABLE exceptions AS SELECT * FROM exc_df")
        print("  -> %d exceptions detected" % len(exc_df))
    else:
        con.execute("""CREATE TABLE exceptions (
            exception_id VARCHAR, exception_type VARCHAR, dataset_id VARCHAR,
            dataset_name VARCHAR, rule_id VARCHAR, rule_name VARCHAR,
            severity VARCHAR, priority INTEGER, detected_date VARCHAR,
            failure_rate DOUBLE, regulatory_criticality VARCHAR,
            recommended_action VARCHAR
        )""")
        print("  -> 0 exceptions detected")

    print("[Layer 5] Generating Data Quality Watchlist...")
    wl_df = generate_watchlist(test_df)
    con.execute("CREATE TABLE dq_watchlist AS SELECT * FROM wl_df")
    wl_count = len(wl_df[wl_df["watchlist_status"] == "Watchlist"])
    print("  -> %d on watchlist, %d on monitor" % (wl_count, len(wl_df[wl_df["watchlist_status"] == "Monitor"])))

    print("[Layer 6] Generating Remediation Tickets...")
    rem_df = generate_remediation(exc_df, test_df)
    if len(rem_df) > 0:
        con.execute("CREATE TABLE remediation_tickets AS SELECT * FROM rem_df")
        print("  -> %d remediation tickets created" % len(rem_df))
    else:
        con.execute("""CREATE TABLE remediation_tickets (
            ticket_id VARCHAR, exception_id VARCHAR, dataset_id VARCHAR,
            dataset_name VARCHAR, rule_id VARCHAR, rule_name VARCHAR,
            severity VARCHAR, status VARCHAR, owner VARCHAR,
            open_date VARCHAR, sla_date VARCHAR, sla_breach BOOLEAN,
            root_cause VARCHAR, resolution_date VARCHAR,
            verification_status VARCHAR, notes VARCHAR
        )""")
        print("  -> 0 tickets created")

    print("[Layer 7] Computing Governance Scores...")
    trust_df = compute_data_trust_scores(test_df, wl_df)
    con.execute("CREATE TABLE domain_trust_scores AS SELECT * FROM trust_df")

    maturity = compute_governance_maturity(test_df, rem_df)
    mat_df   = pd.DataFrame([maturity])
    con.execute("CREATE TABLE governance_maturity AS SELECT * FROM mat_df")

    overall_trust = trust_df[trust_df["domain"] == "Enterprise (Overall)"]["trust_score"].values[0]
    print("  -> Enterprise Data Trust Score: %.1f/100" % overall_trust)
    print("  -> Governance Maturity: %s (%.1f/100)" % (maturity["maturity_level"], maturity["maturity_score"]))

    con.close()
    print("\n[Pipeline Complete] Database written to: %s" % DB_PATH)
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()

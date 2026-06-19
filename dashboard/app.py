"""
Enterprise Data Quality & Governance Framework — Streamlit Dashboard
5-page executive governance dashboard.
"""

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, SRC_DIR)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "warehouse", "governance.duckdb")

st.set_page_config(
    page_title="Enterprise DQ & Governance Framework",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOURS = {
    "Trusted":       "#2ecc71",
    "Monitor":       "#f39c12",
    "At Risk":       "#e74c3c",
    "Critical":      "#e74c3c",
    "High":          "#e67e22",
    "Medium":        "#f39c12",
    "Low":           "#3498db",
    "Watchlist":     "#e74c3c",
    "Deteriorating": "#e74c3c",
    "Stable":        "#f39c12",
    "Improving":     "#2ecc71",
    "Caution":       "#f39c12",
    "Pass":          "#2ecc71",
    "Fail":          "#e74c3c",
    "Resolved":      "#2ecc71",
    "Escalated":     "#e74c3c",
    "In Progress":   "#3498db",
    "Assigned":      "#9b59b6",
    "Open":          "#95a5a6",
}


@st.cache_resource
def get_con():
    if not os.path.exists(DB_PATH):
        st.error("Database not found. Please run:  python src/pipeline.py")
        st.stop()
    return duckdb.connect(DB_PATH, read_only=True)


def q(sql):
    con = get_con()
    return con.execute(sql).df()


# ── Sidebar ───────────────────────────────────────────────────────────────────
PAGES = {
    "🏛️  Executive Overview":        "executive",
    "🚨  Data Quality Watchlist":    "watchlist",
    "🧪  Control Testing":           "controls",
    "🔧  Issue & Remediation":       "remediation",
    "📋  Monthly Governance Review": "review",
}

st.sidebar.title("🏛️ DQ Governance")
st.sidebar.markdown("**Enterprise Framework**")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")
current = PAGES[page]

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Pipeline"):
    try:
        from pipeline import run_pipeline
        with st.spinner("Running pipeline..."):
            run_pipeline()
        st.cache_resource.clear()
        st.success("Pipeline complete!")
        st.rerun()
    except Exception as e:
        st.error(f"Pipeline error: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("Enterprise Data Quality & Governance Framework")
st.sidebar.caption("Portfolio Project — Data Governance")


# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE GOVERNANCE OVERVIEW
# ════════════════════════════════════════════════════════════════════════════

if current == "executive":
    st.title("🏛️ Executive Governance Overview")
    st.caption("Enterprise-wide data quality and governance health — Board-level KPI summary")
    st.markdown("---")

    trust_df = q("SELECT * FROM domain_trust_scores")
    overall  = trust_df[trust_df["domain"] == "Enterprise (Overall)"].iloc[0]
    maturity = q("SELECT * FROM governance_maturity").iloc[0]
    exc_df   = q("SELECT * FROM exceptions")
    rem_df   = q("SELECT * FROM remediation_tickets")
    wl_df    = q("SELECT * FROM dq_watchlist")

    score     = overall["trust_score"]
    score_cat = overall["trust_category"]
    score_col = COLOURS[score_cat]

    col_hero, col_gauge = st.columns([1, 1])
    with col_hero:
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#1a1a2e,#16213e);
                    border-radius:16px;padding:32px;text-align:center;
                    border-left:6px solid {score_col};'>
          <p style='color:#aaa;margin:0;font-size:14px;text-transform:uppercase;letter-spacing:2px;'>
            Enterprise Data Trust Score</p>
          <h1 style='color:{score_col};font-size:80px;margin:8px 0;'>{score}</h1>
          <p style='color:{score_col};font-size:20px;font-weight:bold;margin:0;'>{score_cat}</p>
          <p style='color:#888;font-size:12px;margin-top:8px;'>
            90+ Trusted &nbsp;|&nbsp; 75–89 Monitor &nbsp;|&nbsp; &lt;75 At Risk</p>
        </div>
        """, unsafe_allow_html=True)

    with col_gauge:
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number={"font": {"size": 40, "color": score_col}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#aaa"},
                "bar":  {"color": score_col, "thickness": 0.25},
                "bgcolor": "#1e1e2e",
                "steps": [
                    {"range": [0,  75], "color": "#3d1a1a"},
                    {"range": [75, 90], "color": "#3d2f0a"},
                    {"range": [90,100], "color": "#0a3d1a"},
                ],
                "threshold": {"line": {"color": "white", "width": 3}, "value": 90},
            },
            title={"text": "Data Trust Gauge", "font": {"color": "#ccc"}},
        ))
        fig_g.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font={"color": "#ccc"}, height=260, margin=dict(t=40, b=0, l=10, r=10))
        st.plotly_chart(fig_g, use_container_width=True)

    st.markdown("---")
    st.subheader("Quality KPIs")
    failed_controls = len(q("""
        SELECT DISTINCT rule_id, dataset_id FROM control_test_results
        WHERE test_date >= CURRENT_DATE - 7 AND status = 'Fail'
    """))
    crit_exc   = len(exc_df[exc_df["severity"] == "Critical"]) if len(exc_df) > 0 else 0
    avg_eff    = round(q("SELECT AVG(control_effectiveness) as a FROM control_test_results WHERE test_date >= CURRENT_DATE - 7")["a"].values[0], 1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Data Trust Score",         f"{score}/100",       delta=score_cat)
    c2.metric("Failed Controls (7d)",      failed_controls,     delta=f"-{failed_controls} issues", delta_color="inverse")
    c3.metric("Critical Exceptions",       crit_exc,            delta="Requires action" if crit_exc > 0 else "None", delta_color="inverse" if crit_exc > 0 else "normal")
    c4.metric("Avg Control Effectiveness", f"{avg_eff}%")

    st.subheader("Operations KPIs")
    open_issues    = len(rem_df[rem_df["status"].isin(["Open","Assigned","In Progress"])]) if len(rem_df) > 0 else 0
    sla_breached   = len(rem_df[rem_df["sla_breach"] == True]) if len(rem_df) > 0 else 0
    sla_compliance = round(((len(rem_df) - sla_breached) / max(len(rem_df), 1)) * 100, 1) if len(rem_df) > 0 else 100.0
    backlog        = len(rem_df[rem_df["status"] == "Escalated"]) if len(rem_df) > 0 else 0
    watchlist_cnt  = len(wl_df[wl_df["watchlist_status"] == "Watchlist"]) if len(wl_df) > 0 else 0

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Open Issues",           open_issues,           delta="Active" if open_issues > 0 else "None")
    c6.metric("SLA Compliance",        f"{sla_compliance}%",  delta=f"{sla_breached} breached", delta_color="inverse" if sla_breached > 0 else "normal")
    c7.metric("Remediation Backlog",   backlog,               delta="Escalated" if backlog > 0 else "None", delta_color="inverse" if backlog > 0 else "normal")
    c8.metric("Datasets on Watchlist", watchlist_cnt,         delta="Early warning" if watchlist_cnt > 0 else "None", delta_color="inverse" if watchlist_cnt > 0 else "normal")

    st.markdown("---")
    st.subheader("Domain Trust Scores")
    domain_df = trust_df[trust_df["domain"] != "Enterprise (Overall)"].copy()
    fig2 = px.bar(
        domain_df.sort_values("trust_score", ascending=True),
        x="trust_score", y="domain", orientation="h",
        color="trust_category", color_discrete_map=COLOURS,
        text="trust_score",
        labels={"trust_score": "Trust Score", "domain": "Domain"},
        title="Data Trust Score by Domain",
    )
    fig2.add_vline(x=90, line_dash="dash", line_color="#2ecc71", annotation_text="Trusted (90)")
    fig2.add_vline(x=75, line_dash="dash", line_color="#f39c12", annotation_text="Monitor (75)")
    fig2.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font={"color": "#ccc"}, height=380, margin=dict(l=140))
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Governance Maturity")
    col_m1, col_m2 = st.columns([1, 2])
    mat_level  = maturity["maturity_level"]
    mat_score  = maturity["maturity_score"]
    mat_col    = {"Optimized":"#2ecc71","Managed":"#3498db","Developing":"#f39c12","Initial":"#e74c3c"}.get(mat_level,"#aaa")
    with col_m1:
        st.markdown(f"""
        <div style='background:#16213e;border-radius:12px;padding:24px;text-align:center;
                    border-left:4px solid {mat_col};'>
          <p style='color:#aaa;margin:0;font-size:13px;'>Governance Maturity</p>
          <h2 style='color:{mat_col};margin:8px 0;'>{mat_level}</h2>
          <h3 style='color:{mat_col};margin:0;'>{mat_score}/100</h3>
        </div>
        """, unsafe_allow_html=True)

    with col_m2:
        mat_metrics = {
            "Control Coverage":   maturity["control_coverage"],
            "Automation %":       maturity["automation_pct"],
            "SLA Compliance":     maturity["sla_compliance"],
            "Audit Completeness": maturity["audit_completeness"],
        }
        fig3 = go.Figure([
            go.Bar(x=[v], y=[k], orientation="h", marker_color="#3498db",
                   text=f"{v:.1f}%", textposition="outside", name=k)
            for k, v in mat_metrics.items()
        ])
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#ccc"}, showlegend=False,
            xaxis={"range": [0, 115]}, height=200,
            margin=dict(l=140, t=10, b=10, r=60),
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.subheader("Governance KPIs")
    reg_issues       = len(exc_df[(exc_df["regulatory_criticality"] == "High") & (exc_df["severity"].isin(["Critical","High"]))]) if len(exc_df) > 0 else 0
    ctrl_eff_30d     = round(q("SELECT AVG(control_effectiveness) as a FROM control_test_results WHERE test_date >= CURRENT_DATE - 30")["a"].values[0], 1)
    cg1, cg2, cg3   = st.columns(3)
    cg1.metric("Governance Maturity",            f"{mat_level} ({mat_score}/100)")
    cg2.metric("Regulatory Critical Issues",     reg_issues, delta="High priority" if reg_issues > 0 else "None", delta_color="inverse" if reg_issues > 0 else "normal")
    cg3.metric("Avg Control Effectiveness (30d)", f"{ctrl_eff_30d}%")


# ════════════════════════════════════════════════════════════════════════════
# PAGE 2 — DATA QUALITY WATCHLIST
# ════════════════════════════════════════════════════════════════════════════

elif current == "watchlist":
    st.title("🚨 Data Quality Watchlist")
    st.caption("Early-warning system — detecting deterioration before it impacts reporting")
    st.markdown("---")

    wl_df = q("SELECT * FROM dq_watchlist ORDER BY watchlist_status, priority, dataset_name")

    on_watch   = len(wl_df[wl_df["watchlist_status"] == "Watchlist"])
    on_monitor = len(wl_df[wl_df["watchlist_status"] == "Monitor"])
    clear      = len(wl_df[wl_df["watchlist_status"] == "Clear"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Datasets Monitored", len(wl_df))
    c2.metric("🔴 On Watchlist",          on_watch)
    c3.metric("🟡 On Monitor",            on_monitor)
    c4.metric("🟢 Clear",                 clear)

    st.markdown("---")

    col_f1, col_f2 = st.columns(2)
    status_filter   = col_f1.multiselect("Watchlist Status", ["Watchlist","Monitor","Clear"], default=["Watchlist","Monitor"])
    priority_filter = col_f2.multiselect("Priority", ["High","Medium","Low"], default=["High","Medium"])
    filtered        = wl_df[wl_df["watchlist_status"].isin(status_filter) & wl_df["priority"].isin(priority_filter)]

    st.subheader(f"Watchlist Entries ({len(filtered)} datasets)")
    for _, row in filtered.iterrows():
        label_col = "red" if row["watchlist_status"] == "Watchlist" else "orange" if row["watchlist_status"] == "Monitor" else "green"
        with st.expander(
            f"{row['watchlist_status'].upper()} | {row['dataset_name']} ({row['dataset_id']}) — {row['risk_trend']}",
            expanded=(row["watchlist_status"] == "Watchlist"),
        ):
            ca, cb, cc = st.columns(3)
            ca.markdown(f"**Domain:** {row['domain']}")
            ca.markdown(f"**Reg Criticality:** {row['regulatory_criticality']}")
            cb.markdown(f"**Priority:** {row['priority']}")
            cb.markdown(f"**Review Date:** {row['review_date']}")
            cc.markdown(f"**Status:** :{label_col}[{row['watchlist_status']}]")
            cc.markdown(f"**Risk Trend:** {row['risk_trend']}")

            st.markdown("**Watchlist Reason:**")
            st.info(row["watchlist_reason"])

            trend_data = {
                "Metric":               ["Null Rate (%)", "Duplicate Rate (%)", "Control Failure Rate (%)"],
                "Early (d1–15)":        [row["null_rate_early"], row["duplicate_rate_early"], row["control_failure_rate_early"]],
                "Recent (d16–30)":      [row["null_rate_recent"], row["duplicate_rate_recent"], row["control_failure_rate_recent"]],
                "Trend":                [row["null_rate_trend"], row["duplicate_rate_trend"], row["control_failure_trend"]],
            }
            st.dataframe(pd.DataFrame(trend_data), hide_index=True, use_container_width=True)
            st.markdown("**Recommended Action:**")
            st.warning(row["recommended_action"])

    st.markdown("---")
    st.subheader("Trend Summary Heatmap")

    pivot_rows = []
    for _, row in wl_df.iterrows():
        pivot_rows.append({"Dataset": row["dataset_name"], "Metric": "Null Rate",           "Trend": row["null_rate_trend"]})
        pivot_rows.append({"Dataset": row["dataset_name"], "Metric": "Duplicate Rate",      "Trend": row["duplicate_rate_trend"]})
        pivot_rows.append({"Dataset": row["dataset_name"], "Metric": "Ctrl Failure Rate",   "Trend": row["control_failure_trend"]})

    pivot_df = pd.DataFrame(pivot_rows)
    tmap     = {"Deteriorating": -1, "Stable": 0, "Improving": 1}
    pivot_df["Score"] = pivot_df["Trend"].map(tmap)
    heatmap  = pivot_df.pivot_table(index="Dataset", columns="Metric", values="Score", aggfunc="first")

    fig_heat = px.imshow(
        heatmap,
        color_continuous_scale=["#e74c3c", "#f39c12", "#2ecc71"],
        zmin=-1, zmax=1,
        title="Trend Heatmap (Green = Improving | Red = Deteriorating)",
        aspect="auto",
    )
    fig_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font={"color": "#ccc"}, height=440)
    st.plotly_chart(fig_heat, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 3 — CONTROL TESTING
# ════════════════════════════════════════════════════════════════════════════

elif current == "controls":
    st.title("🧪 Control Testing")
    st.caption("30-day control testing history across 30 controls and 13 datasets")
    st.markdown("---")

    test_df    = q("SELECT * FROM control_test_results")
    rule_df    = q("SELECT * FROM control_rulebook")
    inv_df     = q("SELECT * FROM data_inventory")
    today_test = q("SELECT * FROM control_test_results WHERE test_date = (SELECT MAX(test_date) FROM control_test_results)")

    total_today = len(today_test)
    pass_today  = len(today_test[today_test["status"] == "Pass"])
    fail_today  = len(today_test[today_test["status"] == "Fail"])
    pass_rate   = round((pass_today / max(total_today, 1)) * 100, 1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Controls",          len(rule_df))
    c2.metric("Controls Passed Today",   pass_today)
    c3.metric("Controls Failed Today",   fail_today, delta_color="inverse")
    c4.metric("Today's Pass Rate",       f"{pass_rate}%")

    st.markdown("---")

    with st.expander("📋 Control Rulebook (30 Controls)", expanded=False):
        st.dataframe(rule_df[["rule_id","rule_name","category","threshold","severity"]], hide_index=True, use_container_width=True)

    st.subheader("Control Effectiveness by Category (Last 7 Days)")
    cat_df = q("""
        SELECT cr.category,
               ROUND(AVG(ct.control_effectiveness),1) as avg_effectiveness,
               SUM(CASE WHEN ct.status='Fail' THEN 1 ELSE 0 END) as fail_count
        FROM control_test_results ct
        JOIN control_rulebook cr ON ct.rule_id = cr.rule_id
        WHERE ct.test_date >= CURRENT_DATE - 7
        GROUP BY cr.category ORDER BY avg_effectiveness
    """)

    fig_cat = px.bar(
        cat_df, x="avg_effectiveness", y="category", orientation="h",
        color="avg_effectiveness",
        color_continuous_scale=["#e74c3c","#f39c12","#2ecc71"],
        range_color=[85, 100],
        text="avg_effectiveness",
        title="Average Control Effectiveness by Category",
    )
    fig_cat.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_cat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font={"color":"#ccc"}, coloraxis_showscale=False, height=280)
    st.plotly_chart(fig_cat, use_container_width=True)

    st.subheader("30-Day Control Failure Trend")
    ds_sel    = st.selectbox("Select Dataset", inv_df["dataset_name"].tolist())
    ds_id_sel = inv_df[inv_df["dataset_name"] == ds_sel]["dataset_id"].values[0]

    trend_q = q(f"""
        SELECT test_date,
               ROUND(AVG(control_effectiveness),2) as avg_effectiveness,
               SUM(CASE WHEN status='Fail' THEN 1 ELSE 0 END) as fail_count
        FROM control_test_results
        WHERE dataset_id = '{ds_id_sel}'
        GROUP BY test_date ORDER BY test_date
    """)

    if len(trend_q) > 0:
        fig_tr = go.Figure()
        fig_tr.add_trace(go.Scatter(
            x=trend_q["test_date"], y=trend_q["avg_effectiveness"],
            mode="lines+markers", name="Avg Effectiveness",
            line={"color":"#3498db","width":2},
        ))
        fig_tr.add_hline(y=95, line_dash="dash", line_color="#2ecc71", annotation_text="Target 95%")
        fig_tr.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font={"color":"#ccc"}, height=300, yaxis={"range":[70,102]},
            title=f"Control Effectiveness — {ds_sel}",
        )
        st.plotly_chart(fig_tr, use_container_width=True)

    st.subheader("Dataset Control Scorecard (Last 7 Days)")
    scorecard = q("""
        SELECT ct.dataset_id, di.dataset_name, di.domain, di.regulatory_criticality,
               COUNT(DISTINCT ct.rule_id) as controls_tested,
               SUM(CASE WHEN ct.status='Pass' THEN 1 ELSE 0 END) as passed,
               SUM(CASE WHEN ct.status='Fail' THEN 1 ELSE 0 END) as failed,
               ROUND(AVG(ct.control_effectiveness),1) as avg_effectiveness
        FROM control_test_results ct
        JOIN data_inventory di ON ct.dataset_id = di.dataset_id
        WHERE ct.test_date >= CURRENT_DATE - 7
        GROUP BY ct.dataset_id, di.dataset_name, di.domain, di.regulatory_criticality
        ORDER BY avg_effectiveness
    """)
    st.dataframe(scorecard, hide_index=True, use_container_width=True)

    st.subheader("Failed Controls — Severity Breakdown (Last 7 Days)")
    sev_q = q("""
        SELECT cr.severity, COUNT(*) as fail_count
        FROM control_test_results ct
        JOIN control_rulebook cr ON ct.rule_id = cr.rule_id
        WHERE ct.status='Fail' AND ct.test_date >= CURRENT_DATE - 7
        GROUP BY cr.severity
    """)
    if len(sev_q) > 0:
        fig_sev = px.pie(sev_q, names="severity", values="fail_count",
                         color="severity", color_discrete_map=COLOURS,
                         title="Failed Controls by Severity")
        fig_sev.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={"color":"#ccc"}, height=300)
        st.plotly_chart(fig_sev, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 4 — ISSUE & REMEDIATION MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════

elif current == "remediation":
    st.title("🔧 Issue & Remediation Management")
    st.caption("Full lifecycle tracking from exception detection to verified resolution")
    st.markdown("---")

    exc_df = q("SELECT * FROM exceptions")
    rem_df = q("SELECT * FROM remediation_tickets ORDER BY severity, open_date")

    open_count   = len(rem_df[rem_df["status"].isin(["Open","Assigned","In Progress"])]) if len(rem_df) > 0 else 0
    escalated    = len(rem_df[rem_df["status"] == "Escalated"])                           if len(rem_df) > 0 else 0
    resolved     = len(rem_df[rem_df["status"] == "Resolved"])                            if len(rem_df) > 0 else 0
    sla_breached = len(rem_df[rem_df["sla_breach"] == True])                              if len(rem_df) > 0 else 0
    total        = len(rem_df)
    sla_comp     = round(((total - sla_breached) / max(total, 1)) * 100, 1)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Tickets",        total)
    c2.metric("Open / In Progress",   open_count)
    c3.metric("Escalated",            escalated,    delta="Needs attention" if escalated > 0 else None, delta_color="inverse")
    c4.metric("Resolved",             resolved)
    c5.metric("SLA Compliance",       f"{sla_comp}%", delta=f"{sla_breached} breaches", delta_color="inverse" if sla_breached > 0 else "normal")

    st.markdown("---")
    st.subheader("Exception Registry")
    if len(exc_df) > 0:
        st.dataframe(
            exc_df[["exception_id","exception_type","dataset_name","rule_name",
                    "severity","failure_rate","regulatory_criticality","recommended_action"]],
            hide_index=True, use_container_width=True,
        )
    else:
        st.info("No exceptions detected.")

    st.markdown("---")
    st.subheader("Remediation Tickets")
    if len(rem_df) > 0:
        cf1, cf2 = st.columns(2)
        sev_flt    = cf1.multiselect("Severity",  ["Critical","High","Medium","Low"], default=["Critical","High"])
        status_flt = cf2.multiselect("Status",    ["Open","Assigned","In Progress","Escalated","Resolved"],
                                     default=["Open","Assigned","In Progress","Escalated"])
        filtered_r = rem_df[rem_df["severity"].isin(sev_flt) & rem_df["status"].isin(status_flt)]

        for _, row in filtered_r.iterrows():
            sla_flag = "⚠️ SLA BREACHED" if row["sla_breach"] else "✅ Within SLA"
            with st.expander(f"{row['ticket_id']} | {row['severity']} | {row['dataset_name']} — {row['status']} | {sla_flag}"):
                ca, cb = st.columns(2)
                ca.markdown(f"**Exception:** {row['exception_id']}")
                ca.markdown(f"**Rule:** {row['rule_name']}")
                ca.markdown(f"**Root Cause:** {row['root_cause']}")
                ca.markdown(f"**Owner:** {row['owner']}")
                cb.markdown(f"**Status:** {row['status']}")
                cb.markdown(f"**Opened:** {row['open_date']}")
                cb.markdown(f"**SLA Date:** {row['sla_date']}")
                cb.markdown(f"**Resolution:** {row['resolution_date'] or 'Pending'}")
                cb.markdown(f"**Verification:** {row['verification_status']}")
                st.caption(row["notes"])

    st.markdown("---")
    st.subheader("Root Cause Analysis")
    if len(rem_df) > 0:
        cr1, cr2 = st.columns(2)
        rc_df = rem_df.groupby("root_cause").size().reset_index(name="count")
        fig_rc = px.pie(rc_df, names="root_cause", values="count",
                        title="Tickets by Root Cause",
                        color_discrete_sequence=px.colors.qualitative.Set2)
        fig_rc.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={"color":"#ccc"}, height=320)
        cr1.plotly_chart(fig_rc, use_container_width=True)

        st_df = rem_df.groupby("status").size().reset_index(name="count")
        fig_st = px.bar(st_df, x="status", y="count", color="status",
                        color_discrete_map=COLOURS, title="Tickets by Status")
        fig_st.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                             font={"color":"#ccc"}, height=320, showlegend=False)
        cr2.plotly_chart(fig_st, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 5 — MONTHLY GOVERNANCE REVIEW
# ════════════════════════════════════════════════════════════════════════════

elif current == "review":
    st.title("📋 Monthly Governance Review")
    st.caption("Executive governance narrative — What happened, why, and what to do next")
    st.markdown("---")

    from datetime import datetime as _dt
    trust_df = q("SELECT * FROM domain_trust_scores")
    wl_df    = q("SELECT * FROM dq_watchlist")
    exc_df   = q("SELECT * FROM exceptions")
    rem_df   = q("SELECT * FROM remediation_tickets")
    maturity = q("SELECT * FROM governance_maturity").iloc[0]

    overall_trust = trust_df[trust_df["domain"] == "Enterprise (Overall)"]["trust_score"].values[0]
    overall_cat   = trust_df[trust_df["domain"] == "Enterprise (Overall)"]["trust_category"].values[0]
    on_watchlist  = len(wl_df[wl_df["watchlist_status"] == "Watchlist"]) if len(wl_df) > 0 else 0
    crit_exc      = len(exc_df[exc_df["severity"] == "Critical"])        if len(exc_df) > 0 else 0
    sla_breach    = len(rem_df[rem_df["sla_breach"] == True])            if len(rem_df) > 0 else 0
    today         = _dt.today()
    month_name    = today.strftime("%B %Y")

    st.markdown(f"## Monthly Governance Review — {month_name}")
    st.markdown(f"**Prepared by:** Data Governance Office &nbsp;|&nbsp; **Date:** {today.strftime('%d %B %Y')}")
    st.markdown("---")

    # 1 — What Happened
    st.markdown("### 1. What Happened This Month")
    st.markdown(f"""
The enterprise **Data Trust Score** for {month_name} stands at **{overall_trust}/100 ({overall_cat})**.

Key observations:
- **{on_watchlist} dataset(s)** placed on the Data Quality Watchlist due to deteriorating quality trends.
- **{crit_exc} critical exception(s)** detected across regulatory-critical datasets.
- **{sla_breach} SLA breach(es)** recorded in the remediation workflow.
- Control testing executed across all **13 datasets** and **30 controls** with full 30-day history.
""")

    if on_watchlist > 0:
        det_ds = wl_df[wl_df["watchlist_status"] == "Watchlist"]["dataset_name"].tolist()
        st.warning(f"**Watchlist Datasets:** {', '.join(det_ds)}")
    if crit_exc > 0:
        crit_ds = exc_df[exc_df["severity"] == "Critical"]["dataset_name"].tolist()
        st.error(f"**Critical Exceptions in:** {', '.join(set(crit_ds))}")

    # 2 — Why It Happened
    st.markdown("---")
    st.markdown("### 2. Why It Happened")
    top_rc = rem_df["root_cause"].value_counts().index[0] if len(rem_df) > 0 else "Data not available"
    st.markdown(f"""
Root cause analysis identifies **{top_rc}** as the leading driver of data quality issues this month.

Contributing factors:
- **Source system instability** in upstream feeds causing delayed or incomplete data loads.
- **ETL pipeline failures** resulting in partial dataset refreshes and stale records.
- **Manual entry errors** in operational datasets (Branch Performance, Resource Allocation).
- **Mapping issues** introduced during recent schema changes in Core Banking.

Watchlist deterioration patterns predate downstream reporting impact, validating the early-warning capability.
""")

    # 3 — Business Risk
    st.markdown("---")
    st.markdown("### 3. Business Risk Assessment")
    risk_level = "High" if (crit_exc > 3 or overall_trust < 75) else "Medium" if (crit_exc > 0 or overall_trust < 85) else "Low"
    risk_col   = COLOURS.get(risk_level, "#aaa")
    cr1, cr2   = st.columns([1, 3])
    cr1.markdown(f"""
    <div style='background:#16213e;border-radius:10px;padding:20px;text-align:center;border-left:4px solid {risk_col};'>
      <p style='color:#aaa;margin:0;font-size:12px;'>Overall Business Risk</p>
      <h2 style='color:{risk_col};margin:8px 0;'>{risk_level}</h2>
    </div>
    """, unsafe_allow_html=True)
    cr2.markdown(f"""
**Regulatory reporting risk:** {"Elevated — critical datasets showing quality deterioration." if crit_exc > 0 else "Low — regulatory-critical datasets within tolerance."}

**Audit readiness:** {f"{sla_breach} SLA breach(es) must be documented in the audit log." if sla_breach > 0 else "Control testing records complete and audit-ready."}

**Decision confidence:** {"Medium — executive reports may contain quality caveats until watchlist datasets are remediated." if on_watchlist > 0 else "High — no active watchlist alerts impacting reporting."}

**Compliance readiness:** {"Review required — critical control failures detected in regulatory datasets." if crit_exc > 0 else "Satisfactory — no critical failures in regulatory datasets."}
""")

    # 4 — Recommended Actions
    st.markdown("---")
    st.markdown("### 4. Recommended Actions")
    actions = []
    if crit_exc > 0:
        actions.append(("Immediate",       f"Escalate {crit_exc} critical exception(s) to the Chief Data Officer. Halt use of affected datasets in regulatory reports until resolved."))
    if on_watchlist > 0:
        det_names = wl_df[wl_df["watchlist_status"] == "Watchlist"]["dataset_name"].tolist()
        actions.append(("High Priority",   f"Assign Data Stewards to investigate: {', '.join(det_names)}. Root cause analysis within 5 business days."))
    if sla_breach > 0:
        actions.append(("High Priority",   f"Address {sla_breach} SLA breach(es). Review escalation protocols with relevant teams."))
    actions.append(("Medium Priority",     "Engage Source System Team to review upstream feed stability and add automated alerting for feed delays."))
    actions.append(("Medium Priority",     "Schedule Data Steward review for all Timeliness controls with repeated failures."))
    actions.append(("Standard",            "Update Governance Maturity roadmap targeting 'Managed' level next quarter."))

    p_colours = {"Immediate":"#e74c3c","High Priority":"#f39c12","Medium Priority":"#3498db","Standard":"#95a5a6"}
    for priority, action in actions:
        pc = p_colours.get(priority, "#aaa")
        st.markdown(f"""
        <div style='background:#16213e;border-radius:8px;padding:12px 16px;margin-bottom:8px;border-left:4px solid {pc};'>
          <span style='color:{pc};font-weight:bold;font-size:13px;'>{priority}</span>
          <p style='color:#ddd;margin:4px 0 0;font-size:14px;'>{action}</p>
        </div>
        """, unsafe_allow_html=True)

    # 5 — Expected Impact
    st.markdown("---")
    st.markdown("### 5. Expected Impact")
    sla_cur = round(((len(rem_df) - sla_breach) / max(len(rem_df), 1)) * 100, 1) if len(rem_df) > 0 else 100.0
    st.markdown(f"""
If recommended actions are executed within **30 days**:

| Metric | Current | Target |
|--------|---------|--------|
| Data Trust Score | {overall_trust}/100 | 90+/100 |
| Datasets on Watchlist | {on_watchlist} | 0 |
| Critical Exceptions | {crit_exc} | 0 |
| SLA Compliance | {sla_cur}% | 98%+ |
| Governance Maturity | {maturity['maturity_level']} | Managed |

Resolution of watchlist datasets will reduce audit risk exposure and improve confidence in regulatory and executive reporting.
""")

    st.markdown("---")
    st.success("This report is auto-generated from live governance data.")

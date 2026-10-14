"""Interactive graphs for the AML monitoring analysis outputs."""
from pathlib import Path
import json
import pandas as pd
import plotly.express as px
import streamlit as st

R=Path(__file__).parent/"reports"
st.set_page_config(page_title="AML Monitoring Lab",layout="wide")
st.title("AML Transaction Monitoring Lab")
st.caption("Exploratory analysis of synthetic AMLSim transactions; not a real-world monitoring system.")
required=[R/"monitoring_by_step.csv",R/"monitoring_by_type.csv",R/"holdout_by_type.csv",R/"model_metrics.json"]
hourly=pd.read_csv(required[0]) if required[0].exists() else pd.DataFrame(columns=["step","transaction_count","sar_pattern_count","rule_alerts"])
types=pd.read_csv(required[1]) if required[1].exists() else pd.DataFrame(columns=["type","sar_pattern_count","rule_alerts"])
holdout=pd.read_csv(required[2]) if required[2].exists() else pd.DataFrame()
metrics=json.loads(required[3].read_text(encoding="utf-8")) if required[3].exists() else {"strategies":[],"train_rows":0,"test_rows":0,"supervised_average_precision":0.0}
if not all(p.exists() for p in required):
    st.info("Monitoring and strategy tabs fill in after analysis. The Data quality tab is available after running validation.")
tab1,tab2,tab3,tab4=st.tabs(["Monitoring overview","Strategy comparison","Network view","Data quality"])
with tab1:
    c1,c2=st.columns(2)
    with c1:
        st.plotly_chart(px.line(hourly,x="step",y=["transaction_count","sar_pattern_count","rule_alerts"],title="Activity and alerts by simulation step"),use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(types,x="type",y=["sar_pattern_count","rule_alerts"],barmode="group",title="Pattern labels and rule alerts by transaction type"),use_container_width=True)
    st.dataframe(types,use_container_width=True,hide_index=True)
with tab2:
    strategies=pd.DataFrame(metrics["strategies"],columns=["method","setting","alert_rate","recall","sar_pattern_amount_flagged","precision"])
    left,right=st.columns(2)
    with left:
        st.plotly_chart(px.scatter(strategies,x="alert_rate",y="recall",color="method",size="sar_pattern_amount_flagged",hover_name="setting",title="Detection coverage vs alert rate"),use_container_width=True)
    with right:
        st.plotly_chart(px.bar(strategies,x="method",y="sar_pattern_amount_flagged",color="setting",barmode="group",title="Labeled-pattern transaction amount flagged"),use_container_width=True)
    st.plotly_chart(px.bar(strategies,x="setting",y=["precision","recall"],color="method",barmode="group",title="Precision and recall by strategy setting"),use_container_width=True)
    st.dataframe(strategies,use_container_width=True,hide_index=True)
    st.caption(f"Chronological evaluation: {metrics['train_rows']:,} earlier training rows; {metrics['test_rows']:,} later holdout rows. Average precision: {metrics['supervised_average_precision']:.3f}.")
with tab3:
    net=R/"network_accounts_top.csv"
    if net.exists():
        accounts=pd.read_csv(net)
        st.plotly_chart(px.scatter(accounts,x="in_degree",y="out_degree",size="in_amount",color="pagerank",hover_name="account",title="High-connectivity accounts in directed flow graph"),use_container_width=True)
        st.dataframe(accounts.head(100),use_container_width=True,hide_index=True)
with tab4:
    quality_path=R/"data_quality_summary.json"
    if not quality_path.exists():
        st.info("Run python -m aml_monitoring.validate_data --input data/raw/transactions.csv --output reports to create data quality charts.")
    else:
        quality=json.loads(quality_path.read_text(encoding="utf-8"))
        if quality.get("required_columns_missing"):
            st.error(f"Required fields are missing: {quality['required_columns_missing']}")
        st.metric("Rows inspected",f"{quality.get('row_count',0):,}")
        st.metric("Ready for pipeline","Yes" if quality.get("ready_for_pipeline") else "No — inspect flags below")
        qc=R/"data_quality_columns.csv"
        if qc.exists():
            missing=pd.read_csv(qc)
            st.plotly_chart(px.bar(missing,x="column",y="missing_rate",title="Missing or blank values by column",labels={"missing_rate":"Missing rate"}),use_container_width=True)
        qstep=R/"data_quality_by_step.csv"
        if qstep.exists():
            step_data=pd.read_csv(qstep)
            st.plotly_chart(px.line(step_data,x="step",y=["transaction_count","positive_labels"],title="Transaction volume and positive simulator labels by step"),use_container_width=True)
        amount_sample=R/"data_quality_amount_sample.csv"
        if amount_sample.exists():
            sample=pd.read_csv(amount_sample)
            st.plotly_chart(px.histogram(sample,x="amount",nbins=50,title="Sampled transaction amount distribution"),use_container_width=True)
        checks={k:quality.get(k) for k in ["invalid_step_count","invalid_amount_count","nonpositive_amount_count","invalid_label_count","required_field_missing_count","duplicate_transaction_count","positive_label_count","negative_label_count"]}
        st.subheader("Quality check results")
        st.json(checks)
        st.caption("Duplicates and nonpositive amounts are review flags, not automatic proof that a row is invalid. Confirm the source schema and data meaning before changing records.")
st.warning("Simulator labels are not confirmed suspicious activity. Do not treat these scores, example thresholds, or visual patterns as production recommendations. Read docs/model_white_paper.md.")

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
if not all(p.exists() for p in required):
    st.info("Run the prepare and analyze commands in README.md to generate the report files.")
    st.stop()
hourly,types,holdout=[pd.read_csv(p) for p in required[:3]]
metrics=json.loads(required[3].read_text(encoding="utf-8"))
tab1,tab2,tab3=st.tabs(["Monitoring overview","Strategy comparison","Network view"])
with tab1:
    c1,c2=st.columns(2)
    with c1:
        st.plotly_chart(px.line(hourly,x="step",y=["transaction_count","sar_pattern_count","rule_alerts"],title="Activity and alerts by simulation step"),use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(types,x="type",y=["sar_pattern_count","rule_alerts"],barmode="group",title="Pattern labels and rule alerts by transaction type"),use_container_width=True)
    st.dataframe(types,use_container_width=True,hide_index=True)
with tab2:
    strategies=pd.DataFrame(metrics["strategies"])
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
st.warning("Simulator labels are not confirmed suspicious activity. Do not treat these scores, example thresholds, or visual patterns as production recommendations. Read docs/model_white_paper.md.")

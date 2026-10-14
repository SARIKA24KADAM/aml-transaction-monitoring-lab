"""Create transparent rule, supervised, anomaly, and network analysis outputs."""
import argparse
import json
from pathlib import Path

import duckdb
import networkx as nx
import numpy as np
import pandas as pd
import yaml
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC = ["amount", "oldbalanceOrig", "oldbalanceDest", "prior_send_count", "prior_send_amount", "prior_receive_count", "prior_receive_amount", "prior_orig_receive_count", "prior_orig_receive_amount"]
CATEGORICAL = ["type"]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--config",default="config/monitoring.yml")
    args=parser.parse_args()
    out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    cfg=yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    frame=duckdb.connect().execute("SELECT * FROM read_parquet(?) ORDER BY step",[str(Path(args.input).resolve())]).df()
    sender_ratio=frame.prior_send_amount / frame.prior_orig_receive_amount.clip(lower=1)
    pass_through=(frame.prior_orig_receive_amount >= cfg["pass_through_min_inflow"]) & sender_ratio.between(cfg["pass_through_ratio_low"],cfg["pass_through_ratio_high"])
    frame["rule_alert"]=(
        (frame.prior_send_count >= cfg["high_activity_sender_count"]) |
        (frame.prior_receive_count >= cfg["high_activity_receiver_count"]) |
        pass_through
    )
    frame["rule_reason"]=""
    frame.loc[frame.prior_send_count >= cfg["high_activity_sender_count"],"rule_reason"] += "high_prior_send_activity;"
    frame.loc[frame.prior_receive_count >= cfg["high_activity_receiver_count"],"rule_reason"] += "high_prior_receive_activity;"
    frame.loc[pass_through,"rule_reason"] += "possible_pass_through;"

    cutoff=frame.step.quantile(.8)
    train=frame[frame.step <= cutoff].copy(); test=frame[frame.step > cutoff].copy()
    ytrain=train.isSAR.astype(int); ytest=test.isSAR.astype(int)
    if ytrain.nunique()<2 or ytest.nunique()<2:
        raise ValueError("Both chronological train and test partitions need positive and negative labels; choose a larger or different AMLSim sample.")

    model=make_pipeline(make_preprocessor(),LogisticRegression(max_iter=400,class_weight="balanced"))
    model.fit(train[NUMERIC+CATEGORICAL],ytrain)
    test["supervised_score"]=model.predict_proba(test[NUMERIC+CATEGORICAL])[:,1]

    normal=train[train.isSAR==0]
    anomaly=make_pipeline(make_preprocessor(),IsolationForest(n_estimators=150,contamination="auto",random_state=17,n_jobs=-1))
    anomaly.fit(normal[NUMERIC+CATEGORICAL])
    test["anomaly_score"]=-anomaly.decision_function(test[NUMERIC+CATEGORICAL])

    strategies=[]
    for method,scores in [("supervised",test.supervised_score.to_numpy()),("unsupervised",test.anomaly_score.to_numpy())]:
        for q in cfg["supervised_thresholds"]:
            threshold=float(np.quantile(scores,1-q)); pred=scores>=threshold
            strategies.append(metrics_row(method,f"top_{int(q*100)}pct",pred,ytest.to_numpy(),test.amount.to_numpy(),threshold))
    strategies.append(metrics_row("transparent_rules","configured",test.rule_alert.to_numpy(bool),ytest.to_numpy(),test.amount.to_numpy(),None))
    model_metrics={"train_rows":len(train),"test_rows":len(test),"time_cutoff":float(cutoff),"test_prevalence":float(ytest.mean()),
        "supervised_roc_auc":float(roc_auc_score(ytest,test.supervised_score)),"supervised_average_precision":float(average_precision_score(ytest,test.supervised_score)),"strategies":strategies}
    (out/"model_metrics.json").write_text(json.dumps(model_metrics,indent=2),encoding="utf-8")
    test[["step","type","amount","nameOrig","nameDest","isSAR","alertID","rule_alert","rule_reason","supervised_score","anomaly_score"]].to_parquet(out/"scored_holdout.parquet",index=False)
    make_reports(frame,test,out)
    network_summary(frame,out)
    print(json.dumps(model_metrics,indent=2))

def make_preprocessor():
    return ColumnTransformer([
        ("numeric",make_pipeline(SimpleImputer(strategy="median"),StandardScaler()),NUMERIC),
        ("type",OneHotEncoder(handle_unknown="ignore"),CATEGORICAL)])

def metrics_row(method,label,pred,y,amount,threshold):
    return {"method":method,"setting":label,"threshold_or_quantile":threshold,"alerts":int(pred.sum()),"alert_rate":float(pred.mean()),
        "precision":float(precision_score(y,pred,zero_division=0)),"recall":float(recall_score(y,pred,zero_division=0)),
        "sar_pattern_amount_flagged":float(amount[pred & (y==1)].sum()),"legitimate_alerts":int((pred & (y==0)).sum())}

def make_reports(full,test,out):
    full.groupby("step",as_index=False).agg(transaction_count=("amount","size"),transaction_amount=("amount","sum"),sar_pattern_count=("isSAR","sum"),rule_alerts=("rule_alert","sum")).to_csv(out/"monitoring_by_step.csv",index=False)
    full.groupby("type",as_index=False).agg(transaction_count=("amount","size"),transaction_amount=("amount","sum"),sar_pattern_count=("isSAR","sum"),rule_alerts=("rule_alert","sum")).to_csv(out/"monitoring_by_type.csv",index=False)
    test.groupby("type",as_index=False).agg(test_transactions=("amount","size"),sar_patterns=("isSAR","sum"),rule_alerts=("rule_alert","sum"),avg_supervised_score=("supervised_score","mean"),avg_anomaly_score=("anomaly_score","mean")).to_csv(out/"holdout_by_type.csv",index=False)

def network_summary(frame,out):
    edges=frame.groupby(["nameOrig","nameDest"],as_index=False).agg(tx_count=("amount","size"),total_amount=("amount","sum"))
    graph=nx.DiGraph()
    graph.add_weighted_edges_from((r.nameOrig,r.nameDest,float(r.total_amount)) for r in edges.itertuples(index=False))
    rows=[]
    for node in graph.nodes:
        rows.append({"account":node,"in_degree":graph.in_degree(node),"out_degree":graph.out_degree(node),
            "in_amount":sum(d.get("weight",0) for _,_,d in graph.in_edges(node,data=True)),
            "out_amount":sum(d.get("weight",0) for _,_,d in graph.out_edges(node,data=True)),"pagerank":0.0})
    if graph.number_of_nodes() <= 100000:
        pr=nx.pagerank(graph,weight="weight",max_iter=100)
        for row in rows: row["pagerank"]=pr.get(row["account"],0.0)
    pd.DataFrame(rows).sort_values(["in_degree","out_degree"],ascending=False).head(5000).to_csv(out/"network_accounts_top.csv",index=False)
    pd.DataFrame([{"accounts":graph.number_of_nodes(),"directed_pairs":graph.number_of_edges(),"transactions":len(frame),"components_undirected":nx.number_connected_components(graph.to_undirected())}]).to_csv(out/"network_summary.csv",index=False)

if __name__=="__main__": main()

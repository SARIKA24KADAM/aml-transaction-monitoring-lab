"""Profile an AMLSim CSV and write quality summaries for review."""
import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd

REQUIRED = ["step", "type", "amount", "nameOrig", "nameDest", "isSAR", "alertID", "oldbalanceOrig", "oldbalanceDest"]

def qi(value):
    """Quote a SQL identifier safely."""
    return '"' + value.replace('"', '""') + '"'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",required=True)
    parser.add_argument("--output",default="reports")
    args=parser.parse_args()
    src=Path(args.input).resolve(); out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    path=str(src).replace("'","''"); con=duckdb.connect()
    relation=f"read_csv_auto('{path}', header=true)"
    columns=[r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {relation}").fetchall()]
    missing=sorted(set(REQUIRED)-set(columns))
    if missing:
        report={"file":src.name,"columns_found":columns,"required_columns_missing":missing,"ready_for_pipeline":False}
        (out/"data_quality_summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        raise ValueError(f"Required columns missing: {missing}. See {out / 'data_quality_summary.json'}")

    null_exprs=[]
    for col in columns:
        q=qi(col)
        null_exprs.append(f"COUNT(*) FILTER (WHERE {q} IS NULL OR TRIM(CAST({q} AS VARCHAR))='') AS {qi(col+'_missing')}")
    null_row=con.execute(f"SELECT {', '.join(null_exprs)} FROM {relation}").df().iloc[0].to_dict()
    n=con.execute(f"""SELECT COUNT(*) AS row_count,
      COUNT(*) FILTER (WHERE TRY_CAST(step AS DOUBLE) IS NULL) AS invalid_step_count,
      COUNT(*) FILTER (WHERE TRY_CAST(amount AS DOUBLE) IS NULL) AS invalid_amount_count,
      COUNT(*) FILTER (WHERE TRY_CAST(amount AS DOUBLE) <= 0) AS nonpositive_amount_count,
      COUNT(*) FILTER (WHERE lower(CAST(isSAR AS VARCHAR)) NOT IN ('1','0','true','false','yes','no')) AS invalid_label_count,
      COUNT(*) FILTER (WHERE lower(CAST(isSAR AS VARCHAR)) IN ('1','true','yes')) AS positive_label_count,
      COUNT(*) FILTER (WHERE lower(CAST(isSAR AS VARCHAR)) IN ('0','false','no')) AS negative_label_count,
      MIN(TRY_CAST(step AS DOUBLE)) AS min_step, MAX(TRY_CAST(step AS DOUBLE)) AS max_step,
      MIN(TRY_CAST(amount AS DOUBLE)) AS min_amount, MAX(TRY_CAST(amount AS DOUBLE)) AS max_amount
      FROM {relation}""").df().iloc[0].to_dict()
    key_cols=[c for c in ["step","type","amount","nameOrig","nameDest","alertID"] if c in columns]
    group=", ".join(qi(c) for c in key_cols)
    duplicate_count=con.execute(f"SELECT COALESCE(SUM(n-1),0) FROM (SELECT COUNT(*) n FROM {relation} GROUP BY {group} HAVING COUNT(*)>1)").fetchone()[0]
    required_missing_count=sum(int(null_row.get(c+"_missing",0)) for c in REQUIRED)
    summary={"file":src.name,"row_count":int(n["row_count"]),"columns":columns,"required_columns_missing":[],
      "invalid_step_count":int(n["invalid_step_count"]),"invalid_amount_count":int(n["invalid_amount_count"]),
      "nonpositive_amount_count":int(n["nonpositive_amount_count"]),"invalid_label_count":int(n["invalid_label_count"]),
      "positive_label_count":int(n["positive_label_count"]),"negative_label_count":int(n["negative_label_count"]),
      "duplicate_transaction_count":int(duplicate_count),"min_step":n["min_step"],"max_step":n["max_step"],
      "min_amount":n["min_amount"],"max_amount":n["max_amount"],"required_field_missing_count":required_missing_count,
      "ready_for_pipeline":int(n["row_count"])>0 and required_missing_count==0 and all(int(n[k])==0 for k in ["invalid_step_count","invalid_amount_count","invalid_label_count"])}
    (out/"data_quality_summary.json").write_text(json.dumps(summary,indent=2,default=str),encoding="utf-8")
    missing_rows=[{"column":k.removesuffix("_missing"),"missing_count":int(v),"missing_rate":float(v)/summary["row_count"] if summary["row_count"] else 0.0} for k,v in null_row.items()]
    pd.DataFrame(missing_rows).sort_values("missing_rate",ascending=False).to_csv(out/"data_quality_columns.csv",index=False)
    con.execute(f"SELECT CAST(step AS BIGINT) step,COUNT(*) transaction_count,SUM(TRY_CAST(amount AS DOUBLE)) total_amount,SUM(CASE WHEN lower(CAST(isSAR AS VARCHAR)) IN ('1','true','yes') THEN 1 ELSE 0 END) positive_labels FROM {relation} GROUP BY step ORDER BY step").df().to_csv(out/"data_quality_by_step.csv",index=False)
    con.execute(f"SELECT TRY_CAST(amount AS DOUBLE) amount FROM {relation} USING SAMPLE 20000 ROWS").df().to_csv(out/"data_quality_amount_sample.csv",index=False)
    print(json.dumps(summary,indent=2,default=str))

if __name__=="__main__": main()

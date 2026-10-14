"""Validate AMLSim transaction logs and derive prior-activity features."""
import argparse
from pathlib import Path
import duckdb

REQUIRED = ["step", "type", "amount", "nameOrig", "nameDest", "isSAR", "alertID", "oldbalanceOrig", "oldbalanceDest"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(args.input).resolve()
    target = Path(args.output).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    escaped = str(source).replace("'", "''")
    columns = [row[0] for row in con.execute(f"DESCRIBE SELECT * FROM read_csv_auto('{escaped}', header=true)").fetchall()]
    missing = sorted(set(REQUIRED) - set(columns))
    if missing:
        raise ValueError(f"Missing required AMLSim columns: {missing}. Available columns: {columns}")
    out = str(target).replace("'", "''")
    con.execute(f"""
      COPY (
        WITH tx AS (
          SELECT *, CAST(step AS BIGINT) AS step_num,
                 CASE WHEN lower(CAST(isSAR AS VARCHAR)) IN ('1','true','yes') THEN 1 ELSE 0 END AS target_sar
          FROM read_csv_auto('{escaped}', header=true)
        ),
        send AS (
          SELECT *, COUNT(*) OVER (PARTITION BY nameOrig ORDER BY step_num
            RANGE BETWEEN 24 PRECEDING AND 1 PRECEDING) AS prior_send_count,
            SUM(amount) OVER (PARTITION BY nameOrig ORDER BY step_num
            RANGE BETWEEN 24 PRECEDING AND 1 PRECEDING) AS prior_send_amount
          FROM tx
        ),
        receive_raw AS (
          SELECT step_num, CAST(nameDest AS VARCHAR) AS account_id,
            COUNT(*) OVER (PARTITION BY nameDest ORDER BY step_num
              RANGE BETWEEN 24 PRECEDING AND 1 PRECEDING) AS prior_receive_count,
            SUM(amount) OVER (PARTITION BY nameDest ORDER BY step_num
              RANGE BETWEEN 24 PRECEDING AND 1 PRECEDING) AS prior_receive_amount
          FROM tx
        ),
        receive AS (
          SELECT DISTINCT step_num, account_id, prior_receive_count, prior_receive_amount
          FROM receive_raw
        )
        SELECT s.step_num AS step, CAST(s.type AS VARCHAR) AS type,
          CAST(s.amount AS DOUBLE) AS amount,
          CAST(s.nameOrig AS VARCHAR) AS nameOrig, CAST(s.nameDest AS VARCHAR) AS nameDest,
          CAST(s.alertID AS VARCHAR) AS alertID,
          CAST(s.target_sar AS INTEGER) AS isSAR,
          CAST(s.oldbalanceOrig AS DOUBLE) AS oldbalanceOrig,
          CAST(s.oldbalanceDest AS DOUBLE) AS oldbalanceDest,
          COALESCE(s.prior_send_count,0) AS prior_send_count,
          COALESCE(s.prior_send_amount,0) AS prior_send_amount,
          COALESCE(r_dest.prior_receive_count,0) AS prior_receive_count,
          COALESCE(r_dest.prior_receive_amount,0) AS prior_receive_amount,
          COALESCE(r_orig.prior_receive_count,0) AS prior_orig_receive_count,
          COALESCE(r_orig.prior_receive_amount,0) AS prior_orig_receive_amount
        FROM send s
        LEFT JOIN receive r_dest
          ON s.step_num=r_dest.step_num AND CAST(s.nameDest AS VARCHAR)=r_dest.account_id
        LEFT JOIN receive r_orig
          ON s.step_num=r_orig.step_num AND CAST(s.nameOrig AS VARCHAR)=r_orig.account_id
      ) TO '{out}' (FORMAT PARQUET)
    """)
    print(f"Wrote prepared transactions to {target}")

if __name__ == "__main__":
    main()

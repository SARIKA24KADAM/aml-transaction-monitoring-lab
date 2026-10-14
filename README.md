# AML Transaction Monitoring Lab

A portfolio project for exploring AML transaction monitoring using synthetic transactions, transparent behavioral rules, supervised learning, unsupervised anomaly scoring, and account-network analysis.

## Data

This project uses transaction logs from [IBM AMLSim](https://github.com/IBM/AMLSim). AMLSim generates synthetic transactions and known laundering patterns for research and model experimentation. The sample data does not represent real customers, institutions, or regulatory outcomes. Download an AMLSim sample and copy its transaction log to `data/raw/transactions.csv`. For an initial run, choose a manageable sample such as 100,000 edges.

Expected columns are `step,type,amount,nameOrig,oldbalanceOrig,newbalanceOrig,nameDest,oldbalanceDest,newbalanceDest,isSAR,alertID`, matching the transaction-log header documented by AMLSim. If a sample uses different names, map them in `src/aml_monitoring/prepare.py` before running.

## Run

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m aml_monitoring.prepare --input data/raw/transactions.csv --output data/processed/transactions.parquet
python -m aml_monitoring.analyze --input data/processed/transactions.parquet --output reports
streamlit run dashboard.py
```

The analysis writes rule and model comparisons, account summaries, and graph/network summaries into `reports/`. The dashboard charts those generated results.

## What it demonstrates

- EDA and data quality checks for transaction events.
- Point-in-time sender/receiver activity features.
- Transparent behavioral monitoring rules with configurable thresholds.
- Supervised classification and unsupervised anomaly ranking.
- Directed transaction-network features and suspicious-neighborhood exploration.
- Alert-volume and detection trade-off visualizations.
- A model white paper and explicit governance limitations.

## Important limitations

This is an educational prototype, not a production monitoring solution or regulatory interpretation. AMLSim labels indicate simulator-generated patterns, not confirmed real-world suspicious activity. Performance on synthetic data does not establish effectiveness in a real program. Thresholds in `config/monitoring.yml` are examples only. See `docs/model_white_paper.md` and `docs/risk_and_limitations.md` before interpreting any results.

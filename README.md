# AML Transaction Monitoring Lab

A portfolio project for exploring AML transaction monitoring using synthetic transactions, transparent behavioral rules, supervised learning, unsupervised anomaly scoring, and account-network analysis.

## Data

This project uses transaction logs from [IBM AMLSim](https://github.com/IBM/AMLSim). AMLSim generates synthetic transactions and known laundering patterns for research and model experimentation. The sample data does not represent real customers, institutions, or regulatory outcomes. Download an AMLSim sample and copy its transaction log to data/raw/transactions.csv. For an initial run, choose a manageable sample such as 100,000 edges.

Expected columns follow the AMLSim transaction log: step, type, amount, sender/recipient identifiers, pre/post balances, isSAR, and alertID. If a sample uses different names, map them in the preparation script before running.

## Run

\`\`\`bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m aml_monitoring.validate_data --input data/raw/transactions.csv --output reports
python -m aml_monitoring.prepare --input data/raw/transactions.csv --output data/processed/transactions.parquet
python -m aml_monitoring.analyze --input data/processed/transactions.parquet --output reports
streamlit run dashboard.py
\`\`\`

Run validation first. It checks schema and data quality and produces summary files. Preparation writes historical features, analysis compares rules and models, and the dashboard visualizes monitoring, model performance, network structure, and data quality.

Read the [complete walkthrough](docs/complete_walkthrough.md) for the purpose, data checks, charts, metrics, outputs, and interpretation process.

## What it demonstrates

- Exploratory and data quality checks for transaction events.
- Missing-value, duplicate-row, invalid-field, label-balance, amount, and time-series checks.
- Point-in-time sender/receiver activity features.
- Configurable behavioral monitoring rules.
- Supervised classification and unsupervised anomaly ranking.
- Directed transaction-network analysis.
- Alert-volume and detection trade-off visualizations.
- A model white paper and governance limitations.

## Important limitations

This is an educational prototype, not a production monitoring solution or regulatory interpretation. AMLSim labels indicate simulator-generated patterns, not confirmed real-world suspicious activity. Performance on synthetic data does not establish effectiveness in a real program. Thresholds in the monitoring configuration are examples only. Review the model white paper and risk limitations before interpreting results.

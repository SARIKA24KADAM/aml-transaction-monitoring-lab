# Project guide

## What this project does

It analyzes simulated banking transactions to show how a transaction monitoring prototype can combine transparent rules, supervised learning, anomaly ranking, SQL-style data preparation, and graph analysis. It creates summary tables and graphs for comparing detection coverage with alert volume.

## Workflow

1. Download an AMLSim transaction sample and save it to `data/raw/transactions.csv`.
2. Run `prepare.py` to validate columns and derive prior sender/receiver activity.
3. Run `analyze.py` to create rule alerts, train/evaluate models on a chronological split, and summarize the account network.
4. Open the Streamlit dashboard to explore monitoring trends, method comparisons, and network summaries.
5. Review the model white paper before interpreting the results.

## Key concepts

- **Transaction monitoring:** look for behavior or patterns that merit investigation; a score alone is not a determination.
- **Typology:** an example pattern of activity associated with a possible laundering method. The simulator supplies generated patterns, not real case evidence.
- **Supervised model:** learns to rank examples using known simulator labels.
- **Unsupervised anomaly score:** ranks unusual observations without treating its score as probability of money laundering.
- **Chronological holdout:** evaluate later simulation steps after fitting on earlier steps to better mimic future monitoring.
- **Alert rate:** percentage of rows that a strategy would flag. It is a workload proxy, not the count of real investigations.
- **Precision / recall:** precision describes the share of flagged rows matching the synthetic label; recall describes the share of synthetic labeled rows flagged.
- **Network analysis:** represent origin accounts as sources, recipient accounts as destinations, and transactions as directed weighted edges.

## Generated outputs

- `model_metrics.json`: metrics, threshold/quantile comparisons, and time split.
- `scored_holdout.parquet`: holdout rows with synthetic labels, rule results, and model scores.
- `monitoring_by_step.csv`: activity trends by simulator step.
- `monitoring_by_type.csv` and `holdout_by_type.csv`: segment summaries.
- `network_accounts_top.csv`: account connectivity and flow totals for exploration.
- `network_summary.csv`: graph scale summary.

## What not to conclude

Do not infer real-world risk, regulatory compliance, a recommended threshold, or expected alert quality from the output. Simulator labels are generated and may not resemble investigations. The graph is descriptive, not a complete point-in-time model. See [model white paper](model_white_paper.md) and [risk limitations](risk_and_limitations.md).

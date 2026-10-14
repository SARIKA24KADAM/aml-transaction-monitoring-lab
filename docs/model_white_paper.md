# Model white paper: AML monitoring strategy comparison

## Executive summary

This prototype compares three approaches on synthetic AMLSim transaction logs: transparent behavioral rules, supervised logistic regression, and an unsupervised Isolation Forest score. The goal is to demonstrate a documented monitoring-model lifecycle, not to claim a production-ready AML control.

## Intended use

Support portfolio analysis and learning about transaction monitoring design, feature preparation, alert-capacity trade-offs, network analysis, and model communication. It is not intended to make real customer decisions, file regulatory reports, or replace investigator judgment.

## Data and target

Input fields follow the AMLSim transaction-log schema: simulation step, transaction type and amount, origin/destination account, balances, simulator SAR-pattern label, and alert identifier. The binary target is `isSAR`, treated as a simulator-provided pattern label. It does not mean that a real customer was suspicious, that an analyst confirmed a case, or that a filing was made.

## Methods

- **Transparent behavioral rules:** prior sender/receiver activity and approximate pass-through behavior are compared to configurable example cutoffs.
- **Supervised model:** logistic regression estimates simulator-label ranking from amount, pre-transaction balances, transaction type, and prior account activity.
- **Unsupervised model:** Isolation Forest ranks unusual observations after fitting on non-pattern training rows. Its score is an anomaly ranking, not a calibrated probability.
- **Network analysis:** directed transaction edges are summarized into in/out degree, flow amounts, connected components, and PageRank where graph size allows.

## Evaluation design

Data is ordered by simulation step and divided chronologically: earlier rows are training and later rows are holdout. Logistic regression is assessed with ROC AUC and average precision, plus precision, recall, alert rate, legitimate alerts, and labeled-pattern transaction amount flagged at several score quantiles. Rule results use the same holdout period. Quantile settings are alert-rate scenarios, not statistically optimized or approved operating thresholds.

## Feature and label controls

Account IDs are excluded from predictive input columns. Prior activity windows exclude the current transaction and use the preceding 24 simulation steps. Post-transaction balances are excluded. `isSAR` is used only as a target/outcome; `alertID` is retained for case context but excluded from predictors. A real application would require event-time definitions, label maturity rules, investigation outcomes, feature lineage, and independent leakage testing.

## Limitations

- Data is synthetic and has simulator-defined laundering patterns.
- Synthetic positive labels may be unusually clean compared with delayed and incomplete real investigation outcomes.
- Transaction flows and client/product coverage may not reflect a real institution.
- Rules are simple examples and do not encode jurisdiction, customer risk, sanctions, or policy requirements.
- Account-level network summaries use the complete input window; they are exploratory and must not be used as point-in-time predictive features without a time-aware redesign.
- Anomaly scores are not probabilities; threshold quantiles do not establish value or risk appetite.
- No investigator feedback, SAR quality, customer impact, false-positive operational costs, or regulatory findings are available.

## Monitoring and review recommendations

For a production program, establish approved data definitions, model ownership, independent validation, benchmark challengers, threshold rationale, alert capacity and service-level measures, segment performance, drift and data-quality monitoring, audit logs, escalation criteria, and rollback/change controls. Engage compliance, model risk, privacy, security, and operations stakeholders. This project does not assert regulatory compliance.

## Reproducibility

Record the AMLSim sample/version, data file checksum, configuration, dependency versions, train/holdout boundaries, and output metrics for each run. The raw file is intentionally excluded from version control.

# Risk, governance, and limitations

This is a synthetic-data portfolio prototype. It is not a real AML monitoring system, legal interpretation, or regulatory recommendation.

| Risk | Project treatment / limitation |
|---|---|
| Synthetic labels mistaken for confirmed cases | Label is explicitly described as simulator-provided pattern ground truth only. |
| Alert overload | Report alert rates and alert counts; production capacity is not supplied. |
| Thresholds misread as policy | YAML values are examples, not institution thresholds. |
| Leakage | Current event excluded from rolling windows; post-event balances, labels, and alert IDs excluded from predictors. |
| Network feature look-ahead | Full-period graph metrics are descriptive only; not used as predictive features. |
| Explainability | Transparent rule reasons accompany rule alerts; model scores still require explanation and review before use. |
| Uneven segment performance | Show transaction type summaries; synthetic population cannot establish fairness or client-level impact. |
| Privacy | Use only public synthetic input. Never add confidential customer data to this repository. |

Any real use would need approved data access, detailed business requirements, documented alert rationale, independent validation, legal/compliance and model-risk review, privacy/security review, investigator workflow assessment, ongoing monitoring, auditability, and controlled change/rollback practices.

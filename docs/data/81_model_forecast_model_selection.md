# `forecast_model_selection`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.forecast_model_selection`
- **Sample:** [forecast_model_selection.jsonl](../../data/samples/forecast_model_selection.jsonl)
- **Grain and key:** one supervised model, forecast horizon, and finalization run.
- **Purpose:** freezes both supervised model specifications, settings, and validation evidence.

Version 2 contains regularized-linear and gradient-boosted-tree specifications at both one and three years. State and county trends remain baseline evidence and do not appear as selected project models. Keeping the specifications as a table makes the model roles and settings auditable.

Validation MAE values are cumulative log HPI change errors, not percentage-point errors. Later-period performance belongs in the evaluation scorecard and threshold table.

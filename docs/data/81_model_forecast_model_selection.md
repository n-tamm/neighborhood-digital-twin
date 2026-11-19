# `forecast_model_selection`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.forecast_model_selection`
- **Sample:** [forecast_model_selection.jsonl](../../data/samples/forecast_model_selection.jsonl)
- **Grain and key:** one forecast horizon and finalization run.
- **Purpose:** freezes the selected model family, estimator settings, and validation evidence before the locked temporal test is opened.

The two-row November 19, 2026 build selects a depth-2, 50-tree gradient-boosted model for the one-year horizon and the state current-trend baseline for the three-year horizon. These choices came from development validation; the locked results were not used to choose or tune them. Keeping the selection as a table makes that sequence auditable and prevents the application from silently substituting a model after seeing final-test performance.

The validation MAE values are cumulative log HPI change errors, not percentage-point errors. This table records a choice and its development evidence; final performance and publication eligibility belong in the locked scorecard and release gate.

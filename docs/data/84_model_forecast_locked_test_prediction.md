# `forecast_locked_test_prediction`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.forecast_locked_test_prediction`
- **Sample:** [forecast_locked_test_prediction.jsonl](../../data/samples/forecast_locked_test_prediction.jsonl)
- **Grain and key:** one tract, locked forecast origin, and horizon.
- **Purpose:** preserves the once-opened final temporal-test predictions, observed outcomes, and frozen uncertainty intervals.

The November 19 build contains 87,969 rows: 42,082 one-year predictions from 2024 to 2025 and 45,887 three-year predictions from 2022 to 2025. The champion model and interval method were fixed before these outcomes were scored. Rows retain the training cutoff and run lineage so a future rebuild cannot be confused with this final evaluation.

These predictions support final performance claims, subgroup review, and the release gate. They must not be used for additional tuning. Any later experimental model needs a newly defined evaluation protocol rather than repeatedly consulting these outcomes.

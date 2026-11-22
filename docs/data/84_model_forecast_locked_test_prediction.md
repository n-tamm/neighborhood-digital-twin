# `forecast_locked_test_prediction`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.forecast_locked_test_prediction`
- **Sample:** [forecast_locked_test_prediction.jsonl](../../data/samples/forecast_locked_test_prediction.jsonl)
- **Grain and key:** one tract, supervised model, later evaluation origin, and horizon.
- **Purpose:** preserves later-period predictions, observed outcomes, and frozen uncertainty intervals.

Version 2 scores both supervised models for the one-year 2024–2025 and three-year 2022–2025 evaluation periods. Rows retain model identity, training cutoff, and run lineage. Because these outcomes have already been inspected, the corrected run is later-period evaluation rather than a new untouched model-selection test.

These predictions support performance comparisons, subgroup review, and evaluation warnings. They must not be used for additional tuning.

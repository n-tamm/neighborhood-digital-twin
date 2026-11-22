# `forecast_current_prediction`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.forecast_current_prediction`
- **Sample:** [forecast_current_prediction.jsonl](../../data/samples/forecast_current_prediction.jsonl)
- **Grain and key:** one current model-ready tract, supervised model, and active horizon.
- **Purpose:** stores current point predictions and model-specific calibrated intervals.

Version 2 contains two rows per model-ready tract and horizon: one regularized-linear result and one gradient-boosted-tree result. All are scored from the 2025 origin and retain annualized values, cumulative log change, interval bounds, baseline context, cohort fields, and lineage.

Evaluation status is attached downstream, but current predictions are not deleted because a model misses a benchmark.

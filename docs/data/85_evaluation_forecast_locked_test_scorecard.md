# `forecast_locked_test_scorecard`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.forecast_locked_test_scorecard`
- **Sample:** [forecast_locked_test_scorecard.jsonl](../../data/samples/forecast_locked_test_scorecard.jsonl)
- **Grain and key:** one supervised model, horizon, evaluation slice, and slice value.
- **Purpose:** summarizes final point error, bias, baseline comparisons, and interval performance on the locked period.

Version 2 contains overall and diagnostic slices for regularized linear regression and gradient-boosted trees at both horizons. It records point error, bias, tail error, interval coverage, and interval width. State trend and zero change appear only as comparison fields.

The scorecard is evidence rather than a model-selection table. `forecast_evaluation_threshold` records which thresholds each model-horizon pair meets, but a warning does not suppress the result.

Overall results use 42,082 one-year observations and 45,887 three-year observations per model. Gradient-boosted-tree MAE is 0.0599 and 0.0980; regularized-linear MAE is 0.0632 and 0.1087. Diagnostic slices make up the remaining scorecard rows.

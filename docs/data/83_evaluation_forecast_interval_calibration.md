# `forecast_interval_calibration`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.forecast_interval_calibration`
- **Sample:** [forecast_interval_calibration.jsonl](../../data/samples/forecast_interval_calibration.jsonl)
- **Grain and key:** one supervised model, forecast horizon, and finalization run.
- **Purpose:** stores the residual quantile used to turn each point prediction into a calibrated interval.

The table contains one row for each supervised model and active horizon. The intended coverage is 90 percent. Each radius is estimated and applied only to the matching model-horizon pair.

This is a marginal uncertainty estimate across the calibration population, not a guarantee for every tract or subgroup. Whether the interval generalized to the unseen final period is evaluated separately in `forecast_locked_test_scorecard`.

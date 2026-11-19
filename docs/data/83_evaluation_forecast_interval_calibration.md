# `forecast_interval_calibration`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.forecast_interval_calibration`
- **Sample:** [forecast_interval_calibration.jsonl](../../data/samples/forecast_interval_calibration.jsonl)
- **Grain and key:** one forecast horizon and finalization run.
- **Purpose:** stores the residual quantile used to turn each point prediction into a calibrated interval.

The table contains one row for each active horizon. The intended coverage is 90 percent. The fitted cumulative-log-change radii are 0.1222 at one year and 0.2675 at three years, based on 41,017 and 39,563 reserved observations respectively. The same frozen radius is applied to locked-test and current predictions for that horizon.

This is a marginal uncertainty estimate across the calibration population, not a guarantee for every tract or subgroup. Whether the interval generalized to the unseen final period is evaluated separately in `forecast_locked_test_scorecard`.

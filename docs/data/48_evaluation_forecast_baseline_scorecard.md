# `forecast_baseline_scorecard`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.forecast_baseline_scorecard`
- **Sample:** [forecast_baseline_scorecard.jsonl](../../data/samples/forecast_baseline_scorecard.jsonl)
- **Grain and key:** one model, horizon, evaluation slice, and slice value.
- **Purpose:** compares forecast candidates on identical governed validation rows without opening
  the locked temporal tests.

The scorecard covers mean, root-mean-square, median, and 90th-percentile error; signed bias;
annualized percentage-point error; directional accuracy; R-squared; and MAE/RMSE skill relative
to the zero-change baseline. Directional results include the target direction base rate, the
majority-direction benchmark, and lift over that benchmark. It also records observation and tract
counts. Slices include overall performance, independent forecast-origin year, longitudinal
cohort, Census region, geographic transfer, housing composition, ACS uncertainty, and state.

These are point-forecast development metrics. Interval coverage and width belong here after the
reserved calibration workflow exists, while final locked-test results must remain unopened until
model and uncertainty choices are frozen.

The current build contains 1,248 rows. Directional accuracy must always be read beside
`majority_direction_accuracy` and `directional_accuracy_lift`: positive validation outcomes are so
common that the strongest models currently add almost no directional lift over the majority rule.

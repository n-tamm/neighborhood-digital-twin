# `historical_analogue_scorecard`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.historical_analogue_scorecard`
- **Sample:** [historical_analogue_scorecard.jsonl](../../data/samples/historical_analogue_scorecard.jsonl)
- **Grain and key:** one prediction method, horizon, evaluation slice, slice value, and historical
  analogue run.
- **Purpose:** compares later-outcome analogue estimates with fixed forecast baselines on exactly
  the same validation queries.

The scorecard includes query coverage, MAE, RMSE, median and 90th-percentile absolute error, signed
bias, R-squared, directional accuracy and lift, and skill relative to zero change. Slices cover
overall results, query origin, held-out versus development geography, Census region, and modeling
cohort.

Because this first experiment uses a small deterministic query sample, sliced rows can contain
few observations. Overall values are useful for development comparison, but no final model claim
or locked-test decision should rest on a tiny slice. One-year results remain primary and
three-year results secondary.

The November 3 development run contains 147 rows across overall, query-origin, geographic-role,
Census-region, and modeling-cohort slices.

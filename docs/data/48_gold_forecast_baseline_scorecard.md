# `gold_forecast_baseline_scorecard`

[Back to the data documentation index](README.md)

- **Layer:** Gold model development
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_forecast_baseline_scorecard`
- **Grain and key:** one model, horizon, evaluation slice, and slice value.
- **Purpose:** compares all initial forecast candidates on identical governed validation rows.

The scorecard reports MAE, RMSE, median absolute error, directional accuracy, row count, tract
count, and mean observed and predicted annualized change. Slices include overall performance,
stable versus broader post-2020 cohorts, held-out versus development states, housing composition,
and individual states. Small slices should be treated as diagnostics rather than model-selection
targets.

The table will receive a small sample in `data/samples/` after the first successful shared run.

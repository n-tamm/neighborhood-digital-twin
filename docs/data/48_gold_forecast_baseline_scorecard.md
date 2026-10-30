# `gold_forecast_baseline_scorecard`

[Back to the data documentation index](README.md)

- **Layer:** Gold model development
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_forecast_baseline_scorecard`
- **Sample:** [gold_forecast_baseline_scorecard.jsonl](../../data/samples/gold_forecast_baseline_scorecard.jsonl)
- **Grain and key:** one model, horizon, evaluation slice, and slice value.
- **Purpose:** compares all initial forecast candidates on identical governed validation rows.

The scorecard reports MAE, RMSE, median absolute error, directional accuracy, row count, tract
count, and mean observed and predicted annualized change. Slices include overall performance,
stable versus broader post-2020 cohorts, held-out versus development states, housing composition,
and individual states. Small slices should be treated as diagnostics rather than model-selection
targets.

The first run contains 1,068 rows across six methods. On the overall validation slice, the
regularized linear model has the lowest one-year MAE (0.0724), while the state-trend baseline is
narrowly best at three years (0.0666 versus 0.0679). The five-year linear result has an MAE of
0.0952 but remains exploratory because it was trained on only three independent origins. These
are development findings; the locked temporal tests remain unopened.

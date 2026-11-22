# `forecast_evaluation_threshold`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.forecast_evaluation_threshold`
- **Sample:** [forecast_evaluation_threshold.jsonl](../../data/samples/forecast_evaluation_threshold.jsonl)
- **Grain and key:** one supervised model, active horizon, and finalization run.
- **Purpose:** records reproducible evaluation thresholds and warnings without selecting or suppressing a model.

Each model-horizon pair is checked for at least 1,000 later-period observations, MAE no worse than zero change, and at least 80 percent empirical coverage for its nominal 90 percent interval.

The November 22, 2026 run contains all four model-horizon pairs. Both gradient-boosted-tree results and the three-year regularized-linear result meet every threshold. The one-year regularized-linear result remains published with `worse_than_zero_change_mae` because its MAE of 0.0632 is slightly above the zero-change MAE of 0.0627.

A failed check remains visible as an application warning. State or county trend is never promoted into the model slot, and the serving workflow retains both supervised models.

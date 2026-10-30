# `gold_forecast_baseline_prediction`

[Back to the data documentation index](README.md)

- **Layer:** Gold model development
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_forecast_baseline_prediction`
- **Sample:** [gold_forecast_baseline_prediction.jsonl](../../data/samples/gold_forecast_baseline_prediction.jsonl)
- **Grain and key:** one tract GEOID, forecast-origin year, horizon, and model.
- **Purpose:** preserves validation predictions from the fixed baseline ladder and initial
  regularized linear model so comparisons can be reproduced without rerunning training.
- **Guardrail:** this table contains only rows with `temporal_role = validation`. It does not
  contain calibration rows or the locked temporal tests.

Predictions use cumulative FHFA single-family HPI log change as the modeling scale. The companion
annualized percentage is for interpretation; model fitting and primary errors remain on the
cumulative log-change target. The table retains cohort, geography, housing-composition, target,
and lineage fields needed to audit subgroup results.

The first run contains 1,369,401 validation predictions across 59,562 tracts and six methods.
Large row volume comes from preserving model-level predictions for later residual, subgroup, and
map analysis; it is not a claim of independent temporal evidence.

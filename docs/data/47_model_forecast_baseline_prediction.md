# `forecast_baseline_prediction`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.forecast_baseline_prediction`
- **Sample:** [forecast_baseline_prediction.jsonl](../../data/samples/forecast_baseline_prediction.jsonl)
- **Grain and key:** one tract GEOID, forecast-origin year, horizon, and model.
- **Purpose:** preserves validation predictions from fixed baselines, regularized linear, and
  gradient-boosted-tree candidates so residual and subgroup analyses do not require retraining.
- **Guardrail:** only `temporal_role = validation` is allowed. Calibration rows and locked temporal
  tests are deliberately absent.

Predictions use cumulative FHFA single-family HPI log change as the modeling scale. Annualized
percentage predictions and errors make the results easier to interpret, while the source target,
cohort, geography, housing composition, and run lineage remain available for evaluation.

The November 7, 2026 run contains 1,588,340 validation predictions across 59,179 tracts and seven
methods. Validation targets are observed and remain within their forecast-origin calendar decade.
The model schema keeps these generated outputs separate from curated gold inputs and future
application-serving tables.

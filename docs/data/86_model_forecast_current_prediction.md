# `forecast_current_prediction`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.forecast_current_prediction`
- **Sample:** [forecast_current_prediction.jsonl](../../data/samples/forecast_current_prediction.jsonl)
- **Grain and key:** one current model-ready tract and active horizon.
- **Purpose:** stores current point predictions and calibrated intervals from every frozen horizon before application release filtering.

The table contains 93,438 rows: 46,719 model-ready tracts at each of the one- and three-year horizons, all scored from the 2025 forecast origin. It includes annualized display values, cumulative log-change values, baseline context, cohort fields, calibration lineage, and the finalization run identifier.

Presence here does not mean a prediction is approved for users. Both horizons are retained so the failed three-year result remains auditable, but only rows whose horizon passes `forecast_release_gate` may enter `serving_forecast_current`.

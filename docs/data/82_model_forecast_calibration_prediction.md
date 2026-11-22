# `forecast_calibration_prediction`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.forecast_calibration_prediction`
- **Sample:** [forecast_calibration_prediction.jsonl](../../data/samples/forecast_calibration_prediction.jsonl)
- **Grain and key:** one tract, supervised model, reserved calibration origin, and horizon.
- **Purpose:** preserves out-of-time residuals used to set the forecast interval width.

Each supervised model is trained only on labels known before the reserved origin, then applied to that origin. Absolute residuals feed a separate finite-sample split-conformal calculation for each model and horizon.

Calibration observations are separate from validation and later evaluation. They estimate uncertainty after model settings are frozen. They are not current forecasts and should not be displayed as tract results.

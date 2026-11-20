# `forecast_calibration_prediction`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.forecast_calibration_prediction`
- **Sample:** [forecast_calibration_prediction.jsonl](../../data/samples/forecast_calibration_prediction.jsonl)
- **Grain and key:** one tract, reserved calibration origin, and horizon.
- **Purpose:** preserves out-of-time residuals used to set the forecast interval width.

The current build contains 81,908 predictions: 41,017 at one year and 39,563 at three years. The model is trained only on labels known before the reserved origin, then applied to that origin. Absolute residuals from these rows feed the finite-sample split-conformal calculation in `forecast_interval_calibration`.

Calibration observations are deliberately separate from both model-selection validation and the locked temporal test. They estimate uncertainty after the champion is frozen without spending the final test set. They are not current forecasts and should not be displayed in the application.

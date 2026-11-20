# `serving_forecast_availability_current`

[Back to the data documentation index](README.md)

- **Layer:** Application serving
- **Databricks table:** `workspace.neighborhood_twin_serving.serving_forecast_availability_current`
- **Sample:** [serving_forecast_availability_current.jsonl](../../data/samples/serving_forecast_availability_current.jsonl)
- **Grain and key:** one serving release, current profile tract, and active horizon.
- **Purpose:** tells the application whether a forecast may be shown and why it is unavailable when it may not.

The 171,056-row release covers all 85,528 current profile tracts at both one and three years. At one year, 46,719 rows are available, 34,099 are outside the model-ready cohort, and 4,710 otherwise candidate rows have no published current prediction. Every three-year row is unavailable because the horizon failed its locked release gate.

This explicit universe prevents missing joins from being mistaken for application errors or zero forecasts. The UI should translate the reason codes into clear scope messages while retaining the gate metrics for review.

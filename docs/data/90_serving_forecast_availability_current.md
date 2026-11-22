# `serving_forecast_availability_current`

[Back to the data documentation index](README.md)

- **Layer:** Application serving
- **Databricks table:** `workspace.neighborhood_twin_serving.serving_forecast_availability_current`
- **Sample:** [serving_forecast_availability_current.jsonl](../../data/samples/serving_forecast_availability_current.jsonl)
- **Grain and key:** one serving release, current profile tract, and active horizon.
- **Purpose:** tells the application whether both supervised forecasts exist and why they are unavailable when they do not.

The table covers every current profile tract at one and three years. A row is available only when both regularized-linear and gradient-boosted-tree current predictions were published. Evaluation warnings do not make an otherwise complete row unavailable.

This explicit universe prevents missing joins from being mistaken for application errors or zero forecasts. The UI should translate the reason codes into clear scope messages while retaining the gate metrics for review.

Release `forecast-20261122T164538152848Z` contains 171,056 rows: 85,528 current profile tracts at each horizon. Both model forecasts are available for 93,438 tract-horizon rows, corresponding to 46,719 tracts at each horizon.

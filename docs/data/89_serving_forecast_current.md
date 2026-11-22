# `serving_forecast_current`

[Back to the data documentation index](README.md)

- **Layer:** Application serving
- **Databricks table:** `workspace.neighborhood_twin_serving.serving_forecast_current`
- **Sample:** [serving_forecast_current.jsonl](../../data/samples/serving_forecast_current.jsonl)
- **Grain and key:** one serving release, current tract, supervised model, and horizon.
- **Purpose:** gives the application both supervised forecasts without querying the wide modeling panel.

Version 2 publishes regularized-linear and gradient-boosted-tree rows at one and three years for every model-ready tract. Each row includes its point estimate, model-specific interval, visibly separate baseline, location labels, evaluation status, scope notes, and lineage.

The target is change in FHFA single-family tract HPI, not an individual property value or a measure of every type of housing. The driver summary is a global feature-family finding and must not be presented as a tract-level causal explanation.

Release `forecast-20261122T164538152848Z` contains 186,876 rows and all four expected model-horizon combinations.

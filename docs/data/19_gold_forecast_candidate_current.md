# `gold_forecast_candidate_current`

[Back to the data documentation index](README.md)

- **Layer:** Gold current products
- **Databricks table:** `workspace.neighborhood_twin_dev.gold_forecast_candidate_current`
- **Sample:** [gold_forecast_candidate_current.jsonl](../../data/samples/gold_forecast_candidate_current.jsonl)

- **Grain and key:** one row per candidate 2020 tract GEOID.
- **Purpose:** identifies current-profile tracts with at least ten usable, recent FHFA observations
  for initial forecasting experiments.
- **Caution:** it is a prototype cohort for outcome forecasting. Training examples still need
  point-in-time feature construction and time-aware splits.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

# `current_analogue_summary`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.current_analogue_summary`
- **Sample:** [current_analogue_summary.jsonl](../../data/samples/current_analogue_summary.jsonl)
- **Grain and key:** one selected current query tract, query origin year, and horizon.
- **Purpose:** summarizes the ten historical matches with median and inverse-distance outcomes,
  10th-to-90th percentile outcome context, distance, candidate age, geographic diversity,
  interpretation fields, and MLflow lineage.

The analogue outcome range is descriptive and is not a calibrated prediction interval. The
regularized forecasting model remains the source of the primary numerical forecast; this table
supports the historical-comparison portion of the application.

The first validated run contains six rows for three selected 2025 tracts and two horizons. All
rows summarize ten distinct matches and explicitly set
`outcome_range_is_calibrated_interval=false`. The run ID is
`ff3ad7a038ce4d4180110a7a9adcbab1`.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

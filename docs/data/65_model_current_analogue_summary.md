# `current_analogue_summary`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.current_analogue_summary`
- **Sample:** Added after the first validated live run.
- **Grain and key:** one selected current query tract, query origin year, and horizon.
- **Purpose:** summarizes the ten historical matches with median and inverse-distance outcomes,
  10th-to-90th percentile outcome context, distance, candidate age, geographic diversity,
  interpretation fields, and MLflow lineage.

The analogue outcome range is descriptive and is not a calibrated prediction interval. The
regularized forecasting model remains the source of the primary numerical forecast; this table
supports the historical-comparison portion of the application.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

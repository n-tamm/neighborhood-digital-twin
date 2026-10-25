# `geography_quality_metrics`

[Back to the data documentation index](README.md)

- **Layer:** Silver analytical source tables
- **Databricks table:** `workspace.neighborhood_twin_quality.geography_quality_metrics`
- **Sample:** [geography_quality_metrics.jsonl](../../data/samples/geography_quality_metrics.jsonl)

- **Grain and key:** one row per geography quality run, metric, and dimension.
- **Purpose:** preserves relationship, display-geometry, and Connecticut bridge validation and
  coverage results. The bridge checks reconcile both land-tract universes, reject duplicate
  mappings, and report water-only records separately.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

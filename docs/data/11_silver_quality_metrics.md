# `silver_quality_metrics`

[Back to the data documentation index](README.md)

- **Layer:** Silver analytical source tables
- **Databricks table:** `workspace.neighborhood_twin_dev.silver_quality_metrics`
- **Sample:** [silver_quality_metrics.jsonl](../../data/samples/silver_quality_metrics.jsonl)

- **Grain and key:** one row per quality run, table, metric, and dimension.
- **Purpose:** records schema, integrity, balance, missingness, temporal coverage, and
  reconciliation results for silver builds.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

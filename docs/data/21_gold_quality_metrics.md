# `gold_quality_metrics`

[Back to the data documentation index](README.md)

- **Layer:** Gold current products
- **Databricks table:** `workspace.neighborhood_twin_dev.gold_quality_metrics`
- **Sample:** [gold_quality_metrics.jsonl](../../data/samples/gold_quality_metrics.jsonl)

- **Grain and key:** one row per gold quality run, table, and metric.
- **Purpose:** records nonempty output, GEOID uniqueness, full-profile reconciliation, and current
  ACS-to-canonical join coverage before gold tables are published. Unmatched Connecticut GEOIDs
  are reported as a known warning, while unmatched current ACS identifiers outside reviewed
  exceptions are a hard failure.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

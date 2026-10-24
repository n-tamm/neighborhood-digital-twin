# `gold_quality_metrics`

[Back to the data documentation index](README.md)

- **Layer:** Gold current products
- **Databricks table:** `workspace.neighborhood_twin_dev.gold_quality_metrics`
- **Sample:** [gold_quality_metrics.jsonl](../../data/samples/gold_quality_metrics.jsonl)

- **Grain and key:** one row per gold quality run, table, and metric.
- **Purpose:** records nonempty output, GEOID uniqueness, full-profile reconciliation, and current
  ACS-to-canonical join coverage before gold tables are published. The current build reports 879
  Connecticut bridge matches, five expected water-only exceptions, and zero unexpected unmatched
  current ACS identifiers.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

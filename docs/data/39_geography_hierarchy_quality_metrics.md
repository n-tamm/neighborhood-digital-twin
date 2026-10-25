# `geography_hierarchy_quality_metrics`

[Back to the data documentation index](README.md)

- **Layer:** Quality and observability
- **Databricks table:** `workspace.neighborhood_twin_quality.geography_hierarchy_quality_metrics`
- **Sample:** [geography_hierarchy_quality_metrics.jsonl](../../data/samples/geography_hierarchy_quality_metrics.jsonl)

- **Grain and key:** one row per hierarchy build, table, and quality metric.
- **Purpose:** records row counts, key uniqueness, expected-level reconciliation, county-name
  completeness, and the final publication gate for the geography dimensions.
- **Current result:** the October 25, 2026 build published with zero hard failures.
- **Caution:** metrics are append-only. Filter to the latest `quality_run_id` when checking the
  current build rather than mixing results from separate runs.

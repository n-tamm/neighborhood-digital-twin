# `eda_readiness_quality_metrics`

[Back to the data documentation index](README.md)

- **Layer:** Quality and pipeline observability
- **Databricks table:** `workspace.neighborhood_twin_quality.eda_readiness_quality_metrics`
- **Sample:** [eda_readiness_quality_metrics.jsonl](../../data/samples/eda_readiness_quality_metrics.jsonl)

- **Grain and key:** one row per readiness run, output table, and check.
- **Purpose:** records whether every EDA summary is nonempty, unique at its declared grain, and
  structurally valid before publication.
- **Main structure:** the standard quality-run fields plus checks for FHFA year types and ranges.
- **Caution:** failed attempts remain in this append-only table. Filter by `quality_run_id` when
  reviewing one run rather than treating all historical statuses as current.

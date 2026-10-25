# `bronze_quality_metrics`

[Back to the data documentation index](README.md)

- **Layer:** Governance and bronze
- **Databricks table:** `workspace.neighborhood_twin_quality.bronze_quality_metrics`
- **Sample:** [bronze_quality_metrics.jsonl](../../data/samples/bronze_quality_metrics.jsonl)

- **Grain and key:** one row per quality run, table, metric, and dimension.
- **Purpose:** keeps append-only acquisition and bronze feasibility checks so past runs are still
  inspectable.
- **Main structure:** run ID, profiled table, metric group and name, value, status, expectation,
  and notes.

The national completion gate requires exactly 765 ACS state-release pairs: 15 annual releases
from 2010 through 2024 for the 50 states and Washington, D.C. It also requires a validated source
for every pair and rejects missing or out-of-scope pairs. Multiple immutable snapshots are reported
as lineage information; uniqueness is enforced within each snapshot rather than across history.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

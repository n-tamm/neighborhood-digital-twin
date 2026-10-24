# `bronze_fhfa_tract_hpi`

[Back to the data documentation index](README.md)

- **Layer:** Governance and bronze
- **Databricks table:** `workspace.neighborhood_twin_bronze.bronze_fhfa_tract_hpi`
- **Sample:** [bronze_fhfa_tract_hpi.jsonl](../../data/samples/bronze_fhfa_tract_hpi.jsonl)

- **Grain and key:** one row per snapshot, tract GEOID, and observation year.
- **Purpose:** preserves the source-shaped annual FHFA tract HPI file with snapshot lineage.
- **Main structure:** tract, state, year, annual change, several HPI bases, and source fields.
- **Caution:** FHFA tract HPI describes single-family price movement, not the level or composition
  of the entire housing market. Sparse or unavailable values remain null.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

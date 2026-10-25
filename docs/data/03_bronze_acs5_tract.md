# `bronze_acs5_tract`

[Back to the data documentation index](README.md)

- **Layer:** Governance and bronze
- **Databricks table:** `workspace.neighborhood_twin_bronze.bronze_acs5_tract`
- **Sample:** [bronze_acs5_tract.jsonl](../../data/samples/bronze_acs5_tract.jsonl)

- **Grain and key:** one row per snapshot, tract GEOID, and ACS release year.
- **Purpose:** preserves the selected ACS API response before numeric missing-value rules and
  readable naming are applied.
- **Main structure:** Census API variable codes, geography fields, release-window fields, and
  source lineage.
- **Caution:** each release pools five years of survey responses; adjacent annual releases overlap
  by four years and must not be treated as independent annual samples.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

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

As of October 25, 2026, this table contains 1,160,833 rows and 768 snapshots covering all 765
required combinations of 2010-2024 releases and the 50 states plus Washington, D.C. Bronze keeps
immutable acquisition history, so a tract and release can occur in more than one snapshot. Key
uniqueness is enforced within a snapshot; silver selects one validated snapshot per state and
release. Three 2024 pilot-state sources each have an earlier byte-identical snapshot, accounting
for the 8,228 rows not selected into the current silver build.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

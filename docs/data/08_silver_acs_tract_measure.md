# `silver_acs_tract_measure`

[Back to the data documentation index](README.md)

- **Layer:** Silver analytical source tables
- **Databricks table:** `workspace.neighborhood_twin_dev.silver_acs_tract_measure`
- **Sample:** [silver_acs_tract_measure.jsonl](../../data/samples/silver_acs_tract_measure.jsonl)

- **Grain and key:** one row per tract GEOID, ACS release year, and governed measure.
- **Purpose:** is the primary ACS analytical product. Its long format makes definitions,
  uncertainty, missingness, and cross-release comparisons easier to manage.
- **Main structure:** tract and release fields, measure name and definition, estimate, margin of
  error, relative margin of error, missing reasons, and lineage.
- **Use:** prefer this table for focused analysis, profiling, and any workflow that benefits from
  selecting measures rather than carrying a very wide row.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

# `silver_acs_tract_measure`

[Back to the data documentation index](README.md)

- **Layer:** Silver analytical source tables
- **Databricks table:** `workspace.neighborhood_twin_silver.silver_acs_tract_measure`
- **Sample:** [silver_acs_tract_measure.jsonl](../../data/samples/silver_acs_tract_measure.jsonl)

- **Grain and key:** one row per tract GEOID, ACS release year, and governed measure.
- **Purpose:** is the primary ACS analytical product. Its long format makes definitions,
  uncertainty, missingness, and cross-release comparisons easier to manage.
- **Main structure:** tract and release fields, measure name and definition, estimate, margin of
  error, relative margin of error, missing reasons, and lineage.
- **Use:** prefer this table for focused analysis, profiling, and any workflow that benefits from
  selecting measures rather than carrying a very wide row.

As of October 25, 2026, the table contains 24,204,705 rows: 1,152,605 selected tract-release rows
multiplied by 21 governed measures. It covers every 2010-2024 release for the 50 states and
Washington, D.C.; pre-2020 releases retain their 2010 geography vintage pending explicit
cross-vintage harmonization.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

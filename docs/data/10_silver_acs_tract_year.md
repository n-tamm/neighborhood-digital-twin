# `silver_acs_tract_year`

[Back to the data documentation index](README.md)

- **Layer:** Silver analytical source tables
- **Databricks table:** `workspace.neighborhood_twin_silver.silver_acs_tract_year`
- **Sample:** [silver_acs_tract_year.jsonl](../../data/samples/silver_acs_tract_year.jsonl)

- **Grain and key:** one row per tract GEOID and ACS release year.
- **Purpose:** provides a convenient wide form of the governed ACS measures for exploration,
  feature engineering, and current-profile construction.
- **Main structure:** geography and release identifiers, estimate/MOE/missing-reason fields for
  each selected measure, derived housing rates and shares, and lineage.
- **Caution:** the long measure table remains the source of truth when definitions or uncertainty
  need to be handled programmatically.

As of October 25, 2026, the table contains 1,152,605 selected tract-release rows across all 765
required combinations of the 2010-2024 releases and the 50 states plus Washington, D.C. The latest
silver build reconciled every selected source group, found no duplicate keys or parse failures,
and completed with zero warnings or hard failures.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

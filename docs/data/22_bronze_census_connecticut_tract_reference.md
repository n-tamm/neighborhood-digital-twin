# `bronze_census_connecticut_tract_reference`

[Back to the data documentation index](README.md)

- **Layer:** Bronze
- **Databricks table:** `workspace.neighborhood_twin_bronze.bronze_census_connecticut_tract_reference`
- **Sample:** [bronze_census_connecticut_tract_reference.jsonl](../../data/samples/bronze_census_connecticut_tract_reference.jsonl)

- **Grain and key:** one row per source snapshot, geography vintage, and Connecticut tract GEOID.
- **Purpose:** preserves the tract identity and reference attributes needed to reconcile the county
  codes used in the 2020 TIGER/Line file with the planning-region codes used in current ACS data.
- **Sources:** official 2020 and 2024 Connecticut TIGER/Line tract archives from the U.S. Census
  Bureau.
- **Main structure:** geography vintage, tract and county identifiers, land and water area,
  internal-point coordinates, and immutable source lineage.
- **Current volume:** 883 rows for 2020 and 884 rows for 2024. The two vintages contain 4 and 5
  water-only tracts, respectively.
- **Caution:** this is a source-shaped identity reference, not application geometry and not a
  demographic dataset. Water-only tracts remain in bronze so the source universes reconcile.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

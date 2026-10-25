# `bronze_census_tract_display_geometry_2020`

[Back to the data documentation index](README.md)

- **Layer:** Governance and bronze
- **Databricks table:** `workspace.neighborhood_twin_bronze.bronze_census_tract_display_geometry_2020`
- **Sample:** [bronze_census_tract_display_geometry_2020.jsonl](../../data/samples/bronze_census_tract_display_geometry_2020.jsonl)

- **Grain and key:** one row per displayable 2020 tract GEOID.
- **Purpose:** stores parsed attributes and WKB from the simplified national cartographic archive.
- **Main structure:** names and FIPS codes, land/water area, bounding box, geometry type, geometry,
  and lineage.
- **Caution:** the source is deliberately simplified for mapping and is not suitable for precise
  spatial analysis.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

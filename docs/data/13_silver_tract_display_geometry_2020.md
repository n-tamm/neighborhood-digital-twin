# `silver_tract_display_geometry_2020`

[Back to the data documentation index](README.md)

- **Layer:** Silver analytical source tables
- **Databricks table:** `workspace.neighborhood_twin_silver.silver_tract_display_geometry_2020`
- **Sample:** [silver_tract_display_geometry_2020.jsonl](../../data/samples/silver_tract_display_geometry_2020.jsonl)

- **Grain and key:** one row per displayable 2020 tract GEOID.
- **Purpose:** supplies lightweight geometry and bounding boxes for application maps.
- **Caution:** `geometry_role` explicitly limits this table to display; use full-resolution TIGER
  geometry for analytical spatial work.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

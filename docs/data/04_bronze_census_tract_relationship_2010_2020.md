# `bronze_census_tract_relationship_2010_2020`

[Back to the data documentation index](README.md)

- **Layer:** Governance and bronze
- **Databricks table:** `workspace.neighborhood_twin_bronze.bronze_census_tract_relationship_2010_2020`
- **Sample:** [bronze_census_tract_relationship_2010_2020.jsonl](../../data/samples/bronze_census_tract_relationship_2010_2020.jsonl)

- **Grain and key:** one row per unique 2010-tract to 2020-tract relationship edge.
- **Purpose:** keeps the official Census relationship records needed to understand tract splits,
  merges, and stable mappings across the decennial boundary change.
- **Main structure:** source and target GEOIDs, names and areas, overlapping-part areas, and
  snapshot lineage.
- **Caution:** this is a relationship graph, not a one-row tract dimension.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

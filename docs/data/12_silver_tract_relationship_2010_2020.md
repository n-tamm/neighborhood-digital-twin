# `silver_tract_relationship_2010_2020`

[Back to the data documentation index](README.md)

- **Layer:** Silver analytical source tables
- **Databricks table:** `workspace.neighborhood_twin_silver.silver_tract_relationship_2010_2020`
- **Sample:** [silver_tract_relationship_2010_2020.jsonl](../../data/samples/silver_tract_relationship_2010_2020.jsonl)

- **Grain and key:** one row per unique 2010-tract to 2020-tract edge.
- **Purpose:** turns the official relationship file into typed mapping edges with overlap shares
  and conservative flags for stable and dominant mappings.
- **Main structure:** source/target GEOIDs and areas, part areas, source and target land shares,
  mapping type, stability flags, and lineage.
- **Use:** this is the correct starting point for putting pre-2020 measures onto a 2020 tract
  framework. Do not equate matching GEOIDs with unchanged boundaries without checking the flags.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

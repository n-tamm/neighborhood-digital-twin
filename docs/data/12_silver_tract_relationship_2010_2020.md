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

For the 50-state and District of Columbia project scope, the source contains 73,057 distinct
2010 tracts and 84,414 distinct 2020 tracts. The `is_stable_measure_mapping` flag identifies
59,607 source tracts whose same-GEOID relationship preserves at least 95% of both tract land
areas. The geography quality table separately reports one-target, multiple-target, one-source,
multiple-source, stable, and unresolved counts at the tract grain. These flags support a
stable-tract modeling cohort; the land shares must not be used to redistribute population,
housing counts, medians, rates, ratios, or indexes without a field-specific method.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

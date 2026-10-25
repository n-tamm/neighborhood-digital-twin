# `silver_geography_region`

[Back to the data documentation index](README.md)

- **Layer:** Silver geography dimensions
- **Databricks table:** `workspace.neighborhood_twin_silver.silver_geography_region`
- **Sample:** [silver_geography_region.jsonl](../../data/samples/silver_geography_region.jsonl)

- **Grain and key:** one row per Census region; `region_code` is the key.
- **Purpose:** supports valid regional reporting, evaluation slices, and application filters above
  the Census division level.
- **Current population:** four Census regions.
- **Main structure:** region code and name, country parent, vintage, and build lineage.
- **Caution:** Puerto Rico and the other island areas are not assigned to the four Census regions
  and are intentionally outside this hierarchy.

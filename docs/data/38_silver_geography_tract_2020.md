# `silver_geography_tract_2020`

[Back to the data documentation index](README.md)

- **Layer:** Silver geography dimensions
- **Databricks table:** `workspace.neighborhood_twin_silver.silver_geography_tract_2020`
- **Sample:** [silver_geography_tract_2020.jsonl](../../data/samples/silver_geography_tract_2020.jsonl)

- **Grain and key:** one row per supported canonical 2020 tract; `geoid_2020` is the key.
- **Purpose:** gives modeling, analysis, reporting, and the application one clean hierarchy from
  tract through country without duplicating display geometry.
- **Current population:** 84,414 tracts across the 50 states and District of Columbia.
- **Main structure:** tract, county, state, division, region, and country identifiers and names;
  land and water area; display-geometry availability; vintage; and build lineage.
- **Caution:** this supported hierarchy is narrower than `silver_canonical_tract_2020`, which also
  retains territory records. Metro and ZIP/ZCTA are not valid levels in this hierarchy and are not
  represented here.

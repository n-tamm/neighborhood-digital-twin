# `silver_geography_county`

[Back to the data documentation index](README.md)

- **Layer:** Silver geography dimensions
- **Databricks table:** `workspace.neighborhood_twin_silver.silver_geography_county`
- **Sample:** [silver_geography_county.jsonl](../../data/samples/silver_geography_county.jsonl)

- **Grain and key:** one row per canonical 2020 county or county equivalent;
  `county_geoid` is the key.
- **Purpose:** supports county-level reporting and supplies the valid state-through-country parent
  chain inherited by canonical tracts.
- **Current population:** 3,143 counties and county equivalents in the 50 states and District of
  Columbia.
- **Main structure:** county identifiers and name, state, division, region, country, vintage, and
  build lineage.
- **Caution:** this is the canonical 2020 county definition. Connecticut's later planning-region
  identifiers remain handled by the explicit current-geography bridge.

# `silver_geography_state`

[Back to the data documentation index](README.md)

- **Layer:** Silver geography dimensions
- **Databricks table:** `workspace.neighborhood_twin_silver.silver_geography_state`
- **Sample:** [silver_geography_state.jsonl](../../data/samples/silver_geography_state.jsonl)

- **Grain and key:** one row per supported state or state equivalent; `state_fips` is the key.
- **Purpose:** supplies one governed state definition and its valid division, region, and country
  parents for joins throughout the project.
- **Current population:** the 50 states and District of Columbia, for 51 rows total.
- **Main structure:** state FIPS, postal abbreviation, state name, all parent identifiers and
  names, vintage, and build lineage.
- **Caution:** territories remain in parts of the broader canonical Census source but are not
  forced into Census regions or divisions.

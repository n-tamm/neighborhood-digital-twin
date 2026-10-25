# `silver_geography_country`

[Back to the data documentation index](README.md)

- **Layer:** Silver geography dimensions
- **Databricks table:** `workspace.neighborhood_twin_silver.silver_geography_country`
- **Sample:** [silver_geography_country.jsonl](../../data/samples/silver_geography_country.jsonl)

- **Grain and key:** one row per supported country code; `country_code` is the key.
- **Purpose:** supplies the valid top-level parent for Census regions and all lower supported
  geography levels.
- **Current population:** one United States row.
- **Main structure:** country code and name, 2020 geography vintage, schema version, and build
  lineage.
- **Caution:** this table defines the project hierarchy, not a general international geography
  system.

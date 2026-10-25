# `silver_geography_division`

[Back to the data documentation index](README.md)

- **Layer:** Silver geography dimensions
- **Databricks table:** `workspace.neighborhood_twin_silver.silver_geography_division`
- **Sample:** [silver_geography_division.jsonl](../../data/samples/silver_geography_division.jsonl)

- **Grain and key:** one row per Census division; `division_code` is the key.
- **Purpose:** provides the valid level between Census region and state for geographic summaries,
  comparison groups, and model evaluation.
- **Current population:** nine Census divisions.
- **Main structure:** division code and name, region and country parents, vintage, and build
  lineage.
- **Caution:** divisions are Census statistical groupings of states, not metropolitan areas or
  housing markets.

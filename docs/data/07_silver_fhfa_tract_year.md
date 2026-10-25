# `silver_fhfa_tract_year`

[Back to the data documentation index](README.md)

- **Layer:** Silver analytical source tables
- **Databricks table:** `workspace.neighborhood_twin_silver.silver_fhfa_tract_year`
- **Sample:** [silver_fhfa_tract_year.jsonl](../../data/samples/silver_fhfa_tract_year.jsonl)

- **Grain and key:** one row per 2020 tract GEOID and observation year.
- **Purpose:** provides typed annual FHFA history for forecasting and housing-market trajectory
  features.
- **Main structure:** readable HPI measures, availability flags, geography vintage, and build and
  snapshot lineage.
- **Caution:** this table should support a housing-price component of the twin, not stand in for a
  complete neighborhood or housing-market outcome.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

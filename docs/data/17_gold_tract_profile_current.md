# `gold_tract_profile_current`

[Back to the data documentation index](README.md)

- **Layer:** Gold current products
- **Databricks table:** `workspace.neighborhood_twin_dev.gold_tract_profile_current`
- **Sample:** [gold_tract_profile_current.jsonl](../../data/samples/gold_tract_profile_current.jsonl)

- **Grain and key:** exactly one row per canonical 2020 tract GEOID.
- **Purpose:** is the main current-state product for modeling and application prototypes. It joins
  a compact, readable set of ACS housing and community fields with summarized FHFA history while
  retaining every canonical tract.
- **Main structure:** place identity, current ACS estimates and uncertainty, housing-mix rates,
  recent and historical HPI fields, coverage flags, transparent candidate flags, and build lineage.
- **Caution:** absent source coverage remains null and is explained by flags. This table is a
  feature-ready profile, not a trained model output.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

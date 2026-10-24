# `silver_acs_measure_dictionary`

[Back to the data documentation index](README.md)

- **Layer:** Silver analytical source tables
- **Databricks table:** `workspace.neighborhood_twin_dev.silver_acs_measure_dictionary`
- **Sample:** [silver_acs_measure_dictionary.jsonl](../../data/samples/silver_acs_measure_dictionary.jsonl)

- **Grain and key:** one row per governed ACS measure; keyed by `measure_name`.
- **Purpose:** gives readable definitions and preserves the Census estimate and margin-of-error
  codes used during acquisition.
- **Main structure:** ordering, project name, source group and concept, universe, unit, source
  variable codes, metadata release, and metadata URL.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

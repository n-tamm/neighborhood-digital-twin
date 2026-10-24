# `silver_canonical_tract_2020`

[Back to the data documentation index](README.md)

- **Layer:** Silver analytical source tables
- **Databricks table:** `workspace.neighborhood_twin_silver.silver_canonical_tract_2020`
- **Sample:** [silver_canonical_tract_2020.jsonl](../../data/samples/silver_canonical_tract_2020.jsonl)

- **Grain and key:** exactly one row per relationship-defined 2020 tract GEOID.
- **Purpose:** defines the complete stable tract backbone used for joins. Display geometry is
  optional and cannot determine whether a tract exists.
- **Main structure:** tract identifiers and names, areas, optional display geometry and bounding
  box, coverage flags, source IDs, and build lineage.
- **Caution:** current ACS tract identifiers in Connecticut changed after the state adopted new
  county-equivalent planning regions. That bridge is a separate required geography task.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

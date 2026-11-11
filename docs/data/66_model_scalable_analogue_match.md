# `scalable_analogue_match`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.scalable_analogue_match`
- **Sample:** Added after the first validated live run.
- **Grain and key:** one benchmark query tract, origin year, horizon, retrieval configuration,
  and match rank.
- **Purpose:** retains exhaustive exact and LSH-shortlisted historical matches under the same
  weighted representation and exact final distance.

Every candidate obeys the current analogue timing, geography, self-exclusion, locked-test, and
distinct-physical-tract rules. Configuration names distinguish the exact reference from the three
approximate shortlist methods. This table is benchmark evidence, not an application serving table.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

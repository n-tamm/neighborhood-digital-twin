# `scalable_analogue_match`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.scalable_analogue_match`
- **Sample:** [scalable_analogue_match.jsonl](../../data/samples/scalable_analogue_match.jsonl)
- **Grain and key:** one benchmark query tract, origin year, horizon, retrieval configuration,
  and match rank.
- **Purpose:** retains exhaustive exact and LSH-shortlisted historical matches under the same
  weighted representation and exact final distance.

Every candidate obeys the current analogue timing, geography, self-exclusion, locked-test, and
distinct-physical-tract rules. Configuration names distinguish the exact reference from the three
approximate shortlist methods. This table is benchmark evidence, not an application serving table.

The validated schema-1.1 run contains 2,320 rows: 29 current queries, two horizons, four retrieval
configurations, and ten matches per query. All 232 query/configuration lists contain ten distinct
tracts, with no self, future-outcome, or locked-test match.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

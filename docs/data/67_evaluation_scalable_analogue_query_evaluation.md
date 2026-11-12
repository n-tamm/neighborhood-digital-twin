# `scalable_analogue_query_evaluation`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation outputs
- **Databricks table:** `workspace.neighborhood_twin_evaluation.scalable_analogue_query_evaluation`
- **Sample:** [scalable_analogue_query_evaluation.jsonl](../../data/samples/scalable_analogue_query_evaluation.jsonl)
- **Grain and key:** one benchmark query tract, origin year, horizon, and approximate retrieval
  configuration.
- **Purpose:** compares each approximate match list with the exhaustive exact top ten using
  completeness, community and tract-year-state recall, Jaccard overlap, top-three retention, rank
  movement, and historical outcome-summary drift.

Every declared query and configuration remains represented even when the approximate method finds
no candidates. This prevents favorable averages created by dropping failed queries.

The validated run contains 174 rows for 29 queries, two horizons, and three approximate
configurations. Community recall is perfect throughout. Tract-year-state recall reveals one
three-year narrow-LSH query that recovers the same tract at a different historical year.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

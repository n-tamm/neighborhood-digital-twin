# `scalable_analogue_query_evaluation`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation outputs
- **Databricks table:** `workspace.neighborhood_twin_evaluation.scalable_analogue_query_evaluation`
- **Sample:** Added after the first validated live run.
- **Grain and key:** one benchmark query tract, origin year, horizon, and approximate retrieval
  configuration.
- **Purpose:** compares each approximate match list with the exhaustive exact top ten using
  completeness, community and tract-year-state recall, Jaccard overlap, top-three retention, rank
  movement, and historical outcome-summary drift.

Every declared query and configuration remains represented even when the approximate method finds
no candidates. This prevents favorable averages created by dropping failed queries.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

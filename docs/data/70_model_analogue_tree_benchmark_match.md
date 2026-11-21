# `analogue_tree_benchmark_match`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.analogue_tree_benchmark_match`
- **Sample:** [analogue_tree_benchmark_match.jsonl](../../data/samples/analogue_tree_benchmark_match.jsonl)
- **Grain and key:** one job-603 benchmark query tract, origin year, horizon, and historical
  match rank.
- **Purpose:** retains exact KD-tree matches under the frozen weighted representation so their
  identities, years, ranks, distances, outcomes, and retrieval work can be reviewed directly.

The table contains benchmark evidence rather than the eventual national serving product. Every
query should have ten distinct non-self candidate tracts whose outcomes ended by the query year.
`retrieved_state_count` and `tree_expansion_count` show how much indexed over-fetching was needed
to enforce the distinct-community and distance-tie rules.

The current validated run contains 580 rows: ten matches for 29 queries at each of two horizons.
It uses MLflow run `344fbe71819f4a779b36701a5fdaf7b8` and reproduces the exhaustive reference
exactly. The tracked sample is a point-in-time extract from the preceding validated run; Databricks
is authoritative for current lineage IDs.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

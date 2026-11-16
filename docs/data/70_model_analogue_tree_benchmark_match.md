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

The validated run contains 580 rows: ten matches for 29 queries at each of two horizons. It uses
MLflow run `fae78721154347039d41864bad2e871a` and reproduces the exhaustive reference exactly.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

# `analogue_tree_summary`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation outputs
- **Databricks table:** `workspace.neighborhood_twin_evaluation.analogue_tree_summary`
- **Sample:** Added after the first validated live run.
- **Grain and key:** one outcome horizon and exact indexed retrieval configuration.
- **Purpose:** combines exact-reference fidelity with tree construction time, query time, distance
  work, candidate expansion, current-query coverage, and in-memory tree size.

`distance_computation_ratio` compares reported KD-tree distance calls with one exhaustive
query-candidate pass. It can exceed one if repeated expansion performs more work than a single
pass, so it is a ratio rather than a bounded share. Selection requires exact fidelity and a
material work or runtime improvement; neither condition is inferred from a successful job alone.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

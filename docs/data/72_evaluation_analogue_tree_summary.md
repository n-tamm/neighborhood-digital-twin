# `analogue_tree_summary`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation outputs
- **Databricks table:** `workspace.neighborhood_twin_evaluation.analogue_tree_summary`
- **Sample:** [analogue_tree_summary.jsonl](../../data/samples/analogue_tree_summary.jsonl)
- **Grain and key:** one outcome horizon and exact indexed retrieval configuration.
- **Purpose:** combines exact-reference fidelity with tree construction time, query time, distance
  work, candidate expansion, current-query coverage, and in-memory tree size.

`distance_computation_ratio` compares reported KD-tree distance calls with one exhaustive
query-candidate pass. It can exceed one if repeated expansion performs more work than a single
pass, so it is a ratio rather than a bounded share. Selection requires exact fidelity and a
material work or runtime improvement; neither condition is inferred from a successful job alone.

The live trees build in under half a second and occupy about 57.8 MB at one year and 37.9 MB at
three years. On the 29-query reference, the tree computes about 9.3% to 9.6% of the distances in
one exhaustive pass while reproducing every rank.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

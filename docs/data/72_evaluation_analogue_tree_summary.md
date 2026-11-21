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

In the current corrected-lineage run, the one-year tree indexes 562,597 historical states and the
three-year tree indexes 452,689. On the 29-query reference, both reproduce every match and rank.
The full 46,719-query retrieval uses about 9.4% to 9.5% of the distance work of an exhaustive
pass.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

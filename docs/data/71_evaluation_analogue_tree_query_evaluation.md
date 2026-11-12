# `analogue_tree_query_evaluation`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation outputs
- **Databricks table:** `workspace.neighborhood_twin_evaluation.analogue_tree_query_evaluation`
- **Sample:** [analogue_tree_query_evaluation.jsonl](../../data/samples/analogue_tree_query_evaluation.jsonl)
- **Grain and key:** one job-603 benchmark query tract, origin year, and horizon.
- **Purpose:** compares exact KD-tree results with the exhaustive reference using community and
  tract-year-state recall, rank agreement, completeness, and historical-outcome drift.

Because the KD-tree is intended to be an exact replacement for the cross join, every query must
have complete physical-community and tract-year-state recall with zero outcome drift. A result
that is merely close is a failed implementation rather than an acceptable approximation.

All 58 validated query-horizon rows have complete top-ten lists, full community and tract-year
recall, zero rank displacement, and outcome differences below the `1e-12` numerical tolerance.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

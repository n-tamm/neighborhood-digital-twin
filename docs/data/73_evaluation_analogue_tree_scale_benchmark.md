# `analogue_tree_scale_benchmark`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation outputs
- **Databricks table:** `workspace.neighborhood_twin_evaluation.analogue_tree_scale_benchmark`
- **Sample:** Added after the first validated live run.
- **Grain and key:** one outcome horizon and declared current-query population.
- **Purpose:** records measured KD-tree query work for the job-603 sample, a deterministic
  intermediate sample, and every eligible current neighborhood.

The full current-query row is a direct batch measurement, not a linear projection from 29
examples. It does not publish national match rows yet. This keeps retrieval-method selection
separate from the later serving-table contract and prevents a failed index experiment from
becoming an application dependency.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

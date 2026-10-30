# `similarity_baseline_match`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.similarity_baseline_match`
- **Sample:** [similarity_baseline_match.jsonl](../../data/samples/similarity_baseline_match.jsonl)
- **Grain and key:** one query tract, representation, and match rank.
- **Purpose:** provides a small, inspectable comparison of nearest communities under standardized
  current features and a PCA representation.

Scale-like inputs are transformed with `log1p`, missing values are median-imputed, and all inputs
are standardized before exact Euclidean retrieval. The query tract is excluded from its own
results. This is a current-state representation baseline, not yet the time-safe historical
analogue product or the final application table.

The initial run contains 120 rows: ten neighbors under each representation for six query tracts.
The model schema holds the generated ranked matches while the evaluation schema holds their
representation-level diagnostics.

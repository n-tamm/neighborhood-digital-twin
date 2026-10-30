# `gold_similarity_baseline_match`

[Back to the data documentation index](README.md)

- **Layer:** Gold model development
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_similarity_baseline_match`
- **Grain and key:** one query tract, representation, and match rank.
- **Purpose:** gives the team a small, inspectable comparison of nearest communities under
  standardized current features and a PCA representation.

Scale-like inputs are transformed with `log1p`, missing values are median-imputed, and all inputs
are standardized before distance is calculated. The query tract is always excluded from its own
results. This is a current-state baseline, not yet the time-safe retrospective analogue product
or the final application serving table.

The table will receive a small sample in `data/samples/` after the first successful shared run.

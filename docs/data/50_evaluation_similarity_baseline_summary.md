# `similarity_baseline_summary`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.similarity_baseline_summary`
- **Sample:** [similarity_baseline_summary.jsonl](../../data/samples/similarity_baseline_summary.jsonl)
- **Grain and key:** one representation and baseline run.
- **Purpose:** records behavioral diagnostics before matches are treated as an application feature.

The summary reports query and match counts, distance quantiles and interquartile range, cross-state
and same-county shares, PCA explained variance, and raw-versus-PCA top-k overlap as both a count
and share. Distances are representation-specific and cannot be compared as if they use one common
scale.

These diagnostics reveal compression, geographic reach, distance concentration, and sensitivity
to representation choice. They do not establish that a match is useful. Human review,
perturbation stability, and time-safe later-outcome evaluation remain required.

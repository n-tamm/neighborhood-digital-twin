# `gold_similarity_baseline_summary`

[Back to the data documentation index](README.md)

- **Layer:** Gold model development
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_similarity_baseline_summary`
- **Grain and key:** one representation and baseline run.
- **Purpose:** records representation-level diagnostics before the team treats matches as an
  application feature.

The summary reports query and match counts, median and mean distance, cross-state match share,
PCA explained variance, and the average overlap between the raw and PCA top-k lists. These
diagnostics do not prove that a match is useful; they show whether the representation is overly
local, unstable across methods, or compressing too much information. Human case review and
time-safe later-outcome evaluation remain required.

The table will receive a small sample in `data/samples/` after the first successful shared run.

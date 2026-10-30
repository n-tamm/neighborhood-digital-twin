# `gold_similarity_baseline_summary`

[Back to the data documentation index](README.md)

- **Layer:** Gold model development
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_similarity_baseline_summary`
- **Sample:** [gold_similarity_baseline_summary.jsonl](../../data/samples/gold_similarity_baseline_summary.jsonl)
- **Grain and key:** one representation and baseline run.
- **Purpose:** records representation-level diagnostics before the team treats matches as an
  application feature.

The summary reports query and match counts, median and mean distance, cross-state match share,
PCA explained variance, and the average overlap between the raw and PCA top-k lists. These
diagnostics do not prove that a match is useful; they show whether the representation is overly
local, unstable across methods, or compressing too much information. Human case review and
time-safe later-outcome evaluation remain required.

Six PCA components retain 95.5% of standardized feature variance. Raw and PCA top-10 lists share
5.5 matches on average, while 91.7% and 95.0% of their respective matches cross a state boundary.
The national search is therefore not collapsing into same-state retrieval, but the moderate
method overlap confirms that representation choice materially changes which communities appear.

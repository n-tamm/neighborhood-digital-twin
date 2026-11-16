# `historical_analogue_selection_summary`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.historical_analogue_selection_summary`
- **Sample:** [historical_analogue_selection_summary.jsonl](../../data/samples/historical_analogue_selection_summary.jsonl)
- **Grain and key:** one horizon, representation, and analogue-selection run.
- **Purpose:** describes expanded retrieval behavior before outcome accuracy is interpreted.

The table summarizes query and match counts, distance percentiles, candidate age, cross-state and
same-county shares, PCA explained variance, and weighted-versus-PCA top-ten overlap. Distances are
interpreted only within one representation because PCA and weighted feature space have different
scales.

The four validated rows show that 92.6% to 96.3% of matches cross state lines. Weighted and PCA
top tens overlap by only 18.9% at one year and 27.8% at three years, confirming that PCA would
show materially different historical evidence rather than merely compressing the same result.

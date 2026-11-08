# `historical_analogue_selection_summary`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.historical_analogue_selection_summary`
- **Grain and key:** one horizon, representation, and analogue-selection run.
- **Purpose:** describes expanded retrieval behavior before outcome accuracy is interpreted.

The table summarizes query and match counts, distance percentiles, candidate age, cross-state and
same-county shares, PCA explained variance, and weighted-versus-PCA top-ten overlap. Distances are
interpreted only within one representation because PCA and weighted feature space have different
scales.

Live results and a real sample will be added after the first validated job-602 publication.

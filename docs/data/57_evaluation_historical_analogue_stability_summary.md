# `historical_analogue_stability_summary`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:**
  `workspace.neighborhood_twin_evaluation.historical_analogue_stability_summary`
- **Grain and key:** one validation query tract, origin, horizon, and audit variant.
- **Purpose:** measures how much each query's matches and analogue outcome estimates move when a
  reasonable model choice changes.

For each variant, this table compares its top ten with the matching weighted-standardized or PCA
baseline. It reports overlap, Jaccard similarity, top-three retention, shared-rank movement,
candidate age and geographic diversity, and changes in the median and inverse-distance analogue
estimates. It also records whether the retrieval was exact or shortlist-based.

The stability bands are review aids rather than scientific thresholds: at least 70% top-ten
retention is labeled high, 50% through 69% moderate, and less than 50% low. Results should be read
as a distribution across queries. A good average does not erase an unstable case, and better
later-outcome error under one perturbation is not enough to justify changing the representation.

The first live job-601 publication is pending. A repository sample and observed findings should
be added after the output passes its query-coverage, timing, metric-range, and lineage checks.

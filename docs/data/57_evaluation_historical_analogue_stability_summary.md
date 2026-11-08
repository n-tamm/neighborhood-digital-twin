# `historical_analogue_stability_summary`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:**
  `workspace.neighborhood_twin_evaluation.historical_analogue_stability_summary`
- **Sample:** [historical_analogue_stability_summary.jsonl](../../data/samples/historical_analogue_stability_summary.jsonl)
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

The validated November 7 table contains 672 rows, exactly 32 queries times 21 variants. Small
feature-family weight changes retain 93.4% of the baseline top ten on average; every one is
mathematically certified against the shortlist boundary. Family removals retain 37.6% on average
and are intentionally labeled shortlist-based stress tests. The table preserves zero-overlap
cases rather than dropping them from the evaluation.

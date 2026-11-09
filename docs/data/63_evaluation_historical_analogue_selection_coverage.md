# `historical_analogue_selection_coverage`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.historical_analogue_selection_coverage`
- **Sample:** [historical_analogue_selection_coverage.jsonl](../../data/samples/historical_analogue_selection_coverage.jsonl)
- **Grain and key:** one horizon, coverage dimension, and dimension value.
- **Purpose:** shows whether the expanded deterministic query sample represents the eligible
  validation population across important neighborhood and data-quality groups.

For each category, the table reports eligible and selected tract-year counts, distinct tract
counts, population shares, the selected-minus-eligible share difference, and whether the category
received any selected query. Dimensions cover origin year, Census region, geographic role,
modeling cohort, housing composition, community size, ACS uncertainty, and the exact sampling
strata.

The 78 validated rows confirm that every eligible housing-composition, community-size, and ACS
uncertainty category has at least one query. Very rare categories still have only one case and
cannot support a subgroup performance claim. Held-out states are deliberately oversampled at
roughly 44% to 45% of queries, despite representing less than 2% of eligible rows, because the
sample balances transfer evidence by region and geographic role rather than estimating a
population-weighted national average.

Coverage does not prove that a sample is statistically representative, but it prevents an
aggregate score from hiding an obvious missing or heavily overrepresented group.

# `historical_analogue_selection_coverage`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.historical_analogue_selection_coverage`
- **Grain and key:** one horizon, coverage dimension, and dimension value.
- **Purpose:** shows whether the expanded deterministic query sample represents the eligible
  validation population across important neighborhood and data-quality groups.

For each category, the table reports eligible and selected tract-year counts, distinct tract
counts, population shares, the selected-minus-eligible share difference, and whether the category
received any selected query. Dimensions cover origin year, Census region, geographic role,
modeling cohort, housing composition, community size, ACS uncertainty, and the exact sampling
strata.

Coverage does not prove that a sample is statistically representative, but it prevents an
aggregate score from hiding an obvious missing or heavily overrepresented group. Live results and
a real sample will be added after the first validated job-602 publication.

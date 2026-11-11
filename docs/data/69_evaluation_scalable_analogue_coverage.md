# `scalable_analogue_coverage`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation outputs
- **Databricks table:** `workspace.neighborhood_twin_evaluation.scalable_analogue_coverage`
- **Sample:** Added after the first validated live run.
- **Grain and key:** one benchmark coverage dimension and dimension value.
- **Purpose:** compares the selected current-query benchmark with all eligible current queries by
  region, cohort, housing composition, community size, and ACS uncertainty.

The benchmark deliberately balances several groups and is not population weighted. Rare categories
with one selected query are coverage checks, not reliable subgroup performance estimates.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

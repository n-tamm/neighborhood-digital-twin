# `scalable_analogue_coverage`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation outputs
- **Databricks table:** `workspace.neighborhood_twin_evaluation.scalable_analogue_coverage`
- **Sample:** [scalable_analogue_coverage.jsonl](../../data/samples/scalable_analogue_coverage.jsonl)
- **Grain and key:** one benchmark coverage dimension and dimension value.
- **Purpose:** compares the selected current-query benchmark with all eligible current queries by
  region, cohort, housing composition, community size, and ACS uncertainty.

The benchmark deliberately balances several groups and is not population weighted. Rare categories
with one selected query are coverage checks, not reliable subgroup performance estimates.

The 29-query benchmark covers all four Census regions, both modeling cohorts, and every eligible
housing-composition, community-size, and ACS-uncertainty category. It represents the 46,719 tracts
eligible for the current historical-analogue contract, but it is not a national performance sample.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

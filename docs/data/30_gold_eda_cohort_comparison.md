# `gold_eda_cohort_comparison`

[Back to the data documentation index](README.md)

- **Layer:** Gold exploration summaries
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_eda_cohort_comparison`
- **Sample:** [gold_eda_cohort_comparison.jsonl](../../data/samples/gold_eda_cohort_comparison.jsonl)

- **Grain and key:** one row per current-profile feature used in the governed comparison.
- **Purpose:** compares current ACS tracts that pass the FHFA forecast-availability screen with
  current ACS tracts that do not.
- **Main structure:** cohort sizes, available values, means, medians, missing-value shares, and a
  standardized mean difference calculated as forecast candidates minus excluded tracts.
- **Caution:** these are descriptive selection differences, not causal effects. Several features
  are complements or close relatives, such as owner and renter occupancy, so rows should not be
  treated as independent findings.

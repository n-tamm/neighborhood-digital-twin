# `gold_eda_state_coverage`

[Back to the data documentation index](README.md)

- **Layer:** Gold exploration summaries
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_eda_state_coverage`
- **Sample:** [gold_eda_state_coverage.jsonl](../../data/samples/gold_eda_state_coverage.jsonl)

- **Grain and key:** one row per state or state-equivalent FIPS code.
- **Purpose:** makes geographic attrition visible from the canonical tract universe through current
  ACS, FHFA history, similarity eligibility, and forecast eligibility.
- **Main structure:** tract counts and shares for each pipeline checkpoint, readable state labels,
  and readiness-build lineage.
- **Caution:** candidate counts are availability screens, not final model populations. The 56 rows
  include territories found in canonical geography even when current ACS was not acquired there.

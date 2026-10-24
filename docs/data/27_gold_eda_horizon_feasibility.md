# `gold_eda_horizon_feasibility`

[Back to the data documentation index](README.md)

- **Layer:** Gold exploration summaries
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_eda_horizon_feasibility`
- **Sample:** [gold_eda_horizon_feasibility.jsonl](../../data/samples/gold_eda_horizon_feasibility.jsonl)

- **Grain and key:** one row per state FIPS code and forecast horizon.
- **Purpose:** tests whether one-, three-, and five-year FHFA targets can be constructed before the
  historical modeling panel is designed.
- **Main structure:** available tract-origin pairs, distinct tracts, earliest and latest usable
  forecast origins, and 10th/50th/90th percentiles of annualized HPI change.
- **Caution:** these are source-only pairs. Final training counts will be lower after enforcing
  feature timing, geography, and split rules.

# `gold_eda_fhfa_history`

[Back to the data documentation index](README.md)

- **Layer:** Gold exploration summaries
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_eda_fhfa_history`
- **Sample:** [gold_eda_fhfa_history.jsonl](../../data/samples/gold_eda_fhfa_history.jsonl)

- **Grain and key:** one row per state FIPS code represented in FHFA.
- **Purpose:** shows how many tracts have usable HPI history and how history depth varies by state.
- **Main structure:** source and usable tract counts, 10th/50th/90th percentiles of usable years,
  earliest usable year, latest usable year, and readiness-build lineage.
- **Caution:** this summarizes source availability. It does not guarantee that a tract also has
  point-in-time ACS features at a valid forecast origin.

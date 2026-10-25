# `gold_eda_hpi_temporal`

[Back to the data documentation index](README.md)

- **Layer:** Gold exploration summaries
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_eda_hpi_temporal`
- **Sample:** [gold_eda_hpi_temporal.jsonl](../../data/samples/gold_eda_hpi_temporal.jsonl)

- **Grain and key:** one row per geographic scope and FHFA observation year. The current scopes
  are the United States and the Arizona, Michigan, and Pennsylvania pilot states.
- **Purpose:** supports a consistent temporal view of the tract-level annual HPI change
  distribution without rescanning source history in plotting code.
- **Main structure:** source and available-value counts plus the 10th percentile, median, and 90th
  percentile annual HPI change.
- **Caution:** the set of reporting tracts changes over time. These summaries describe the
  available records and do not correct for changing coverage or define a causal housing cycle.

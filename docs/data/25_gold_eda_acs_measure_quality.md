# `gold_eda_acs_measure_quality`

[Back to the data documentation index](README.md)

- **Layer:** Gold exploration summaries
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_eda_acs_measure_quality`
- **Sample:** [gold_eda_acs_measure_quality.jsonl](../../data/samples/gold_eda_acs_measure_quality.jsonl)

- **Grain and key:** one row per governed measure in the latest ACS release.
- **Purpose:** compares missingness and sampling uncertainty before ACS measures are selected as
  similarity or forecasting features.
- **Main structure:** available and missing counts, median and 90th-percentile relative margins of
  error, and the share of tracts with relative MOE above 50 percent.
- **Caution:** relative MOE can be very large when a small housing category is near zero. Fine
  structure categories should not be treated as equally reliable across tracts merely because the
  estimate is non-null.

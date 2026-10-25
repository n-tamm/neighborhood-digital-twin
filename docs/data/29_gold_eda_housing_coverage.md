# `gold_eda_housing_coverage`

[Back to the data documentation index](README.md)

- **Layer:** Gold exploration summaries
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_eda_housing_coverage`
- **Sample:** [gold_eda_housing_coverage.jsonl](../../data/samples/gold_eda_housing_coverage.jsonl)

- **Grain and key:** one row per governed single-family housing-share band, including an explicit
  missing-composition band.
- **Purpose:** shows how FHFA history, forecast eligibility, and similarity eligibility vary with
  the type of housing found in a tract.
- **Main structure:** tract and candidate counts, coverage shares, median housing composition,
  median household income, and visual-EDA build lineage.
- **Caution:** FHFA is a single-family price index. Low coverage in multifamily-heavy tracts is a
  limitation of the target source, not evidence that those communities are unimportant or that
  their broader housing markets are unmeasurable.

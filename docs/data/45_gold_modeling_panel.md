# `gold_modeling_panel`

[Back to the data documentation index](README.md)

- **Layer:** Gold model readiness
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_modeling_panel`
- **Sample:** [gold_modeling_panel.jsonl](../../data/samples/gold_modeling_panel.jsonl)
- **Grain and key:** one canonical 2020 tract GEOID, forecast-origin year, and forecast horizon.
- **Purpose:** gives forecasting and retrospective analogue evaluation one governed join of raw
  point-in-time features, direct later outcomes, and fixed split assignments.
- **Main structure:** all feature-table fields; horizon and target endpoint; observed cumulative
  and annualized FHFA changes or censor reason; temporal and geographic roles; downstream
  eligibility flags; source and build lineage.

The November 7, 2026 build contains 2,090,658 rows, exactly reconciling to the split-assignment
table. It spans 63,367 tracts and 2011-2025 origins. Observed targets total 571,237 at one year,
380,562 at three years, and 203,694 at five years within this ACS-compatible feature window.
Decade-crossing targets remain as censored rows with
`target_censor_reason = 'crosses_decade_boundary'`; their split assignments carry
`ineligible_target`. No observed panel target crosses a calendar-decade boundary. Locked temporal
tests contain 42,082, 45,887, and 34,644 rows respectively.

The current eligible training rows cover nine origins (2011-2018 and 2020) at one year, three
origins (2011-2013) at three years, and two origins (2011-2012) at five years. Validation origins
are 2021-2022, 2014-2015, and 2013 respectively. This shortens the independent training history at
longer horizons; five-year performance must be treated as exploratory.

Retaining censored, purged, holdout, and future-scoring rows is intentional. Modeling code must
filter by the published eligibility fields rather than inventing a new random split or silently
dropping incomplete cases. Training-fitted preprocessing is still absent and belongs inside each
model pipeline.

Across all panel origins, one-year target observation is lowest for tracts below 25 percent
single-family housing at 78.4 percent, compared with 85.2-89.1 percent in the other housing-mix
bands. This is a coverage diagnostic, not a causal relationship. Evaluation must report housing
mix and target availability beside model error so favorable scores are not achieved only by
serving the places FHFA measures most consistently.

This panel is an analytical and training contract, not an application serving table. The
interactive application should read later prediction, analogue, explanation, and profile tables
that contain only the fields needed at request time.

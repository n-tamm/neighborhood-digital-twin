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

The table contains 2,090,658 rows, exactly reconciling to the split-assignment table. It spans
63,367 tracts and 2011-2025 origins. Observed targets total 614,217 at one year, 506,147 at three
years, and 398,725 at five years within this ACS-compatible feature window. Locked temporal tests
contain 42,082, 45,887, and 34,644 rows respectively.

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

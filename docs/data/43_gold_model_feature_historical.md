# `gold_model_feature_historical`

[Back to the data documentation index](README.md)

- **Layer:** Gold model readiness
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_model_feature_historical`
- **Sample:** [gold_model_feature_historical.jsonl](../../data/samples/gold_model_feature_historical.jsonl)
- **Grain and key:** one canonical 2020 tract GEOID and forecast-origin year.
- **Purpose:** provides raw, interpretable, point-in-time inputs for forecasting and retrospective
  similarity work without fitting preprocessing on future data.
- **Main structure:** Census hierarchy; FHFA origin level, lags, changes, volatility, and history
  coverage; county and state trend context; the most recent ACS profile available by the origin;
  margins of error and relative uncertainty; tract-vintage cohort flags; source and build lineage.

ACS is selected with `acs_available_year <= forecast_origin_year`. The published build contains no
future ACS selections and no pre-2021 rows outside the stable tract cohort. FHFA lags are retained
only when the expected calendar year exists; a missing year is not treated as an adjacent lag.
County and state fields summarize contemporaneous origin-year FHFA changes and are contextual
baselines, not tract adjacency features.

The table contains 696,886 rows across 63,367 tracts and origins from 2011 through 2025. The stable
longitudinal cohort contributes 628,846 rows across 45,967 tracts. A further 68,040 rows across
17,400 tracts belong to the broader post-2020-only cohort. The 59,607 stable tracts in the source
state panel become 45,967 here because a model feature row also needs a usable FHFA origin and an
ACS release available by that origin; the difference must be treated as analytical attrition, not
as a geography failure.

This is deliberately not a fully transformed design matrix. Scaling, imputation, feature
selection, PCA, and other learned transformations must be fitted inside the training data for a
given evaluation split. The FHFA fields describe its filtered single-family market and should not
be presented as full-market housing prices.

Core ACS counts, housing shares, and rates are complete within the published feature rows. Median
gross rent is the least complete profiled ACS estimate at 97.2 percent. Calendar-exact HPI lag
coverage is 96.8 percent at one year, 93.7 percent at three years, and 92.1 percent at five years.
Later model pipelines must handle this remaining missingness inside their training folds rather
than applying one global imputation before splitting.

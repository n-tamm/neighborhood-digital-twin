# Analytical Data and Cohorts

This document explains the shared data rules underneath the implemented EDA, forecast baselines,
and similarity baselines. These rules matter because a tract row is not automatically comparable
across every year, and a feature is only valid for forecasting if it would have been available at
the forecast date.

## Data population

The acquisition pipeline currently includes:

- ACS five-year tract releases for all 50 states and Washington, D.C., from 2010 through 2024;
- national FHFA tract HPI history through 2025;
- the Census 2010-to-2020 tract relationship file;
- 2020 tract display geometry; and
- a geography hierarchy of country, Census region, Census division, state, county, and tract.

The ACS releases are annual, but each release summarizes an overlapping five-year period. For
example, adjacent releases share four years of underlying survey responses. Treating them as
independent annual measurements would exaggerate the amount of new information and make short-term
changes look more precise than they are.

FHFA tract HPI measures a filtered single-family housing market. It is not an index of every home
or every housing type in a tract. The pipeline keeps multifamily and other housing-stock measures
so coverage and model error can be interpreted in light of that limitation.

## Why two tract cohorts are necessary

Census tract boundaries changed between 2010 and 2020. Many relationships are splits or merges,
so assigning all older observations to a 2020 tract would create false precision.

The project therefore uses two explicit cohorts:

| Cohort | Use | Coverage |
|---|---|---|
| Stable longitudinal cohort | Any analysis that crosses the 2020 tract redesign | 59,607 source tracts pass the conservative relationship rule before later model eligibility filters |
| Broad current-vintage cohort | Post-2020 profiles and analyses that do not require comparable pre-2020 tract history | Roughly 84,400 supported 2020-vintage tracts, with small release-to-release differences |

A tract enters the stable cohort only when it keeps the same GEOID, has a dominant relationship,
and at least 95% of source land maps to the target while at least 95% of target land comes from the
source. The model-feature table contains 45,967 of these stable tracts after also requiring a
usable FHFA forecast origin and an ACS release available by that origin. That reduction is model
sample attrition, not a geography-mapping failure.

The five Connecticut water-only GEOID exceptions are documented and excluded from strict
land-tract reconciliation. Connecticut's 2022 planning-region change is handled by the governed
bridge table rather than by forcing incompatible county identifiers together.

See [Tract Vintage Coverage](../TRACT_VINTAGE_COVERAGE.md) for the relationship tests, counts, and
Connecticut details.

## Point-in-time historical features

[`gold_model_feature_historical`](../data/43_gold_model_feature_historical.md) contains one row per
eligible tract and forecast-origin year before horizons are expanded. It currently has 696,886
rows across 63,367 tracts and forecast origins from 2011 through 2025.

For an origin year `t`, the row uses:

- HPI values and lags ending at `t`;
- county and state trends available at `t`; and
- the latest ACS release whose release year is no later than `t`.

It does not use a future ACS release simply because that release is available today. The table
also records ACS measurement age and relative margins of error so staleness and sampling
uncertainty can be evaluated rather than silently ignored.

The current core features are well populated, but not perfectly complete. Median gross rent is
the least complete of the selected ACS fields at about 97.2%. Exact one-, three-, and five-year
HPI lag coverage is approximately 96.8%, 93.7%, and 92.1%, respectively. The model pipeline
handles remaining numeric missingness with training-fitted median imputation.

## Forecast target and row grain

[`gold_modeling_panel`](../data/45_gold_modeling_panel.md) expands each historical feature row to
the supported one-, three-, and five-year horizons. Its grain is one tract, one forecast-origin
year, and one horizon. The table contains 2,090,658 rows.

The target is cumulative log change in FHFA tract HPI:

```text
log(HPI at origin + horizon / HPI at origin)
```

In plain language, the model predicts how much the tract's measured single-family HPI changes
between the starting year and the end of the selected horizon. Log change is used for fitting and
scoring because changes combine cleanly across time. Results can be converted to an annualized
percentage for display.

Observed target counts differ by horizon because later endpoints are not yet available:

| Horizon | Rows with an observed target | Locked-test rows |
|---|---:|---:|
| 1 year | 614,217 | 42,082 |
| 3 years | 506,147 | 45,887 |
| 5 years | 398,725 | 34,644 |

Target availability is also lower in tracts where detached single-family housing represents less
than 25% of housing stock. This is why the EDA and model evaluation report coverage and error by
housing composition.

## Temporal and geographic assignments

[`gold_model_split_assignment`](../data/44_gold_model_split_assignment.md) assigns every eligible
tract-origin-horizon row before a model is fit. Randomly splitting these rows would leak closely
related tract histories and overlapping ACS periods across the train and evaluation samples.

| Horizon | Training origins | Validation origins | Calibration origin | Locked test origin |
|---|---:|---|---:|---:|
| 1 year | 10 | 2021-2022 | 2023 | 2024 |
| 3 years | 6 | 2017-2018 | 2019 | 2022 |
| 5 years | 3 | 2014 | 2015 | 2020 |

Rows whose outcome would end after the relevant locked-test origin are purged from development.
Maine, North Dakota, West Virginia, and New Mexico are deterministic geographic holdouts, one from
each Census region. The current model results use training and validation roles only; calibration
and locked-test outcomes remain unused.

The one-year horizon is the primary result because it has ten independent training origins. The
three-year horizon is secondary. Five years is exploratory: many tract rows exist, but only three
independent training years support the temporal claim.

## Current analytical products

| Product | Grain and role |
|---|---|
| [`gold_tract_profile_current`](../data/17_gold_tract_profile_current.md) | One current descriptive profile per canonical tract |
| [`gold_similarity_candidate_current`](../data/18_gold_similarity_candidate_current.md) | Current tracts meeting the implemented similarity feature requirements |
| [`gold_forecast_candidate_current`](../data/19_gold_forecast_candidate_current.md) | Current tracts with the history needed to be considered for forecast use |
| [`gold_model_feature_historical`](../data/43_gold_model_feature_historical.md) | Point-in-time tract state by forecast origin |
| [`gold_model_split_assignment`](../data/44_gold_model_split_assignment.md) | Frozen temporal and geographic roles by tract, origin, and horizon |
| [`gold_modeling_panel`](../data/45_gold_modeling_panel.md) | Joined feature, target, and assignment table used by the forecast workflow |

These are analytical inputs, not application serving tables. In particular,
`gold_modeling_panel` includes evaluation-only fields and rows and should never be queried directly
by an interactive application.

## Interpretation rules shared by all analyses

1. Use the stable cohort for comparisons that cross the tract redesign; report the broader
   post-2020 cohort separately.
2. Describe FHFA results as single-family HPI results, not as the value of all housing.
3. Treat ACS releases as overlapping five-year estimates and use their margins of error when
   interpreting small differences.
4. Use display geometry for maps only. It is not approved for adjacency, distance, or spatial
   model features.
5. Do not treat tract rows as independent time replications. The number of forecast-origin years
   is the main temporal evidence limit.
6. Do not open calibration or locked-test roles while choosing a point model.

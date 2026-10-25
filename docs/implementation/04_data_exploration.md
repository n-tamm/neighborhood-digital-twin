# 04 — Data Exploration

## Purpose

Exploration should determine what the data can support, where it is biased or uncertain, and which relationships deserve formal testing. It is not a gallery of univariate charts and should not leak the final test period into model design.

## Implemented readiness checkpoint

The first repeatable EDA job is `data_readiness_eda`. It publishes four compact summaries in the
gold schema and records its publication checks in the quality schema:

- state-level attrition from canonical geography through ACS, FHFA, similarity, and forecast
  eligibility;
- current ACS missingness and relative margins of error by measure;
- FHFA history depth by state;
- one-, three-, and five-year FHFA tract-origin feasibility and observed annualized-change ranges.

The October 24, 2026 run retained 85,528 canonical tracts, 84,396 current ACS profiles, 63,930
tracts with FHFA history, 83,359 similarity candidates, and 51,263 current forecast candidates.
The source supports about 1.97 million one-year, 1.85 million three-year, and 1.73 million
five-year FHFA tract-origin pairs before feature timing and split rules reduce the sample.

The checkpoint also resolved Connecticut rather than accepting its prior zero forecast count. All
728 Connecticut FHFA identifiers use the new planning-region GEOIDs; all match the current side of
the audited bridge, and 662 tracts now pass the current forecast-availability screen. The gold job
now fails if a Connecticut FHFA identifier is not covered by that bridge.

ACS uncertainty is not uniform across feature families. Current total population has a median
relative MOE near 13.8%, while small housing categories can have median relative MOE above 100%.
For example, two-unit buildings exceed 50% relative MOE in about 58% of tracts. Feature selection
should therefore favor stable totals and broader housing shares, retain uncertainty indicators,
and test whether fine categories improve held-out performance enough to justify their noise.

## Implemented visual checkpoint

The `visual_eda` job completes the next descriptive pass with three additional governed tables and
a versioned figure manifest. It produces seven reviewed PNGs covering pipeline attrition, housing
composition, included-versus-excluded tracts, ACS uncertainty, FHFA behavior over time, forecast
eligibility maps, and recent HPI-change maps. The figures live in the managed
`neighborhood_twin_gold.eda_figures` volume; `gold_eda_figure_manifest` identifies the matched
current set and explains what each figure is intended to show.

The October 24, 2026 run found a strong housing-composition limitation in the forecasting target.
Among current-ACS tracts with less than 25% single-family housing, 21.2% have any FHFA history and
only 7.5% pass the current forecast screen. Those shares rise to 90.1% and 75.9% for tracts with at
least 90% single-family housing. Similarity coverage stays near complete across the nonmissing
housing bands, so this issue constrains the FHFA forecasting task rather than the national analogue
pool.

Forecast candidates are also observably different from excluded current-ACS tracts. The largest
standardized differences include single-family share (0.83), owner-occupancy rate (0.75),
multifamily share (-0.65), population (0.56), and occupancy rate (0.50). The forecasting results
must therefore be described as applying to the FHFA-covered, primarily single-family tract
population. They should not be presented as representative of every community or of all housing
types.

The temporal summaries confirm that a single random split would hide important market regimes.
For example, Arizona's tract median annual change ranges from -19.4% in 2009 to 32.3% in 2005. In
2025 the national distribution still spans -5.5% at the 10th percentile to 12.8% at the 90th,
with a 3.2% median. Forecast evaluation therefore needs chronological holdouts, regional
breakdowns, simple persistence and regional baselines, and uncertainty intervals. The full-history
chart is a source diagnostic only; final-test outcomes must not be used to select features,
transformations, or model settings.

This checkpoint supports retaining the national current-state similarity and application scope.
The source pipeline now also provides full national 2010-2024 ACS history, although the historical
modeling cohort still depends on the approved cross-vintage and point-in-time contracts. The EDA
also identifies a required product boundary: the application can describe all supported
communities, while FHFA-based forecasts must show their narrower eligibility and target
interpretation clearly.

## Exploration layers

### Coverage and attrition

Track the number of sources, files, rows, tracts, years, and metros after every meaningful step. Map where FHFA targets exist, where ACS quality filters remove observations, and where crosswalks are complex. Compare retained and excluded areas on observable regional characteristics and housing-stock composition. Measure whether FHFA availability or history length falls as multifamily share rises.

### Temporal behavior

Inspect the distribution, autocorrelation, trend, volatility, and regime behavior of HPI changes. Check how target availability changes at one-, three-, and five-year horizons. Examine whether ACS fields move plausibly given overlapping five-year windows and whether release lags vary.

### Spatial behavior

Map levels and changes, test spatial autocorrelation, and compare within-metro and between-metro variation. Inspect whether residual-like quantities appear spatially structured even under simple regional baselines. Avoid interpreting a smooth map as evidence of causality.

### Missingness and measurement quality

Treat missingness as data. Report missingness by year, geography, source, income or affordability band, and HPI history length. Examine ACS relative margins of error and whether poor measurement quality is concentrated in smaller or lower-density tracts.

### Candidate relationships

Examine lagged relationships between target and feature families using training periods only. Focus on effect stability across time and metros rather than a single pooled correlation. Flag transformations or outliers that change conclusions materially.

## Required questions

- Is HPI history itself likely to dominate the model?
- Do regional and neighboring-market trends add signal beyond persistence?
- Which ACS dimensions have enough temporal and geographic variation to matter?
- Are feature relationships stable across housing regimes?
- Where do coverage and uncertainty create a nonrepresentative sample?
- Where is the FHFA single-family target a limited description of the tract's overall housing stock?
- Does a national model appear plausible, or do region-specific patterns dominate?
- Which features are descriptive for the app but unsuitable for prediction?

## Outputs

- coverage map and pipeline attrition chart;
- source-year and geography coverage tables;
- target distribution and horizon-availability analysis;
- ACS margin-of-error and missingness analysis;
- FHFA coverage and history-length analysis by housing-stock composition;
- spatial autocorrelation and simple residual maps;
- training-period relationship and stability plots;
- initial feature-family recommendation;
- concise list of risks that feature engineering or evaluation must address.

## Notebook expectations

Number notebooks by question, not by author. Each notebook should name its inputs and versions, state whether the final test period is excluded, and finish with decisions or open questions. Move repeatable profiling functions and final figure generation into the package.

## Acceptance checks

- Row counts reconcile with the pipeline quality reports.
- Excluded and retained geographies are compared.
- Final-test outcomes are not used to choose features or transformations.
- Overlapping ACS estimates are not described as independent annual change.
- Every proposed feature family has a timing and data-quality rationale.
- At least one analysis challenges the project's assumptions rather than only supporting them.

## Handoff

Stage 05 receives a documented feature shortlist, target risks, missingness policy candidates, and evidence for which data families belong in the first neighborhood-state contract.

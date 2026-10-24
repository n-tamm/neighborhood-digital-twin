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

This checkpoint does not complete EDA. The next pass must add housing-composition coverage slices,
retained-versus-excluded comparisons, temporal plots, maps, and report-ready figures. It should use
the persisted summaries rather than recomputing national joins inside plotting cells.

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

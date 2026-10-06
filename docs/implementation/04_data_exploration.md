# 04 — Data Exploration

## Purpose

Exploration should determine what the data can support, where it is biased or uncertain, and which relationships deserve formal testing. It is not a gallery of univariate charts and should not leak the final test period into model design.

## Exploration layers

### Coverage and attrition

Track the number of sources, files, rows, tracts, years, and metros after every meaningful step. Map where FHFA targets exist, where ACS quality filters remove observations, and where crosswalks are complex. Compare retained and excluded areas on observable regional characteristics.

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
- Does a national model appear plausible, or do region-specific patterns dominate?
- Which features are descriptive for the app but unsuitable for prediction?

## Outputs

- coverage map and pipeline attrition chart;
- source-year and geography coverage tables;
- target distribution and horizon-availability analysis;
- ACS margin-of-error and missingness analysis;
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

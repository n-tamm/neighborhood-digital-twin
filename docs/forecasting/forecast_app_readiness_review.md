# Forecast Application Readiness Review

This review began as a pre-release checklist. The data-contract concern has now been resolved, the
final models have been evaluated, and the forecast release is active. This file records the
decisions so the app and report do not drift from the evidence.

## Resolved target and geography decision

The earlier workflow removed any target that crossed a calendar-decade boundary. That rule was
too broad. FHFA publishes one tract HPI history on 2020 tract geography, while the actual
cross-vintage concern comes from using pre-2020 ACS features.

The corrected contract therefore keeps fully observed FHFA outcomes. Whenever a feature history
crosses the 2020 tract redesign, the modeling row must belong to the reviewed 59,607-tract stable
cohort. Direct validation confirmed that no cross-2020 non-stable row enters the modeling panel.

## Completed release sequence

1. Jobs 301 and 302 rebuilt targets, split assignments, point-in-time features, and the modeling
   panel under the corrected contract.
2. Job 500 compared baselines, regularized linear regression, and gradient-boosted trees using
   origin-safe training and validation.
3. The one-year tree and three-year state-trend baseline were frozen before calibration.
4. Job 504 calibrated 90% split-conformal intervals, opened the locked tests once, and scored the
   current 2025 origin.
5. Job 605 applied a fixed release gate without selecting a replacement model.
6. Job 701 published compact forecasts and explicit availability behind a complete manifest.
7. The Databricks app received read-only access and now loads the newest complete forecast release
   independently of its analogue release.

## What appears in the application

For an eligible tract, the Forecast tab shows:

- the 2025 as-of year and one-year target endpoint;
- the annualized point estimate;
- lower and upper bounds from the 90% calibrated interval;
- the state-current-trend baseline;
- the FHFA single-family target definition;
- a global feature-family driver summary; and
- forecast release and model lineage.

The three-year horizon is not silently omitted. Its availability row says that it failed the
locked release gate, and the app reports its MAE relative to zero change and its interval coverage
relative to the release minimum.

## Coverage

There are 46,719 approved one-year forecast rows. The availability table contains both horizons
for all 85,528 current profile tracts. A tract without a one-year result retains a concrete
readiness reason. All three-year rows are unavailable because the horizon-level release gate
failed, not because 85,528 separate tract queries failed.

## Product limits

- FHFA measures a filtered single-family market, not all housing and not an individual property.
- A 90% interval describes historical model-error calibration; it cannot include every future
  shock.
- Driver text summarizes global ablation evidence. It is not a tract-level causal explanation.
- Historical analogues remain separate observed evidence and do not set the forecast interval.
- A future three-year research model requires a new contract and new future evaluation evidence.
  It cannot overwrite the reported 2022-2025 locked result.

## Remaining acceptance work

The modeling gate is complete. Remaining app work is product review: inspect eligible and
ineligible tracts across regions, confirm the forecast/analogue distinction is obvious, verify
empty states and mobile layout, and include the final screen and evaluation figures in the
report. Application evaluation should focus on whether required content is delivered correctly,
works reliably, and helps a user understand the evidence—not on click counts.

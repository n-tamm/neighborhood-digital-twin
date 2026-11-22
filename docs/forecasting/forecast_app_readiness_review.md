# Forecast Application Readiness Review

This review defines what the forecast workflow must publish before the app is considered current.

## Target and geography contract

The target is cumulative change in FHFA single-family tract HPI. Fully observed FHFA outcomes are
retained. When an input feature history crosses the 2020 tract redesign, the row must belong to the
reviewed 59,607-tract stable cohort. The target therefore stays broad enough to be useful without
mixing incompatible pre- and post-2020 community features.

## Required release sequence

1. Jobs 301 and 302 build targets, point-in-time features, split roles, and the modeling panel.
2. Job 500 compares five baselines, regularized linear regression, and gradient-boosted trees.
3. The linear and boosted-tree settings are frozen for both one and three years.
4. Job 504 calibrates separate 90% intervals, evaluates later outcomes, and scores the 2025
   current origin for all four model-horizon combinations.
5. Job 605 records evaluation warnings for each combination without selecting a replacement.
6. Job 606 produces side-by-side model evaluation figures.
7. Job 701 publishes both models at both horizons for every model-ready tract.
8. Job 900 reapplies descriptions and column comments after the schema overwrite.

## Required application content

For an eligible tract, the Forecast tab must show:

- the 2025 as-of year and target endpoint;
- regularized-linear and gradient-boosted-tree estimates at one and three years;
- a model-specific calibrated interval for every estimate;
- the state trend as a visibly separate baseline;
- evaluation warnings tied to the model and horizon that missed a threshold;
- the FHFA single-family target definition;
- the global, noncausal feature-family explanation; and
- release and model lineage.

The Data Science Results forecast section must focus on the model pipeline and evaluation:
validation design, candidate methods, MAE and RMSE, bias and tail error, interval coverage,
geographic and temporal slices, and the difference between a supervised model and a baseline.

## Availability contract

Availability is one row per current tract and horizon. A horizon is available only when both
supervised current predictions exist. The forecast table itself has two rows per tract and
horizon—one per model. A weak evaluation result remains available with its warning rather than
being deleted.

## Product limits

- FHFA measures a filtered single-family market, not all housing and not an individual property.
- A 90% interval describes historical model-error calibration and cannot include every future
  shock.
- Driver text summarizes global ablation evidence; it is not a tract-level causal explanation.
- Historical analogues are separate observed evidence and do not set the forecast interval.
- State and county trends are evaluation baselines and must never be labeled as the project's
  linear or nonlinear forecast.

## Acceptance checks

The corrected release is ready only after all four model-horizon combinations exist in model,
evaluation, and serving tables; current forecasts reconcile to availability; the figures show both
models; and representative eligible and ineligible tracts render correctly in the live app.

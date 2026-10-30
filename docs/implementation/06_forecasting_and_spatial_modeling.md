# 06 — Forecasting and Spatial Modeling

## Purpose

The forecasting stage tests whether public tract-level context improves on strong, simple expectations about future movement in the FHFA single-family HPI. It does not forecast prices for multifamily housing or the value of every home in a tract. The goal is not to try every algorithm. It is to establish a fair baseline ladder, select one defensible nonlinear model, and measure what spatial and feature-family additions contribute out of time.

## Evaluation splits before models

Freeze split definitions before tuning:

- early forecast origins for initial training;
- later origins for model comparison and tuning;
- a separate calibration period for uncertainty when needed;
- latest complete origins as the locked temporal test;
- one or more complete metros held out for geographic transfer.

Use expanding-window or rolling-origin evaluation. Do not randomly split tract-year rows. Adjacent observations from the same tract share history, and ACS releases overlap.

The first split contract is now frozen in `gold_model_split_assignment`. The locked test origins
are 2024, 2022, and 2020 for the one-, three-, and five-year horizons. Calibration uses 2023, 2019,
and 2015; validation uses 2021-2022, 2017-2018, and 2014. Labels that end after the applicable
locked test origin are purged. Maine, North Dakota, West Virginia, and New Mexico are held out as
the deterministic geographic transfer sample. If the team changes this contract, it should create
a new split version rather than overwrite the meaning of the existing evaluation.

The independent-year count is the binding limitation. One-year modeling has ten training origins
and three-year modeling has six; five-year modeling has only three. Repeated tract rows provide
cross-sectional information but do not turn three time origins into a large temporal sample. The
one-year horizon is therefore primary, three years is secondary, and five years should remain a
simple, exploratory comparison unless a revised design creates more defensible independent
periods.

The broader post-2020-only tract cohort first appears in validation and later periods because it
does not have stable pre-2020 geography. Report it separately from the stable longitudinal cohort.
Otherwise a change in the evaluated tract population could be mistaken for a change in temporal
forecast performance. The broader slice remains useful as a realistic test of current national
coverage, but the stable slice is the cleaner like-for-like time comparison.

## Baseline ladder

Every horizon should include the baselines it can support:

1. **Zero change:** no future HPI movement.
2. **Historical average:** tract or region follows its prior mean change.
3. **Persistence:** future change follows the most recent observed change.
4. **Regional trend:** tract follows recent county or CBSA movement.
5. **Regularized linear model:** lagged HPI plus the approved core feature set.

Baselines use the same rows, split, and metrics as the candidate model. A baseline should not receive less careful timing simply because it is simple.

### Implemented development scaffold

Job `500 Modeling | Forecast Baselines` now implements the first comparison checkpoint. It reads
`gold_modeling_panel`, fits no preprocessing outside the published training rows, and publishes
validation predictions from zero change, latest-change persistence, recent three-year mean,
county trend, state trend, and one L2-regularized linear model. The output scorecard uses MAE,
RMSE, median absolute error, directional accuracy, coverage, cohort, geography, housing mix, and
state slices. MLflow records the feature list, target, regularization, and aggregate validation
metrics.

The workflow is intentionally not a final model. It does not use calibration rows, does not open
the locked temporal tests, and does not serialize an application model yet. Its purpose is to
establish honest difficulty, expose weak slices, and show whether more complex modeling is worth
the added work. The five-year linear result should be interpreted cautiously because its training
sample contains only three independent origin years.

The first shared run completed on October 30, 2026 and published 1,369,401 validation predictions
and 1,068 scorecard rows. Regularized linear regression has the best overall one-year validation
MAE at 0.0724, compared with 0.0757 for the state-trend baseline. At three years, the state trend
is narrowly better at 0.0666 than the linear model at 0.0679. This is a useful warning against
assuming that the more elaborate model is automatically better. The five-year linear MAE is
0.0952, but that horizon remains exploratory because the fitted sample has only three independent
training origins.

The next forecast iteration should inspect subgroup scorecards and residual maps before adding
complexity. If the linear improvement is consistent enough across time, geography, housing mix,
cohort, and ACS uncertainty, compare one gradient-boosted model and a small feature-family
ablation. If not, improve the feature or target contract before broad model search. Calibration
rows and locked tests remain untouched until the point-model choice is frozen.

## Candidate nonlinear model

Select one gradient-boosted tree implementation based on missing-value support, training time, reproducibility, interpretability, Databricks compatibility, and team familiarity. HistGradientBoosting, XGBoost, LightGBM, or CatBoost can all be reasonable; the decision belongs in an ADR after a small comparison.

Fit a separate direct model for each horizon. Do not recursively feed one-year forecasts into later years for the MVP. Each horizon can have its own eligible population, preprocessing, parameters, calibration, and limitation statement.

Start from `gold_modeling_panel` and filter with its published eligibility fields. Do not rebuild
splits in a notebook. The shared feature table intentionally contains raw values: imputation,
scaling, encoding, feature selection, and any target-aware transformation must be fitted inside
the appropriate training fold.

## Training pipeline

The complete estimator should include training-fitted preprocessing and model logic. A run records:

- source, geography, feature, and target versions;
- split definition and eligible-row counts;
- feature list and preprocessing configuration;
- model family, parameters, seed, and library versions;
- metrics by fold and important slices;
- serialized estimator and schema signature;
- code commit and configuration hash.

MLflow is the planned experiment registry in Databricks. A small local run may use the same metadata structure without requiring a hosted tracking server.

## Spatial context

Add spatial information through explicit, lagged features before considering a graph model:

- weighted neighbor HPI change at prior periods;
- neighbor volatility or dispersion;
- county and CBSA recent trend;
- deviation of the tract from its regional trend;
- optional accessibility or distance context if later admitted.

Spatial features must be computable for new or held-out locations without using their future targets. Record neighbor count and missingness. An island tract needs a documented fallback rather than silently receiving zero.

County and state contemporaneous trend features are available for the first nonspatial baseline.
True tract-neighbor features are not yet approved because the current geometry is simplified for
display. The baseline and first nonlinear model should proceed without adjacency; add analytical
geometry only if the nonspatial comparison leaves a specific question worth the added pipeline
and validation work.

## Required ablations

Compare at least:

1. HPI history only;
2. HPI plus regional and macro context;
3. HPI plus housing and affordability features;
4. HPI plus socioeconomic context;
5. HPI plus neighbor context;
6. approved full model.

The ablation should use the same split and model settings where practical. Its purpose is to measure feature-family value, not to produce the highest possible number for each row.

## Model selection

Use mean absolute error as the primary point metric and inspect RMSE, median absolute error, directional accuracy against a majority-direction baseline, and performance relative to persistence and regional baselines. Report coverage and error by housing-stock composition as well as time, geography, HPI history length, and ACS quality. Selection should also consider calibration potential, geographic transfer, stability, runtime, and clarity.

Choose the champion on validation results, write the decision record, and stop broad model search. The locked test is for estimating final performance, not picking a winner.

Coverage must be reported alongside error. FHFA represents a filtered single-family market, and
earlier EDA showed substantially lower target coverage in heavily multifamily tracts. The model
can still use housing composition to describe where it is operating, but its output must not be
reframed as a forecast for the entire local housing market. The ACS inputs are overlapping
five-year estimates, so a non-overlapping-release sensitivity check is preferable where the
remaining origin count permits it.

## Required outputs

- fitted baseline implementations;
- candidate horizon-specific pipelines;
- MLflow or equivalent run records;
- validation scorecard by horizon and split;
- feature-family and spatial ablations;
- residual maps and error slices;
- approved model manifest and draft model card;
- prediction contract for downstream calibration and serving.

The initial prediction and scorecard contracts are documented as
`gold_forecast_baseline_prediction` and `gold_forecast_baseline_scorecard`. They remain
development artifacts rather than application serving tables.

## Acceptance checks

- no row from the future influences a training transformation;
- baseline and model scores use identical eligible rows;
- model output is reproducible with the recorded environment and seed;
- geographic holdout aggregates exclude held-out future targets;
- evaluation separates target availability and error by housing-stock composition;
- all predictions carry model, feature, target, and split versions;
- a complex model that fails to add meaningful value is reported honestly rather than hidden.

## Handoff

Stage 07 calibrates uncertainty and prepares explanations from frozen candidate predictions. Stage 10 owns the locked final evaluation. The application receives only approved predictions and metadata, not an open-ended experiment table.

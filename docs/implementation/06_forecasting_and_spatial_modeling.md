# 06 — Forecasting and Spatial Modeling

## Purpose

The forecasting stage tests whether public tract-level context improves on strong, simple expectations about future housing-market movement. The goal is not to try every algorithm. It is to establish a fair baseline ladder, select one defensible nonlinear model, and measure what spatial and feature-family additions contribute out of time.

## Evaluation splits before models

Freeze split definitions before tuning:

- early forecast origins for initial training;
- later origins for model comparison and tuning;
- a separate calibration period for uncertainty when needed;
- latest complete origins as the locked temporal test;
- one or more complete metros held out for geographic transfer.

Use expanding-window or rolling-origin evaluation. Do not randomly split tract-year rows. Adjacent observations from the same tract share history, and ACS releases overlap.

## Baseline ladder

Every horizon should include the baselines it can support:

1. **Zero change:** no future HPI movement.
2. **Historical average:** tract or region follows its prior mean change.
3. **Persistence:** future change follows the most recent observed change.
4. **Regional trend:** tract follows recent county or CBSA movement.
5. **Regularized linear model:** lagged HPI plus the approved core feature set.

Baselines use the same rows, split, and metrics as the candidate model. A baseline should not receive less careful timing simply because it is simple.

## Candidate nonlinear model

Select one gradient-boosted tree implementation based on missing-value support, training time, reproducibility, interpretability, Databricks compatibility, and team familiarity. HistGradientBoosting, XGBoost, LightGBM, or CatBoost can all be reasonable; the decision belongs in an ADR after a small comparison.

Fit a separate direct model for each horizon. Do not recursively feed one-year forecasts into later years for the MVP. Each horizon can have its own eligible population, preprocessing, parameters, calibration, and limitation statement.

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

Use mean absolute error as the primary point metric and inspect RMSE, median absolute error, directional accuracy against a majority-direction baseline, and performance relative to persistence and regional baselines. Selection should also consider calibration potential, geographic transfer, stability, runtime, and clarity.

Choose the champion on validation results, write the decision record, and stop broad model search. The locked test is for estimating final performance, not picking a winner.

## Required outputs

- fitted baseline implementations;
- candidate horizon-specific pipelines;
- MLflow or equivalent run records;
- validation scorecard by horizon and split;
- feature-family and spatial ablations;
- residual maps and error slices;
- approved model manifest and draft model card;
- prediction contract for downstream calibration and serving.

## Acceptance checks

- no row from the future influences a training transformation;
- baseline and model scores use identical eligible rows;
- model output is reproducible with the recorded environment and seed;
- geographic holdout aggregates exclude held-out future targets;
- all predictions carry model, feature, target, and split versions;
- a complex model that fails to add meaningful value is reported honestly rather than hidden.

## Handoff

Stage 07 calibrates uncertainty and prepares explanations from frozen candidate predictions. Stage 10 owns the locked final evaluation. The application receives only approved predictions and metadata, not an open-ended experiment table.

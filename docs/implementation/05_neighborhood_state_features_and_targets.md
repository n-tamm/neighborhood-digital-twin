# 05 — Neighborhood State, Features, and Targets

## Purpose

This stage turns aligned source tables into the project's central analytical products. Keep three ideas separate:

- the **neighborhood state** describes what is observed for a tract at a point in time;
- **model features** are leakage-safe transformations available at a forecast origin;
- **targets** describe later outcomes and are never part of the state used for prediction.

That separation lets the app describe a neighborhood without forcing every descriptive field into the predictive model.

## Neighborhood-state contract

The state table should have one row per canonical tract and state year. Required identity and lineage fields include:

- tract GEOID and geography version;
- state year and forecast-origin compatibility;
- county, state, region, and metro identifiers;
- source vintage or release chosen for each data family;
- measurement age and quality flags;
- feature-set or state-contract version;
- pipeline build identifier.

Candidate dimensions include housing history, affordability, population and households, income and employment context, tenure and vacancy, housing supply, regional macro conditions, spatial context, and selected slow-moving environmental attributes.

## Field registry

Maintain a registry for every state field and feature:

- name and plain-language definition;
- source and original variable;
- source and analytical geography;
- unit and transformation;
- reference period and availability lag;
- expected range and missingness policy;
- margin-of-error field when applicable;
- descriptive, predictive, scenario, audit, or display role;
- feature-family and version;
- ethical or interpretation note.

This registry becomes the data dictionary and prevents fields from changing meaning between notebooks, models, and the app.

## Feature construction

### Housing history

Use lagged HPI levels or log levels, one- and multi-year changes, recent momentum, volatility, history length, gap count, and coverage flags. Calculate every rolling feature using data no later than the forecast origin.

### Regional and spatial context

Build lagged county or CBSA trends and neighbor aggregates from training-safe values. A neighbor feature should document its relationship method, weight transform, minimum neighbor count, and missing-neighbor behavior. In geographic holdouts, target-derived regional features cannot include future outcomes from the held-out metro.

### ACS and slow-moving context

Prefer interpretable levels and slow changes over noisy annual differences. Carry estimates and margins of error together long enough to support quality filters, weights, or flags. Derived ratios must document their numerator, denominator, universe, and behavior when the denominator is small.

### Availability and quality features

Missingness indicators, measurement age, relative margin of error, HPI history length, and crosswalk confidence may help the model express uncertainty. They should not become a shortcut for learning protected or otherwise inappropriate proxies without review.

## Missing-data policy

Separate these cases:

- structurally unavailable;
- below a source reliability threshold;
- missing because of a failed join;
- not yet published at the forecast origin;
- intermittently absent within a history;
- excluded by project policy.

Do not replace all cases with the same sentinel. Fit imputers on training data only, keep important missingness flags, and compare results with complete-case or higher-quality subsets. The nonlinear model may handle nulls directly, but the pipeline must still explain them.

## Target definitions

Use direct horizon-specific targets. A proposed housing target is cumulative log HPI change from forecast origin `t` to `t+h`, with separate contracts for `h = 1`, `3`, and `5` years. Record:

- forecast origin and target end year;
- exact HPI observations used;
- whether either endpoint was missing or interpolated;
- horizon and annualization rule, if any;
- right-censoring reason;
- target-definition version.

The primary result is the one-year target. Longer horizons are retained only when their training and test samples remain credible.

## Preprocessing contract

Scaling, imputation, encoding, feature selection, and dimensionality reduction are fitted inside the training fold. Persist the fitted preprocessing object with the model. The feature table may hold raw, interpretable fields; it should not contain transformations estimated from the full dataset.

## Required outputs

- `gold_neighborhood_state`;
- horizon-specific `gold_features` and `gold_targets` or a clearly partitioned equivalent;
- feature registry and data dictionary draft;
- row-attrition and missingness report;
- state, feature, and target contract tests;
- one documented example row showing its source vintages and target construction.

## Acceptance checks

- tract-year keys are unique;
- every feature passes its availability-date rule;
- target endpoints occur strictly after the forecast origin;
- rolling features do not cross the forecast origin;
- units and transformations match the registry;
- regional fields retain their true geography;
- target censoring and row loss are reproducible;
- the application can display a state row without loading model-training internals.

## Handoff

Forecasting receives versioned features, targets, split assignments, and a preprocessing policy. Representations receive a selected subset of state dimensions with roles and units. The app receives descriptive state fields and quality flags through the later serving bundle.

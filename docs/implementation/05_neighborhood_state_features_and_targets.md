# 05 — Neighborhood State, Features, and Targets

## Purpose

This stage turns aligned source tables into the project's central analytical products. Keep three ideas separate:

- the **neighborhood state** describes what is observed for a tract at a point in time;
- **model features** are leakage-safe transformations available at a forecast origin;
- **targets** describe later outcomes and are never part of the state used for prediction.

That separation lets the app describe a neighborhood without forcing every descriptive field into the predictive model.

## Current implementation

`gold_tract_profile_current` is the first implemented current-state product. It keeps exactly one
row for each of the 85,528 canonical tracts and joins a deliberately compact set of ACS housing,
population, tenure, affordability, and housing-type fields with summarized FHFA history. Source
absence remains null and is accompanied by explicit `has_current_acs_profile` and
`has_fhfa_history` flags.

The table retains `acs_source_geoid` alongside the canonical `geoid_2020`. For most states these
values are the same. In Connecticut, 879 current ACS land-tract GEOIDs are connected through the
validated planning-region bridge, so their current descriptive profiles are available without
erasing the source identifier. Water-only tracts remain unprofiled.

Three filtered tables make downstream work easier without redefining the full project scope:

- `gold_similarity_candidate_current` requires current ACS coverage, positive population and
  housing-unit estimates, and at least eight of twelve governed similarity inputs;
- `gold_forecast_candidate_current` requires current ACS context plus at least ten usable FHFA
  observations with recent target coverage;
- `gold_application_demo_tract` keeps displayable current-profile tracts in Arizona, Michigan, and
  Pennsylvania for early application development.

These filters are intentionally called candidates. Feature selection, preprocessing, historical
target construction, time-aware evaluation, and subgroup diagnostics still determine whether a row
belongs in a final model. The full contracts and small real samples are in the
[current-profile table document](../data/17_gold_tract_profile_current.md).

The longitudinal state and target contracts are now implemented as three additional gold tables:

- `gold_historical_tract_coverage` exposes retained and excluded tract counts for every ACS
  release and alignment method;
- `gold_neighborhood_state_historical` contains 1,018,099 tract-release rows with conservative
  availability years and alignment lineage; and
- `gold_forecast_target_historical` contains 6,207,795 direct FHFA outcomes or explicit censored
  rows across one-, three-, and five-year horizons.

All three were published and passed their hard validation checks on October 26, 2026. Leakage-safe
feature construction and split assignment remain separate next-stage products rather than being
embedded in either the descriptive state or target tables.

## Neighborhood-state contract

Historical state rows do not have uniform geographic coverage. Under the
[tract vintage coverage contract](../TRACT_VINTAGE_COVERAGE.md), 2010-2019 ACS releases contribute
only the 59,607-tract conservative stable 2010-to-2020 subset. Releases on 2020 geography retain
roughly 84,400 supported tracts, with the audited Connecticut bridge applied where necessary.
This difference is not missing data to impute: it is a deliberate geography policy. A balanced
analysis spanning the vintage change must restrict later years to the same stable cohort; a
later-period analysis may use the broader coverage but must label the changed population. The
implemented state table retains the alignment method and the companion coverage table records
release-level denominators and exclusions.

The state table should have one row per canonical tract and state year. Required identity and lineage fields include:

- tract GEOID and geography version;
- state year and forecast-origin compatibility;
- county, state, region, and metro identifiers;
- source vintage or release chosen for each data family;
- measurement age and quality flags;
- feature-set or state-contract version;
- pipeline build identifier.

Candidate dimensions include single-family HPI history, housing-stock composition, affordability, population and households, income and employment context, tenure and vacancy, housing supply, regional macro conditions, spatial context, and selected slow-moving environmental attributes.

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

The registry and target contract must call this series the `FHFA single-family HPI`. Do not shorten the label to a general tract housing-price index in reports or application fields where that would hide its coverage limits.

### Housing-stock composition

Use ACS units-in-structure estimates to calculate three mutually exclusive shares:

- single-family: one-unit detached plus one-unit attached;
- multifamily: structures with two or more units;
- mobile/other: mobile homes, boats, recreational vehicles, vans, and other residual categories represented by the selected table.

Retain the total housing-unit denominator, source fields, margins of error or derived quality flags, and release vintage. Validate that the categories reconcile to the total within the documented tolerance. These shares may be used as descriptive state, analogue dimensions, model features, and evaluation slices, but they do not extend FHFA price coverage to multifamily housing.

### Regional and spatial context

Build lagged county or CBSA trends and neighbor aggregates from training-safe values. A neighbor feature should document its relationship method, weight transform, minimum neighbor count, and missing-neighbor behavior. In geographic holdouts, target-derived regional features cannot include future outcomes from the held-out metro.

### ACS and slow-moving context

The table may have one row per annual forecast origin, but an ACS tract value is an annually released five-year estimate, not a one-year measurement. Retain the release year and survey-window start and end. Prefer interpretable levels and slow changes over differences between heavily overlapping releases. Carry estimates and margins of error together long enough to support quality filters, weights, or flags. Derived ratios must document their numerator, denominator, universe, and behavior when the denominator is small.

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

Use direct horizon-specific targets. The proposed target is cumulative log change in the FHFA single-family HPI from forecast origin `t` to `t+h`, with separate contracts for `h = 1`, `3`, and `5` years. Record:

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

- current profile and explicit candidate cohorts (implemented as the four current gold tables);
- a historical neighborhood-state panel (implemented as
  `gold_neighborhood_state_historical`);
- horizon-specific targets (implemented as `gold_forecast_target_historical`);
- leakage-safe historical model features and published split assignments (next stage);
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
- housing-composition categories reconcile to the documented ACS universe;
- ACS release years and five-year survey windows remain distinguishable;
- target censoring and row loss are reproducible;
- the application can display a state row without loading model-training internals.

## Handoff

Forecasting receives versioned features, targets, split assignments, and a preprocessing policy. Representations receive a selected subset of state dimensions with roles and units. The app receives descriptive state fields and quality flags through the later serving bundle.

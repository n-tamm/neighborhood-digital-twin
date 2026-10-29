# Project Readiness and Next Implementation Steps

This is the working handoff as of October 29, 2026. The broader design remains in the
[roadmap](ROADMAP.md) and [implementation guide](docs/implementation/README.md).

## Current answer

The approved source and feature-preparation pipeline is complete enough to begin baseline
forecasting and retrospective similarity work. The project now has reproducible public-source
acquisition, bronze and silver transformations, governed geography, current and historical gold
products, point-in-time model features, fixed evaluation assignments, and a joined modeling
panel. There is no unresolved data-integrity or leakage failure blocking the first models.

This does not mean the whole project is complete. Forecast and similarity models, calibrated
uncertainty, model evaluation outputs, serving tables, and the interactive application still need
to be built. New source families should not be added until a baseline result or required app view
shows a specific gap.

## Data checkpoint

- ACS covers all 765 required state-release pairs for the 50 states and Washington, D.C., from
  2010 through 2024.
- FHFA tract HPI history is national through 2025.
- The valid hierarchy contains country, Census region, Census division, state, county, and tract.
- Pre-2020 ACS history uses the governed 59,607-tract stable geography subset; later releases keep
  roughly 84,400 supported tracts.
- `gold_model_feature_historical` contains 696,886 point-in-time rows across 63,367 tracts and
  2011-2025 forecast origins.
- `gold_model_split_assignment` and `gold_modeling_panel` each contain 2,090,658
  tract-origin-horizon rows and reconcile exactly.
- `gold_model_readiness_summary` contains 95 governed cohort, feature-completeness, ACS
  uncertainty, housing-mix, and split summaries.
- Maine, North Dakota, West Virginia, and New Mexico are the deterministic held-out states, one per
  Census region.
- All hard key, timing, availability, leakage, split, and reconciliation checks passed. The only
  current warning is that the five-year horizon has three independent training origins.
- Each new table has a Databricks description and column comments, a per-table document, and a
  small real sample in `data/samples/`.

## Important interpretation limits

- FHFA describes a filtered single-family market. It is not a forecast of multifamily prices or
  every home in a tract. Coverage and error must be reported by housing composition.
- ACS annual releases are overlapping five-year estimates, not independent one-year samples.
- The 59,607 source tracts in the stable geography cohort become 45,967 stable tracts in the
  model-feature table after requiring a usable FHFA origin and an ACS release available by that
  date. This is model-sample attrition, not a failed geography mapping.
- The one-year horizon has ten training origins and is the primary result. Three years has six and
  is secondary. Five years has three and should remain exploratory with simple models.
- The broad post-2020 cohort appears only in later origins. Report stable-cohort performance
  separately so geographic expansion is not mistaken for temporal model deterioration or gain.
- County and state trend features are implemented. True tract adjacency is not: the current
  geometry is approved for display only.
- The current feature and modeling tables are analytical products, not application serving
  tables. They are too wide and contain evaluation-only rows and fields.

## Immediate next sequence

### 1. Forecasting baseline pass

- Profile feature missingness and eligible-row attrition by horizon, origin year, region, held-out
  state, housing mix, ACS uncertainty, and stable versus broad cohort.
- Implement zero-change, historical-average, persistence, and county/state regional baselines.
- Fit one regularized linear pipeline with all preprocessing learned inside the training rows.
- Compare every model on identical published validation rows; do not inspect the locked tests for
  model choice.
- Record MAE, RMSE, median absolute error, directional accuracy, coverage, and subgroup results.
- Report stable-cohort and broader post-2020 results separately, as well as housing-mix and ACS
  uncertainty slices.

### 2. Similarity baseline pass

- Freeze a small, interpretable feature registry and feature-family weights.
- Fit scaling on development data and compare standardized Euclidean retrieval with PCA retrieval.
- Build current-state matches first, then use `gold_model_feature_historical` for time-safe
  retrospective analogue evaluation.
- Exclude the same tract and future candidate states; report important differences as well as
  shared strengths.
- Evaluate retrieval stability, distance separation, geographic diversity, coverage, reviewed
  cases, and later-outcome utility without making FHFA availability the definition of similarity.

### 3. Descriptive application shell

- Start a thin Streamlit application using current profiles, display geometry, housing
  composition, source dates, FHFA history, and explicit coverage warnings.
- Keep app data access behind a small serving interface so later forecast and analogue tables can
  be added without rewriting pages.
- Do not read `gold_modeling_panel` directly from the UI.
- Show unavailable forecasts as an explained state while preserving the descriptive profile.

### 4. Model and product decisions

- After the baseline scorecards, decide whether one gradient-boosted tree earns a focused
  comparison with the regularized linear model.
- Decide whether analytical adjacency, CBSA membership, or macroeconomic data would answer a
  demonstrated gap. None is required before the baseline checkpoint.
- Select and calibrate one uncertainty method using the reserved calibration origins.
- Publish versioned forecast, interval, explanation, analogue, and evaluation tables only after
  validation passes.

### 5. Serving and integration

- Build compact serving tables and a release manifest from approved outputs.
- Connect the application to the serving contract, then add forecasts, analogues, explanations,
  and guarded scenario sensitivity.
- Add application contract tests, smoke tests, accessibility review, and deployment runbooks.

## Parallel ownership for two people

| Workstream | Primary responsibility | Shared boundary |
|---|---|---|
| Forecasting | Missingness/attrition review, baseline ladder, linear and selected nonlinear model, interval calibration | Owns modeling-panel filters and model-evaluation tables |
| Similarity and app | Representation registry, current and retrospective retrieval, case review, Streamlit descriptive shell | Owns analogue outputs and serving-interface prototype |

Both workstreams use the published feature and split contracts without changing them privately.
One person should temporarily own shared edits to `databricks.yml` and table metadata. App work can
proceed against current profiles while model work runs; forecast and analogue pages should wait
for approved output tables rather than mock analytical claims.

## Definition of the next checkpoint

The next checkpoint is complete when:

- the baseline models run from the published split and panel tables;
- all forecast candidates use identical validation rows and have a subgroup scorecard;
- the locked temporal tests remain untouched during model selection;
- the current-state similarity baseline has stability results and reviewed examples;
- retrospective analogue evaluation uses only information available at each query date;
- a descriptive application shell reads a documented serving interface; and
- the team has an evidence-based decision on nonlinear forecasting, analytical adjacency, and any
  additional source family.

At that point, the work moves from data preparation into model selection, calibrated outputs, and
application integration rather than further general-purpose ETL expansion.

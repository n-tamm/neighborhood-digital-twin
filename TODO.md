# Project Readiness and Next Implementation Steps

This is the operational handoff for the next development sessions. It records what is actually
implemented as of October 28, 2026, what can begin now, and what still separates the validated
source pipeline from modeling and application-ready products. The [project roadmap](ROADMAP.md)
and [implementation guides](docs/implementation/README.md) remain the broader plan.

## Current answer

The approved ACS, FHFA, and Census geography pipeline is complete through validated historical
state and target products. No unresolved source-acquisition, geography, or hard table-validation
problem prevents the project from moving into modeling preparation.

The project is **not yet fully model-ready or application-ready**, however. The existing gold
tables are governed analytical inputs, not the final feature, split, prediction, analogue, or
serving contracts. Forecast modeling still needs point-in-time features and frozen evaluation
assignments. Similarity baseline work and a descriptive application shell can start immediately,
but retrospective analogues and the full application need later model outputs.

No new socioeconomic, development, environmental, or macroeconomic source is needed before the
first forecasting and similarity baselines. Additional data should be admitted only after a
baseline or required application view demonstrates a specific gap.

## What is complete

### Acquisition, bronze, and governance

- Public FHFA, ACS, Census relationship, display-geometry, and Connecticut reference sources are
  stored as governed snapshots with checksums, source metadata, and validation history.
- Source/bronze, silver, gold, and quality outputs are separated into distinct Unity Catalog
  schemas.
- ACS coverage is complete for all 765 required state-release pairs across the 50 states and
  Washington, D.C., from 2010 through 2024.
- FHFA tract history is available nationally through 2025.
- Raw national files and credentials remain outside Git; source manifests and reproducible code
  remain in the repository and Databricks.

### Clean analytical source tables

- Silver FHFA, normalized ACS measures, generated ACS tract-release rows, Census relationships,
  display geometry, Connecticut bridge, and geography dimensions are implemented and validated.
- The hierarchy contains one country, four Census regions, nine divisions, 51 state equivalents,
  3,143 county equivalents, and 84,414 supported canonical 2020 tracts.
- The canonical dimension contains 85,528 source-universe tracts. Supported analytical coverage
  remains explicit rather than forcing territories or water-only records into the project scope.
- The Connecticut bridge resolves all 879 current land tracts and all 728 FHFA identifiers used
  by the project. Five current water-only ACS tracts remain documented exceptions rather than
  failed joins.

### Current-state and exploratory gold products

- `gold_tract_profile_current`: 85,528 canonical tract profiles with explicit ACS and FHFA
  coverage flags.
- `gold_similarity_candidate_current`: 83,359 nationally distributed candidates that pass the
  first availability screen.
- `gold_forecast_candidate_current`: 51,263 current candidates with enough recent FHFA history for
  initial forecasting work.
- `gold_application_demo_tract`: 8,182 displayable tracts in Arizona, Michigan, and Pennsylvania
  for application prototyping. This is a development slice, not the final national scope.
- Governed EDA summary tables and seven reviewed, versioned figures cover source readiness,
  housing composition, target selection, cohort differences, and temporal FHFA behavior.

### Historical gold products

- `gold_historical_tract_coverage`: 40 rows explaining retention and exclusion across every ACS
  release and alignment method.
- `gold_neighborhood_state_historical`: 1,018,099 rows covering 2010-2024 ACS releases with source
  and canonical GEOIDs, availability year, survey period, alignment method, selected neighborhood
  state, and source lineage.
- `gold_forecast_target_historical`: 6,207,795 direct one-, three-, and five-year FHFA target rows
  with observed endpoints or explicit censor reasons.
- The stable pre-2020 cohort contains 59,607 tracts in each release. Later releases retain roughly
  84,400 supported tracts. This difference is documented and must remain visible in model samples
  and application coverage.
- The latest historical build passed uniqueness, availability-year, alignment, horizon, target
  timing, and censoring checks with no unresolved hard failures.

### Documentation and metadata

- Every implemented table has a separate data document, a small real sample, a managed table
  description, and source-controlled column comments.
- The repository contains run commands, architecture and implementation guidance, source policy,
  EDA reproduction instructions, and tract-vintage coverage rules.

## Readiness by downstream activity

| Activity | Status | What can be used now | What is still needed |
|---|---|---|---|
| Source and table exploration | Ready | Silver source tables, current profiles, historical state, targets, EDA summaries, samples, and metadata | Only question-specific exploration and issue follow-up |
| Current-state similarity baseline | Ready to begin | `gold_similarity_candidate_current` and governed current profile fields | Frozen representation fields, training-only scaling, neighbor tables, stability tests, and case review |
| Retrospective historical analogues | Inputs ready; implementation incomplete | Historical state, direct later outcomes, availability and geography lineage | Time-safe query/candidate construction, representation versions, same-tract/neighbor exclusions, and evaluation tables |
| Forecast modeling | Source inputs ready; not yet model-ready | Historical neighborhood state, FHFA history, direct targets, hierarchy, and coverage flags | Point-in-time features, HPI lags, regional baselines, split assignments, joined panel, attrition report, and leakage validation |
| Descriptive application prototype | Ready to begin | Demo tract profiles, simplified display geometry, current values, history, source dates, and coverage warnings | Streamlit code, serving-schema loader, map/detail components, and contract tests |
| Forecast/analogue/scenario application | Not ready | Planned contracts and current descriptive data | Approved predictions, intervals, explanations, analogue results, scenario outputs, and versioned serving tables |
| Production-style refresh and serving | Partially ready | Separate Databricks jobs, schemas, metadata job, source manifests, and validated Delta tables | Model jobs, serving-bundle job, persisted integration tests, release manifest, app smoke tests, and operating runbook |

## Why the current historical tables are not yet a modeling panel

`gold_neighborhood_state_historical` has one row per tract and ACS release. A forecast row needs
one row per tract and forecast origin, using the latest ACS release that was actually available at
that origin. It also needs point-in-time FHFA lags and regional summaries. Those selections have
not yet been materialized.

`gold_forecast_target_historical` intentionally contains more FHFA history than the ACS feature
window. Joining the two tables without an explicit availability rule would either lose rows
silently or attach a later ACS release to an earlier forecast. The next stage must make this
attrition and timing visible.

The current tables also do not contain training-fitted imputation, scaling, PCA, feature
selection, or other learned transformations. They should remain out of the shared feature table;
those transformations belong inside training folds so the validation and test distributions do
not influence the fitted preprocessing.

## Required next data products

### 1. Freeze the feature and evaluation contract

The team should approve and version:

- the exact forecast-origin definition and maximum age allowed for each source family;
- the initial raw feature registry, including role, unit, source, availability, missingness rule,
  and whether the field is used for forecasting, similarity, display, or evaluation only;
- the balanced 59,607-tract long-history cohort versus the broader post-2020 cohort;
- training, validation, calibration, locked-test, and geographic-holdout rules; and
- the first regional baseline geography, using the existing county or state hierarchy unless a
  new geography is deliberately admitted.

The current evaluation draft proposes locked forecast origins of 2024 for one year, 2022 for
three years, and 2020 for five years. It also proposes a deterministic state-level geographic
holdout stratified by Census region. These are implementation candidates, not final tables, until
both teammates review them.

### 2. Build `gold_model_feature_historical`

Recommended grain: one canonical tract and forecast origin per row.

The first version should include:

- the most recent ACS release with `acs_available_year <= forecast_origin_year`;
- ACS release, survey window, source geography, alignment method, and measurement-age fields;
- raw, interpretable housing composition, tenure, vacancy, population, income, rent, and value
  fields with margins of error where available;
- lagged FHFA level, one- and multi-year changes, history length, missingness, and recent
  volatility calculated using data no later than the origin;
- leakage-safe county or state trend features from the existing hierarchy;
- stable-cohort, current-coverage, source-quality, and target-representativeness flags; and
- feature-contract version and build lineage.

Do not put globally standardized values, training-fitted imputations, PCA components, or selected
features into this shared raw feature table.

### 3. Build `gold_model_split_assignment`

Recommended grain: forecast origin, horizon, canonical tract, and evaluation definition.

The table should publish:

- training, validation, calibration, locked temporal-test, and geographic-holdout roles;
- fold cutoff and the latest allowed target endpoint for training rows;
- stable-history versus broader-post-2020 cohort assignment;
- the deterministic geographic-holdout seed and selected states;
- target eligibility and censoring status; and
- split-contract version and lineage.

No training or calibration row may have a target endpoint later than its fold cutoff. Random
tract-year splitting is not an acceptable fallback.

### 4. Build `gold_modeling_panel`

Join raw point-in-time features, direct horizon targets, and split assignments into the explicit
training contract. Retain unavailable or excluded rows long enough to produce an attrition table;
do not silently publish only complete cases.

Required validation includes:

- unique tract-origin-horizon keys;
- selected ACS availability no later than the forecast origin;
- all lag and rolling windows ending at or before the origin;
- target end equal to origin plus horizon;
- training/calibration target endpoints no later than the fold cutoff;
- consistent geography and cohort identifiers;
- identical eligible evaluation rows for every baseline and candidate model;
- reconciled row counts from features, targets, splits, and exclusions; and
- missingness and sample sizes by year, horizon, region, housing mix, and cohort.

### 5. Publish a model-readiness report

Before fitting the nonlinear model, report:

- row flow from historical state and FHFA history into each horizon;
- available origin years and independent evaluation periods;
- feature missingness and ACS uncertainty;
- balanced versus broad cohort composition;
- geographic-holdout coverage;
- housing-composition differences between eligible and excluded target rows; and
- every warning or failed contract check.

## Do we need more data now?

### Not before baseline modeling

The current sources are enough to build credible first versions of:

- zero-change, persistence, historical-average, and county/state regional forecast baselines;
- a regularized linear model and one gradient-boosted-tree model;
- current-state standardized Euclidean and PCA similarity baselines;
- retrospective analogue evaluation using existing state and target history; and
- a descriptive map/profile application prototype.

Adding more data now would increase timing, geography, missingness, and evaluation work before the
project has established what the current information can achieve.

### Likely needed for the planned spatial comparison

The existing cartographic geometry is approved for display only. It must not be used for tract
adjacency, distance, area, or spatial weights. If the MVP retains a true neighboring-tract
with/without-spatial-context comparison, add a reviewed analytical geography source such as the
appropriate national TIGER/Line tract geometry or an authoritative adjacency product. Build and
validate that product in a separate stage after the nonspatial baselines work.

County and state regional features can be implemented now and may serve as the first contextual
baseline, but they are not the same as tract adjacency.

### Useful only if a measured gap justifies them

- **CBSA/metro membership:** useful for metro comparisons, metro holdouts, and regional trends,
  but not necessary while the existing state/county evaluation is the approved first version.
- **FRED/ALFRED:** mortgage rates, inflation, and labor-market regime context. Add only with a
  point-in-time vintage policy and an ablation showing value beyond tract and regional history.
- **Building Permits Survey:** supply and development context at county or metro grain.
- **LEHD or County Business Patterns:** employment access and business context, with additional
  volume and geography work.
- **FEMA or NOAA:** environmental context for description or long-run sensitivity, not an annual
  causal housing driver.

These sources can enrich the Digital Twin later, but none should block the next modeling
checkpoint. The first application should describe only the domains that are actually populated;
it should not claim that development or environmental state is already represented.

## Parallel work that avoids blockers

### Workstream A: model-ready historical data and forecasting

Suggested branch: `data/model-ready-panel`

- finalize feature, split, and cohort contracts;
- build point-in-time feature, split-assignment, and joined modeling tables;
- publish validation and attrition results;
- fit zero-change, historical-average, persistence, regional, and regularized-linear baselines;
- own shared edits to `databricks.yml`, table metadata, and new gold-table documentation during
  this stage.

### Workstream B: similarity and descriptive application foundation

Suggested branch: `model/similarity-baseline`

- build standardized Euclidean nearest-neighbor retrieval from the current similarity cohort;
- compare original feature space with PCA using training-fitted transformations;
- store rank, distance, feature version, shared similarities, and important differences;
- test top-neighbor stability and review representative successes and failures;
- build a thin Streamlit shell for tract selection, map, current profile, housing mix, history,
  source dates, and coverage warnings using the existing demo table.

This workstream can build current-state retrieval now. Time-safe historical analogue evaluation
should wait for Workstream A's point-in-time feature and split contracts.

### Coordination rules

- Create both branches from the same reviewed contract commit.
- Give one person temporary ownership of shared Databricks configuration and metadata files.
- Do not run competing jobs that publish the same canonical table.
- Keep experimental tables separate from canonical gold outputs until validation passes.
- Put reusable logic in `src/neighborhood_twin/`; notebooks should orchestrate or investigate.
- Merge the model-ready data contract before adding retrospective evaluation to the similarity
  branch.

## Recommended implementation order

1. Review and freeze the feature, cohort, and split contract.
2. Build and validate point-in-time historical features.
3. Publish split assignments and the joined model-ready panel.
4. Produce the attrition and leakage-readiness report.
5. In parallel, complete the current-state similarity baseline and descriptive app shell.
6. Fit forecast baselines on identical rows and run the first retrospective analogue evaluation.
7. Decide whether analytical adjacency, metro membership, or macro context earns admission.
8. Select one nonlinear forecast model and one uncertainty method on validation evidence.
9. Publish predictions, intervals, explanations, and historical analogue outputs.
10. Build compact versioned serving tables, scenario outputs, and the full interactive app.

## Definition of the next checkpoint

The next checkpoint is complete when:

- feature, split, cohort, and target contracts are reviewed and versioned;
- point-in-time feature, split-assignment, and modeling-panel tables are live in Databricks;
- every new table has metadata, documentation, a small sample, and zero unresolved hard failures;
- a row-attrition and leakage report explains every exclusion;
- all forecast baselines are evaluated on identical rolling and geographic splits;
- the current-state similarity baseline has stability metrics and reviewed cases;
- the app shell reads a versioned descriptive serving contract rather than analytical internals;
  and
- the team has a written evidence-based decision on analytical adjacency and any other added
  source.

At that point, the data pipeline is complete for baseline modeling. Later prediction, analogue,
scenario, and serving tables are model/application products built on top of that pipeline rather
than unfinished source ETL.

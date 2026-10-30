# Project Readiness and Next Implementation Steps

This is the working handoff as of October 30, 2026. The broader design remains in the
[roadmap](ROADMAP.md) and [implementation guide](docs/implementation/README.md).

## Current answer

The approved source and feature-preparation pipeline is complete, and the first forecasting and
current-state similarity baselines now run in Databricks. The project has reproducible public-source
acquisition, bronze and silver transformations, governed geography, current and historical gold
products, point-in-time model features, fixed evaluation assignments, and a joined modeling
panel, tracked experiments, validation-only forecast scorecards, reviewable neighborhood matches,
and seven versioned model-evaluation figures. Model outputs and diagnostics now live outside gold
in dedicated model and evaluation schemas. There is no unresolved data-integrity or leakage
failure blocking the next model stage.

This does not mean the whole project is complete. Forecast model selection, time-safe historical
analogue evaluation, calibrated uncertainty, serving tables, and the interactive application still
need to be built. New source families should not be added until a baseline result or required app
view shows a specific gap.

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
- The 21 Databricks jobs use numbered layer ranges (`000`, `100-104`, `200-205`, `300-302`,
  `400-401`, `500-501`, `600`, and `900`), grouping tags, and the maintained
  [pipeline run-order guide](docs/PIPELINE_RUN_ORDER.md).

## Baseline modeling checkpoint

- Job `500 Modeling | Forecast Baselines` completed on October 30 and published 1,369,401
  validation predictions across 59,562 tracts and six methods, plus 1,248 sliced scorecard rows.
- The regularized linear model has the best overall one-year validation MAE at 0.0724. The state
  trend is close at 0.0757, which sets a strong and interpretable baseline.
- At three years, the state trend is narrowly best at 0.0666, compared with 0.0679 for the linear
  model. More model complexity has not yet earned a clear win at this horizon.
- The five-year linear MAE is 0.0952, but it remains exploratory because the training contract has
  only three independent origins. It must not drive broad claims or extensive tuning.
- Job `501 Modeling | Similarity Baselines` published 120 matches for six review queries under
  standardized raw and six-component PCA representations. PCA retains 95.5% of standardized
  variance.
- The raw and PCA top-10 lists overlap by 5.5 matches on average. Both search nationally rather
  than collapsing to same-state results, but the moderate overlap means representation choice is
  consequential and still needs case review and time-safe retrospective evaluation.
- Directional accuracy is not currently informative by itself. Positive outcomes make up about
  90.2% of one-year validation rows and more than 97% at longer horizons, and the strongest models
  add essentially no directional lift over always predicting that majority direction.
- Both jobs record reproducible parameters and metrics in shared MLflow experiments. The first
  forecast attempt exposed a missing shared experiment parent folder; the notebooks now create it
  idempotently so a fresh workspace does not require a manual MLflow setup step.
- Job `600 Evaluation | Model Diagnostics` published seven versioned PNGs and a run-linked
  manifest in `neighborhood_twin_evaluation`. The figures cover accuracy, skill over zero change,
  bias and tail error, geographic transfer, housing composition, similarity representation, and
  independent forecast-origin stability. All seven passed publication checks and visual review.
- The expanded visual EDA run published twelve checked PNGs. It adds tract-vintage coverage,
  feature completeness, split-origin evidence, improved tract maps, dissolved county displays,
  and a national state-coverage view. Display geometry remains prohibited for spatial modeling.

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
- Current metrics and figures are validation evidence. They do not replace calibrated interval
  evaluation or the locked temporal test, which must remain unopened until model choices freeze.

## Decisions to freeze before the next model iteration

The first baseline has made these choices concrete. The team should review them before nonlinear
modeling, calibration, or retrospective analogue work:

1. **Forecast horizons:** keep one year as the primary result, three years as secondary, and
   either retain five years as explicitly exploratory or remove it from the MVP.
2. **Target contract:** model cumulative log change in the FHFA single-family HPI, then transform
   it into a readable percentage for presentation. Do not relabel it as the entire housing market.
3. **Evaluation populations:** use the stable cohort for the cleanest like-for-like temporal
   comparison and report the broader post-2020 cohort separately as a current-coverage transfer
   test.
4. **Geographic holdout:** review whether Maine, North Dakota, West Virginia, and New Mexico are
   sufficient as the final geographic transfer test. They provide regional diversity but are
   relatively small states. Additional blocked state validation can supplement them without
   changing the locked contract.
5. **Feature registry:** mark every field as forecasting, similarity, display, quality, scenario,
   or evaluation-only. Freeze units and missingness rules before building preprocessing pipelines.
6. **Model selection rule:** use validation evidence to decide whether one nonlinear model earns
   further work. Do not search many model families or use the locked tests for selection.

Changing one of the frozen target or split definitions later should create a new contract version
rather than silently replacing the meaning of an existing result.

## Data additions under consideration

No new source is required before baseline forecasting and similarity work. The first results
should determine whether added data is worth its timing, geography, and validation cost.

- **Bounded ACS expansion:** the current state is strongest on housing, tenure, income, rent, and
  value. If similarity results feel too housing-centric, consider a small expansion covering age,
  education, poverty or employment, household composition, and commuting. This is the least
  disruptive way to broaden the community representation because it reuses the existing ACS
  source, geography, and release logic.
- **Slow ACS change features:** the current model-ready table primarily contains point-in-time
  ACS levels. After the baseline, test a few slow or non-overlapping changes rather than noisy
  annual differences between overlapping five-year releases.
- **Analytical tract geometry:** add only if true adjacency, distance, or neighbor features remain
  part of the selected model. Current geometry remains display-only.
- **CBSA or metro membership:** add only if metro comparison, metro context, or metro holdouts
  become an explicit application or evaluation requirement.
- **Macroeconomic, permits, development, environmental, or business data:** defer until an
  ablation, failed application view, or scenario requirement identifies a specific gap.

Until any expansion is implemented, describe the product as housing-focused neighborhood
intelligence rather than implying that health, amenities, development, environment, and every
dimension of lived experience are already represented.

## Immediate next sequence

### 0. Review and freeze contracts

- Approve the horizon, target, cohort, geographic-holdout, feature-role, and model-selection
  decisions above.
- Record any revision through a new schema or contract version before fitting models.
- Leave the locked temporal tests unopened during all following development work.

### 1. Forecasting baseline pass: implemented, now review

- Profile feature missingness and eligible-row attrition by horizon, origin year, region, held-out
  state, housing mix, ACS uncertainty, and stable versus broad cohort.
- Review the implemented zero-change, persistence, recent-history, county/state, and regularized
  linear results rather than adding another baseline family immediately.
- Confirm the regularized linear preprocessing and feature registry before nonlinear comparison.
- Use cumulative log HPI change as the modeling target and transform predictions only for
  reporting.
- Compare every model on identical published validation rows; do not inspect the locked tests for
  model choice.
- Record MAE, RMSE, median and 90th-percentile absolute error, signed bias, R-squared, skill over
  zero change, directional lift over the majority rule, and subgroup results.
- Report stable-cohort and broader post-2020 results separately, as well as housing-mix and ACS
  uncertainty slices.
- Keep recording source, feature, target, split, parameters, metrics, environment, and artifacts
  in MLflow; the first shared experiment is now established.
- After the baseline scorecard, compare at most one focused gradient-boosted-tree candidate and
  run feature-family ablations before selecting a champion.
- Use the reserved calibration origins for prediction intervals, then open the locked tests only
  after point-model and uncertainty choices are final.
- Add fold- or origin-aware uncertainty around comparison metrics where the number of independent
  origins supports it; do not present tract-row counts as the number of independent replications.

### 2. Similarity baseline pass: current-state scaffold implemented

- Freeze a small, interpretable feature registry and feature-family weights.
- Review the implemented standardized Euclidean and PCA matches for the six initial query tracts.
- Use `gold_model_feature_historical` next for time-safe retrospective analogue evaluation with
  transforms fitted only on the appropriate development period.
- Exclude the same tract and future candidate states; report important differences as well as
  shared strengths.
- Evaluate retrieval stability, distance separation, geographic diversity, coverage, reviewed
  cases, and later-outcome utility without making FHFA availability the definition of similarity.
- Preserve useful ACS-based similarity for multifamily-heavy or FHFA-uncovered communities even
  when later-outcome evaluation is unavailable.
- Publish rank, distance, representation version, shared strengths, and important differences so
  the application can explain each match.

### 3. Descriptive application shell

- Start a thin Streamlit application using current profiles, display geometry, housing
  composition, source dates, FHFA history, and explicit coverage warnings.
- Keep app data access behind a small serving interface so later forecast and analogue tables can
  be added without rewriting pages.
- Do not read `gold_modeling_panel` directly from the UI.
- Show unavailable forecasts as an explained state while preserving the descriptive profile.
- Begin with tract search and map selection, community profile, housing composition, historical
  ACS/FHFA charts, source dates, uncertainty, and explicit coverage messages.
- Use clear unavailable-result placeholders until approved forecast and analogue serving tables
  exist; do not demonstrate mocked analytical claims.
- Defer the optional conversational or AI layer until the analytical application and serving
  contracts work. It may explain stored results but should not produce the underlying analysis.

### 4. Model and product decisions

- After the baseline scorecards, decide whether one gradient-boosted tree earns a focused
  comparison with the regularized linear model.
- Decide whether analytical adjacency, CBSA membership, or macroeconomic data would answer a
  demonstrated gap. None is required before the baseline checkpoint.
- Select and calibrate one uncertainty method using the reserved calibration origins.
- Publish versioned forecast, interval, explanation, analogue, and evaluation tables only after
  validation passes.
- Preserve the dedicated `neighborhood_twin_model` and `neighborhood_twin_evaluation` schemas so
  gold remains the governed analytical input layer rather than a mixture of inputs and model runs.

### 5. Serving and integration

- Build compact serving tables and a release manifest from approved outputs.
- Connect the application to the serving contract, then add forecasts, analogues, explanations,
  and guarded scenario sensitivity.
- Add application contract tests, smoke tests, accessibility review, and deployment runbooks.
- Use the Databricks App as the primary authenticated deployment; evaluate a public Streamlit
  mirror only after the serving contract is stable and an anonymous portfolio URL is required.

## Parallel ownership for two people

| Workstream | Primary responsibility | Shared boundary |
|---|---|---|
| Forecasting | Missingness/attrition review, baseline ladder, MLflow tracking, linear and selected nonlinear model, interval calibration | Owns modeling-panel filters, forecast artifacts, and model-evaluation tables |
| Similarity and app | Representation registry, current and retrospective retrieval, case review, Streamlit descriptive shell | Owns analogue outputs, match explanations, and serving-interface prototype |

Both workstreams use the published feature and split contracts without changing them privately.
One person should temporarily own shared edits to `databricks.yml` and table metadata. App work can
proceed against current profiles while model work runs; forecast and analogue pages should wait
for approved output tables rather than mock analytical claims.

## Definition of the next checkpoint

The next checkpoint is complete when:

- the baseline models run from the published split and panel tables;
- experiment runs record reproducible configurations and artifacts in MLflow;
- all forecast candidates use identical validation rows and have a subgroup scorecard;
- point metrics are interpreted together, including bias, tail error, baseline skill, and the
  majority-direction comparison rather than only the most favorable metric;
- the locked temporal tests remain untouched during model selection;
- the current-state similarity baseline has stability results and reviewed examples;
- retrospective analogue evaluation uses only information available at each query date;
- a descriptive application shell reads a documented serving interface;
- the application clearly separates observed ACS, observed FHFA history, model forecasts,
  historical analogues, and scenario sensitivity; and
- the team has an evidence-based decision on nonlinear forecasting, analytical adjacency, and any
  additional source family.

At that point, the work moves from data preparation into model selection, calibrated outputs, and
application integration rather than further general-purpose ETL expansion.

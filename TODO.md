# Project Readiness and Next Implementation Steps

This is the working handoff as of November 11, 2026. The broader design remains in the
[roadmap](ROADMAP.md) and [implementation guide](docs/implementation/README.md).

## Current answer

The approved source and feature-preparation pipeline is complete, and the first forecasting,
current-state similarity, and historical-analogue baselines now run in Databricks. The project has
reproducible public-source acquisition, bronze and silver transformations, governed geography,
current and historical gold products, point-in-time model features, fixed evaluation assignments,
a joined modeling panel, tracked experiments, validation-only forecast scorecards, reviewable
neighborhood matches, seven versioned model-evaluation figures, and retrospective analogue
evaluation. Model outputs and diagnostics now live outside gold in dedicated model and evaluation
schemas. There is no unresolved data-integrity or leakage failure blocking the next model stage.

This does not mean the whole project is complete. Forecast model selection, calibrated
uncertainty, production analogue serving, match explanations, serving tables, and the interactive
application still need to be built. Historical-analogue case review, bounded stability testing,
expanded representation selection, exact current-neighborhood retrieval, and the first scalable
retrieval benchmark are complete. New source families should not be added until a model result or
required app view shows a specific gap.

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
- The 26 Databricks jobs use numbered layer ranges (`000`, `100-104`, `200-205`, `300-302`,
  `400-401`, `500-503`, `600-603`, and `900`), grouping tags, and the maintained
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
- Job `502 Modeling | Historical Analogue Baseline` now evaluates earlier tract-year matches whose
  later outcomes were known by each query date. It published 640 matches, 224 analogue and
  comparator predictions, four retrieval summaries, and 147 sliced scorecard rows for 16 queries
  at each of the one- and three-year horizons.
- Historical retrieval is nationally broad: 95.0% to 97.5% of matches cross a state boundary.
  Weighted-standardized and PCA top-ten results overlap by only 20.8% at one year and 27.1% at
  three years, so individual case review and stability testing are required before either becomes
  the application default.
- Every analogue estimate beat zero change on the sampled queries, but none beat the state-trend
  or regularized-linear comparators. The strongest analogue MAE is 0.0839 at one year and 0.0919
  at three years, compared with state-trend MAE of 0.0758 and 0.0587. The current evidence supports
  historical analogues as interpretable context and a secondary estimate, not the primary
  forecast.
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
- Job `601 Evaluation | Historical Analogue Audit` published 6,720 variant matches, 672 complete
  query-variant stability rows, and 600 deterministic case-review rows. It reproduces job 502,
  contains no future or self matches, and retains all 21 variants for each of the 32 queries.
- Small feature-family weight changes retain 93.4% of the weighted top ten on average and are
  exactness-certified. Full family removals retain 37.6%; removing market trajectory is most
  disruptive at 16.6%, showing that it strongly controls the present match definition.
- Five- and seven-component PCA variants retain 50.9% of the six-component list on average and
  sometimes hide a large original-family gap. This made weighted standardized retrieval the
  provisional choice entering the expanded evaluation; PCA remained the comparison lens.
- Seventeen of 32 baseline query lists repeat a physical tract at multiple years. The certified
  distinct-tract variants retain 93.1% of neighbors and restore ten distinct communities, so the
  application should use a distinct-community policy.
- Job `602 Evaluation | Historical Analogue Selection` expanded the evidence to 88 one-year and
  90 three-year query tract-years. It published 3,560 matches, 1,246 predictions, four retrieval
  summaries, 322 scorecard rows, and 78 selected-versus-eligible coverage rows.
- The first live coverage review found that an otherwise balanced sample missed the under-25%
  single-family group at one year. The corrected workflow adds deterministic, outcome-blind
  supplements for missing housing, size, or ACS-uncertainty categories. The final run covers every
  eligible required category; rare categories with one case remain coverage checks, not reliable
  subgroup estimates.
- Weighted analogue MAE is lower overall than PCA at both horizons: 0.0788 versus 0.0823 at one
  year and 0.1022 versus 0.1098 at three years when comparing each representation's better
  aggregation. Regularized linear remains more accurate at 0.0682 and 0.0801.
- Weighted standardized distance and ten distinct physical communities are now the frozen
  application retrieval policy. PCA remains an internal audit lens, and analogues remain secondary
  historical context rather than the primary forecast.
- Job `503 Modeling | Current Analogue Retrieval` now applies that policy to selected 2025
  neighborhoods. Its first live run published 60 exact matches and six summaries for one Arizona,
  Michigan, and Pennsylvania tract under MLflow run
  `ff3ad7a038ce4d4180110a7a9adcbab1`.
- Every current query returned ten distinct matches, and direct SQL checks found no self-match,
  future outcome, locked temporal-test candidate, unapproved representation, or falsely calibrated
  outcome-range row. Metadata covers all 33 match columns and all 35 summary columns.
- Exact job-503 retrieval took about 14 minutes for three tracts. It is the reference result for
  evaluating a scalable index or precomputed product, not a viable on-click application query.
- Current historical-analogue coverage is narrower than profile coverage: 46,719 tracts have a
  2025 model-ready query row, compared with 83,359 current ACS similarity candidates and 84,396
  current ACS profiles. The application needs an explicit unavailable state unless a separate
  ACS-only fallback is designed and evaluated.
- Job `603 Evaluation | Scalable Analogue Retrieval` benchmarked exact retrieval and three
  random-projection LSH configurations for 29 stratified current queries at one- and three-year
  horizons. The final schema-1.1 run published 2,320 matches, 174 query-level evaluations, eight
  configuration summaries, and 19 coverage rows under MLflow run
  `3dd5aaa6c4ce47d88ef752a1d5e20f6b`.
- All configurations returned complete top-ten lists with 100% physical-community recall. A new
  tract-year-state metric exposed one narrow-LSH three-year query with 90% state recall, even
  though it retained the same ten tract identifiers. That single changed historical year shifted
  the query's median analogue outcome by 0.049 cumulative log-change units.
- The tested LSH design is rejected for serving. Its shortlists retain 88.7% to 99.9% of the full
  query-candidate cross-product and take about three to five times as long as exact retrieval in
  the same cached benchmark. The high fidelity comes from doing almost all of the original work.
- The benchmark contains no self, future-outcome, locked-test, incomplete-list, or duplicate-tract
  violation. All required region, cohort, housing-mix, community-size, and ACS-uncertainty groups
  are represented. Job 900 reapplied descriptions and comments to every new table column.

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

### 2. Similarity and historical analogues: LSH benchmark complete, serving next

- Implement weighted standardized distance and ten distinct physical communities as the frozen
  production retrieval policy. Keep PCA and tract-year matches available for development audit.
- Preserve job-602 sample coverage, subgroup counts, and later-outcome comparisons. Do not convert
  one-case rare-category checks into performance claims, and do not open the locked temporal test.
- Preserve the implemented stability, case-review, distance, geography, coverage, and
  later-outcome evidence as the baseline for future changes.
- Preserve useful ACS-based similarity for multifamily-heavy or FHFA-uncovered communities even
  when later-outcome evaluation is unavailable.
- Preserve job 503 as the exact reference implementation. Do not use its roughly 14-minute batch
  runtime as an on-click application path.
- Preserve job 603 as evidence that broad random-projection LSH buckets do not improve this
  workload. Do not approve or further tune the tested configurations without a new hypothesis
  that materially reduces the candidate-pair share.
- On the next similarity-serving branch, compare bounded exact precomputation with one genuinely
  selective index design. Use the same 29-query benchmark and require community recall,
  tract-year-state recall, rank agreement, outcome drift, runtime, storage size, and explicit
  failure behavior before approving either path.
- Quantify and expose current retrieval eligibility. Historical analogues are currently available
  for 46,719 model-ready 2025 tracts, not all 84,396 current ACS profiles.
- Decide whether unsupported tracts should show an explained unavailable state or receive a
  separately versioned ACS-only similarity fallback. Do not silently impute the missing market
  trajectory family and call it the same representation.
- Generate explanations containing shared strengths, important differences, candidate year and
  location, later outcome, coverage warnings, and the descriptive outcome range.
- Build a reviewed similarity visual package rather than relying on the early raw-versus-PCA
  diagnostic alone. The minimum final set should include:
  - a plain-language workflow diagram showing feature families, training-only preprocessing,
    weighted distance, time-safe candidate filtering, top-ten retrieval, and later outcomes;
  - a stability and representation-selection figure showing top-ten retention under bounded
    weight changes, PCA comparison, and the evidence supporting weighted matching;
  - an outcome-utility figure comparing analogue error with zero change, state trend, and the
    primary forecast at one- and three-year horizons;
  - a coverage figure showing where current historical analogues are available and where the
    application must explain an unavailable result; and
  - a polished case-study figure combining a query neighborhood, mapped historical matches,
    feature similarities and differences, and what happened to the matches afterward.
- Give every similarity figure one clear question, readable labels, restrained styling, source
  run IDs, interpretation notes, and a documented limitation. Publish a versioned manifest and
  visually inspect the complete set before selecting report or presentation figures.
- Publish compact, versioned serving tables rather than querying `gold_modeling_panel` or the
  wide audit tables from the application.

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

- one focused nonlinear forecast candidate has been compared with the regularized-linear and
  state-trend baselines on identical validation rows;
- forecast selection uses subgroup, bias, tail-error, and independent-origin evidence rather than
  only overall MAE;
- one uncertainty method has been calibrated and evaluated on the reserved calibration origins;
- a production analogue retrieval design either materially improves on job 603 or uses bounded
  exact precomputation with documented runtime, storage, refresh, and unavailable-result behavior;
- match explanations and the planned similarity visual package are published from governed model
  and evaluation outputs;
- compact, versioned forecast and analogue serving tables exist, with release lineage and no UI
  dependency on `gold_modeling_panel`;
- a descriptive application shell reads the documented serving interface and handles unsupported
  tracts honestly;
- the locked temporal tests remain untouched during model selection;
- the application clearly separates observed ACS, observed FHFA history, model forecasts,
  historical analogues, and scenario sensitivity; and
- the team has an evidence-based decision on nonlinear forecasting, analytical adjacency, and any
  additional source family.

At that point, the work moves from data preparation into model selection, calibrated outputs, and
application integration rather than further general-purpose ETL expansion.

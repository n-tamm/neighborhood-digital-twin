# Databricks Pipeline Run Order

This is the canonical operating sequence for the project's Databricks jobs. Update this document
in the same change that adds a job, changes a dependency, or changes which tables a job
overwrites. The implementation guides explain how each stage works; this page answers the
operational question: **what should run, in what order, and when should it not run?**

## How jobs are organized in Databricks

Every bundle job has a sortable display name and four tags:

- `project=neighborhood-digital-twin` keeps the project jobs filterable;
- `pipeline_group` is `setup`, `bronze`, `silver`, `gold`, `analysis`, `modeling`, `evaluation`,
  `serving`, or `metadata`;
- `run_order` matches the number in the display name; and
- `lifecycle` distinguishes one-time, refresh, optional, downstream, and diagnostic jobs.

The display names sort as `000 Setup`, `100-104 Bronze`, `200-205 Silver`, `300-302 Gold`,
`400-401 Analysis`, `500-503 Modeling`, `600-604 Evaluation`, `700 Serving`, and `900 Metadata`.
Jobs increment
by one inside each three-digit layer range,
leaving room to add later jobs without renumbering another layer. These numbers communicate
dependency order; they do not create an automatic dependency between separate jobs. The reserved
ranges are `000-099` for setup and operations, `100-199` for bronze, `200-299` for silver,
`300-399` for gold, `400-499` for analysis, `500-599` for modeling, `600-699` for evaluation,
`700-799` for serving, and `900-999` for metadata.
The bundle job keys remain stable even if a display label is clarified later.

## Job inventory

| Order | Group | Bundle job key | Run when | Main prerequisite or caution |
|---:|---|---|---|---|
| 000 | Setup | `organize_project_schemas` | Once for a new or legacy workspace | Safe to rerun, but not part of routine refreshes |
| 100 | Bronze | `core_source_ingestion` | Initial setup or a reviewed core-source refresh | Ingests FHFA, core Census files, and the pilot ACS release, then profiles bronze |
| 101 | Bronze | `historical_acs_ingestion` | Optional bounded ACS batch | Uses configured years, states, and request limit; not a routine prerequisite now |
| 102 | Bronze | `pilot_annual_acs_ingestion` | Initial pilot reconstruction only | The national panel is already complete |
| 103 | Bronze | `national_current_acs_ingestion` | A reviewed current ACS release expansion | Confirm the configured release before running |
| 104 | Bronze | `national_historical_acs_backfill` | One-time national history or explicit repair | Long-running; internally profiles bronze, rebuilds silver and current gold, and applies metadata |
| 200 | Silver | `silver_source_transforms` | After accepted FHFA or ACS bronze changes | Rebuilds the source-specific silver tables and validation metrics |
| 201 | Silver | `geography_relationship_pipeline` | Initial build or relationship-source change | Requires the registered 2010-to-2020 relationship snapshot |
| 202 | Silver | `display_geometry_pipeline` | Initial build or display-geometry change | Display geometry is not approved for spatial analysis |
| 203 | Silver | `connecticut_geography_pipeline` | Initial build or Connecticut reference change | Maintains the reviewed planning-region bridge |
| 204 | Silver | `canonical_geography_pipeline` | After 201 and 202 | Builds the canonical tract dimension and attaches optional display geometry |
| 205 | Silver | `geography_hierarchy_pipeline` | After 204 | Builds country-to-tract hierarchy dimensions |
| 300 | Gold | `gold_current_products` | After relevant silver or geography changes | Rebuilds current profiles and application/model candidate cohorts |
| 301 | Gold | `gold_historical_products` | After relevant silver, tract-alignment, or hierarchy changes | Rebuilds aligned historical state and direct horizon targets |
| 302 | Gold | `gold_model_readiness` | After 301 or a feature/split-contract change | Rebuilds point-in-time features, frozen splits, panel, and readiness summaries |
| 400 | Analysis | `data_readiness_eda` | After relevant silver or current-gold changes | Publishes governed coverage and feasibility summaries |
| 401 | Analysis | `visual_eda` | After 400 or visual-analysis code changes | Rebuilds visual summaries and versioned EDA figures |
| 500 | Modeling | `forecast_baselines` | After 302 or forecast-development code changes | Publishes validation-only baseline predictions and scorecards; does not open locked tests |
| 501 | Modeling | `similarity_baselines` | After 300 or similarity-development code changes | Publishes a small reviewable current-state baseline, not the final retrospective analogue product |
| 502 | Modeling | `historical_analogue_baseline` | After current successful runs of 302 and 500 | Retrieves time-safe historical matches for sampled validation queries and compares their later outcomes with forecast baselines |
| 503 | Modeling | `current_analogue_retrieval` | After a current successful run of 302, using the representation contract already selected by 602 | Applies the frozen weighted representation to selected latest-year neighborhoods without opening locked temporal-test outcomes |
| 600 | Evaluation | `model_evaluation_figures` | After current successful runs of 500 and 501 | Renders seven versioned model-diagnostic figures and publishes their run-linked manifest |
| 601 | Evaluation | `historical_analogue_audit` | After a current successful run of 502 | Reproduces the published baselines, builds deterministic review cases, and measures stability under bounded retrieval variants |
| 602 | Evaluation | `historical_analogue_selection` | After successful runs of 500 and 601 | Expands validation coverage, requires distinct physical candidates, and compares the provisional weighted representation with PCA before the application policy is frozen |
| 603 | Evaluation | `scalable_analogue_retrieval` | After the weighted representation is frozen and job 503 establishes an exact current-query reference | Compares deterministic LSH shortlists with exhaustive exact top-ten matches on a stratified current-query benchmark |
| 604 | Evaluation | `analogue_tree_retrieval` | After job 603 and from the same model-readiness build | Requires an exact KD-tree to reproduce the exhaustive benchmark, then measures indexed work on 1,000 and all eligible current queries |
| 700 | Serving | `analogue_serving_products` | After a successful current job 604 or when approved current analogues need refreshing | Publishes national exact matches, descriptive summaries, explicit availability, and an activation manifest; it does not train or select the method |
| 900 | Metadata | `table_metadata_pipeline` | Last, after any schema-overwriting job | Reapplies table descriptions, grains, and column comments |

## Dependency outline

```text
000 Setup
   |
   +--> 100-104 Bronze acquisition and backfill paths
              |
              v
          200 Silver source tables ------------------------+
                                                            |
100 Core Census sources --> 201 Relationship --+              |
                        --> 202 Display geometry +--> 204 Canonical --> 205 Hierarchy
                        --> 203 Connecticut -----+              |
                                                            |
200 Silver + 203-205 Geography ------------------> 300 Current gold
200 Silver + 201/203/205 Geography -------------> 301 Historical gold
301 Historical gold ----------------------------> 302 Model readiness
200/300 Gold -----------------------------------> 400 Readiness EDA --> 401 Visual EDA
302 Model readiness ----------------------------> 500 Forecast baselines
300 Current gold -------------------------------> 501 Similarity baselines
302 Model readiness + 500 Forecast -------------> 502 Historical analogue baseline
500 Forecast + 501 Similarity ------------------> 600 Model evaluation figures
502 Historical analogue baseline --------------> 601 Analogue review and stability
500 Forecast + 601 Analogue audit --------------> 602 Expanded analogue selection
302 Model readiness ----------------------------> 503 Current analogue retrieval
503 Exact current retrieval contract -----------> 603 Scalable retrieval benchmark
603 Frozen exhaustive reference ----------------> 604 Exact tree retrieval benchmark
604 Approved exact retrieval policy ------------> 700 National analogue serving release

All schema-overwriting paths -------------------> 900 Metadata
```

The three geography jobs numbered 201-203 are independent of one another once their source
snapshots exist. Jobs 204 and 205 are ordered because the hierarchy uses the canonical tract
dimension. Gold jobs should wait until both their source tables and relevant geography products
are current.

## Before every run

From the repository root and the intended Git commit:

```powershell
databricks bundle validate --profile neighborhood-twin -t team
databricks bundle deploy --profile neighborhood-twin -t team
```

Deployment updates job definitions and code but does not run the pipeline. In a shared workspace,
one teammate should own a deployment window so two branches do not replace the same bundle jobs.
Record the Git commit and run owner for a full source refresh.

## Current normal workflow

The national 2010-2024 ACS backfill is already complete. Do **not** begin an ordinary development
session with jobs 100-104. Start at the first stage whose code or input changed and continue only
through its downstream consumers.

### Model-readiness code or split change

```powershell
databricks bundle run gold_model_readiness --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

### Historical gold logic change

```powershell
databricks bundle run gold_historical_products --profile neighborhood-twin -t team
databricks bundle run gold_model_readiness --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

Run jobs 400 and 401 afterward only when the change affects an EDA input, documented finding, or
figure. A documentation-only change requires no Databricks job.

### Modeling development change

The two initial workflows are independent after their upstream tables exist, so teammates may
run them in parallel during an agreed deployment window:

```powershell
databricks bundle run forecast_baselines --profile neighborhood-twin -t team
databricks bundle run similarity_baselines --profile neighborhood-twin -t team
databricks bundle run historical_analogue_baseline --profile neighborhood-twin -t team
databricks bundle run current_analogue_retrieval --profile neighborhood-twin -t team
databricks bundle run model_evaluation_figures --profile neighborhood-twin -t team
databricks bundle run historical_analogue_audit --profile neighborhood-twin -t team
databricks bundle run historical_analogue_selection --profile neighborhood-twin -t team
databricks bundle run scalable_analogue_retrieval --profile neighborhood-twin -t team
databricks bundle run analogue_tree_retrieval --profile neighborhood-twin -t team
databricks bundle run analogue_serving_products --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

Job 500 may read training and validation assignments but publishes validation predictions only.
It must not be changed to inspect the locked temporal tests during model development. Job 501 is
a current-state representation check. Job 502 uses validation queries only, requires every
candidate outcome to end by the query origin, and compares analogue estimates with selected
job-500 forecasts on the same deterministic query set. Its first contract supports one- and
three-year horizons. The five-year validation origin does not have enough earlier model-ready
history for a leakage-safe candidate outcome.
Job 600 reads the governed evaluation summaries, writes versioned PNGs to the evaluation volume,
and records both source MLflow run IDs in its manifest.
Job 601 must follow job 502. It first requires the rerun weighted-standardized and PCA baselines to
reproduce the published candidate identities, years, ranks, and distances. It then evaluates 21
declared variants on the same validation queries. The exact baselines and certifiable bounded
rerankings are distinguished from shortlist-based stress tests in every row; the job does not use
the locked temporal tests or select the application representation automatically.
Job 602 follows the audit evidence but does not overwrite jobs 502 or 601. It expands the
deterministic validation sample from one to five queries per available origin, Census region, and
geographic-role stratum, then adds an outcome-blind supplement for any missing housing-mix,
community-size, or ACS-uncertainty category. It requires ten distinct candidate tracts and compares
weighted and PCA retrieval on identical queries. Its coverage table compares the selected sample
with all eligible validation queries across time, geography, cohort, housing mix, community size,
and ACS uncertainty. The locked temporal tests remain unavailable to this workflow.
Job 503 applies the representation and distinct-community policy selected by job 602 to a small,
configurable set of neighborhoods at the latest model-ready year. It fits imputation and scaling
on point-model training rows, returns exact weighted-standardized matches, and excludes every
locked temporal-test candidate. Its historical outcome range is descriptive context, not the
primary forecast or a calibrated interval. The default bundle parameters retrieve one tract from
each configured application-demo state; `query_geoids` can target specific model-ready tracts.
Job 603 expands the current-query sample by Census region and modeling cohort, supplements any
missing housing-composition, community-size, or ACS-uncertainty group, and treats exhaustive
weighted top-ten retrieval as the reference. It evaluates three deterministic random-projection
LSH configurations that generate candidate shortlists before applying the same exact distance and
distinct-tract reranking. The benchmark records top-ten recall, Jaccard overlap, top-three
retention, tract-year-state recall, rank displacement, historical-outcome drift, shortlist size,
runtime, and sample coverage. It does not authorize a serving method automatically and does not
access locked temporal-test candidate outcomes. The November 11 run rejected all three LSH
configurations because they retained 88.7% to 99.9% of possible pairs and were slower than the
exact reference. Rerun 603 when the representation, candidate pool, benchmark contract, or a new
candidate-generation method changes; do not treat it as an application-serving refresh.
Job 604 tests whether an exact scikit-learn KD-tree can retain that reference's identities, years,
ranks, distances, and outcome summaries while avoiding the exhaustive Spark cross join. It first
checks the same 29 job-603 queries, then measures direct indexed retrieval for a deterministic
1,000-query sample and every eligible current query. The index operates on tract-year states and
expands its request until the top ten distinct physical tracts and any boundary tie are resolved.
The workflow fails on any fidelity loss, same-tract result, future outcome, locked-test access, or
incomplete top ten. Job 604 is evaluation evidence, not the national application serving table;
rerun it after job 603 or when its tree configuration or retrieval implementation changes.
The November 12 run reproduced all 58 query-horizon references exactly and directly queried all
46,719 eligible current tracts in about 193 seconds at one year and 133 seconds at three years.
It used about 9.5% to 9.8% of an exhaustive distance pass, so the exact tree is the approved engine
for the batch serving-table build. Job 604 remains evaluation evidence rather than an application
refresh; job 700 applies its approved policy nationally.

Job 700 rebuilds the training-only feature preprocessing for each approved horizon, constructs the
exact KD-tree, and retrieves ten distinct historical tracts for every eligible current tract. It
publishes append-only release partitions in `neighborhood_twin_serving`: match-level evidence, a
query-level descriptive summary, and an availability row for every current profile and horizon.
The job validates lineage, complete top tens, uniqueness, time safety, locked-test exclusion,
summary reconciliation, and coverage before writing. It writes the release manifest last. Only a
release with three `validated` manifest rows is approved for application use; data rows from a
failed attempt without a manifest remain inactive and can be cleaned up later by exact release ID.
Job 700 does not use MLflow because it applies an already evaluated and frozen retrieval policy
rather than comparing models.
The first live release on November 12 published 934,380 matches, 93,438 query summaries, and
171,056 availability rows. It covered 46,719 eligible tracts at both horizons and activated the
release only after all counts and safety checks reconciled.

### Find the MLflow experiments

The modeling notebooks create their shared experiment folders idempotently. In the Databricks
left navigation, open **Workspace**, then **Shared**, then `neighborhood-digital-twin`. The current
experiments are:

- `/Shared/neighborhood-digital-twin/forecast-baselines` (experiment ID `3001817840578297`);
- `/Shared/neighborhood-digital-twin/similarity-baselines` (experiment ID `3001817840578298`);
- `/Shared/neighborhood-digital-twin/historical-analogues` (created by the first job-502 run).
- `/Shared/neighborhood-digital-twin/analogue-audit-stability` (created by the first job-601 run).
- `/Shared/neighborhood-digital-twin/analogue-selection` (created by the first job-602 run).
- `/Shared/neighborhood-digital-twin/current-analogue-retrieval` (created by the first job-503 run).
- `/Shared/neighborhood-digital-twin/scalable-analogue-retrieval` (created by the first job-603 run).
- `/Shared/neighborhood-digital-twin/analogue-tree-retrieval` (created by the first job-604 run).

They can also be found from **Machine Learning** or **Experiments** by searching for
`forecast-baselines` or `similarity-baselines`. A Databricks modeling job run also links to its
corresponding MLflow run. The evaluation manifest records the exact forecast and similarity run
IDs used by each figure build, so figures should not be associated with experiments by date alone.

## Source refresh paths

### New or corrected ACS snapshots

1. Confirm the requested release, states, expected request count, API terms, and whether the
   snapshots already exist.
2. Run job 103 for a new national current release, or job 101 for a deliberately bounded repair.
3. Run 200 to rebuild silver source tables.
4. Run 203-205 only if tract identifiers, the Connecticut reference, or canonical geography changed.
5. Run 300, 301, and 302 in order.
6. Run 400 and 401 when analytical summaries or figures need refreshing.
7. Run 500 and 501 when the source change should be reflected in model-development outputs.
8. Run 502 after 500 when the historical analogue evaluation should be refreshed.
9. Run 503 when current-neighborhood analogue outputs should reflect the refreshed inputs.
10. Run 600 when reviewed evaluation figures should reflect the forecast and current-state
   similarity runs.
11. Run 601 after 502 when case-review or stability evidence should reflect the updated analogue
    run.
12. Run 602 after 601 when the expanded representation-selection evidence should be refreshed.
13. Run 603 when scalable-retrieval evidence should reflect the refreshed analogue inputs.
14. Run 604 after 603 when exact indexed-retrieval evidence should be refreshed.
15. Run 700 after 604 when the application release should reflect the refreshed inputs.
16. Finish with 900.

### New FHFA release

1. Run 100 only after confirming the core acquisition job points to the intended publisher file.
2. Run 200, then 300, 301, and 302.
3. Refresh 400 and 401 if the added year changes coverage or reported figures.
4. Refresh 500 and 501 after the upstream contracts pass.
5. Refresh 502 after 500 when analogue results should reflect the new FHFA history.
6. Refresh 503 when current-neighborhood analogue outputs should reflect the new inputs.
7. Refresh 601 after 502 when the analogue audit should reflect the new baseline run.
8. Refresh 602 after 601 when representation-selection evidence should reflect the new inputs.
9. Refresh 603 when scalable-retrieval evidence should reflect the new inputs.
10. Refresh 604 after 603 when exact indexed-retrieval evidence should reflect the new inputs.
11. Refresh 700 after 604 to publish the new approved application release.
12. Finish with 900.

### Geography-source change

Run only the affected jobs among 201-203, then run 204 and 205 when their inputs changed. Follow
with 300, 301, 302, the affected analysis and modeling jobs, and 900. Do not use simplified display geometry
from job 202 for adjacency, distance, or other analytical spatial work.

## One-time national backfill and failure recovery

Job 104 is not part of a routine refresh. It iterates over the configured national historical ACS
releases and can run for well over an hour. It then profiles the completed bronze data, rebuilds
silver source tables, rebuilds current gold products, and applies metadata. It does not build the
tract geography jobs, historical gold products, model-readiness products, or EDA products.

For a genuinely empty workspace, establish the source and geography foundation first: 000, 100,
101-103 as required by the configured coverage plan, 200, 201-203, 204, and 205. Then run 104 for
the reviewed national historical gap, followed by 301, 302, 400, 401, and 900. Verify coverage at
every layer rather than treating completion status alone as evidence of a correct load.

If the ingestion task inside job 104 succeeds but a later task fails, do not restart the entire
ingestion. Prefer a Databricks repair run beginning at the failed task. The independent recovery
equivalents are:

- failed silver rebuild: run 200;
- failed current-gold rebuild: run 300;
- failed exact tree retrieval: correct and rerun 604 without rerunning unchanged job 603;
- failed analogue serving release: correct and rerun 700 without rerunning unchanged job 604;
  a partial release is inactive unless its manifest was written;
- failed metadata application: run 900;
- historical products not yet built: continue with 301, then 302.

## Completion gates

Do not continue merely because a job is green. Before advancing:

- Bronze: expected immutable snapshots, checksums, manifests, and source coverage are present.
- Silver: key, type, range, source-reconciliation, and geography checks have no hard failures.
- Geography: relationship coverage, Connecticut exceptions, canonical counts, and hierarchy
  reconciliation match their documented contracts.
- Gold: row counts reconcile to inputs; censoring, cohort, and availability rules remain explicit.
- Model readiness: no future ACS use, target-timing error, duplicate key, split mismatch, or
  geographic-holdout failure exists.
- Analysis: figures and manifests point to the current analytical build.
- Modeling: MLflow records the input contract and parameters; forecast outputs contain only
  validation roles; current-state similarity outputs exclude self-matches; historical analogues
  use validation queries, exclude the query tract, obey the outcome-known-by-query cutoff, and
  reconcile every query to the declared top-k count.
- Evaluation: every expected figure exists, exceeds the publication size guard, links to current
  source run IDs, and has been visually reviewed for readable labels and valid interpretation.
  Historical analogue audit baselines must reproduce job 502, every variant must cover the same
  query set with top-k results, future and self matches must remain absent, and every result must
  state whether retrieval exactness was certified or only shortlist-based.
  Expanded analogue selection must fill every available deterministic sampling stratum, compare
  both representations on identical validation queries, retain ten distinct candidate tracts,
  and publish selected-versus-eligible coverage without accessing locked temporal tests.
  Current analogue retrieval must use the frozen weighted representation, return complete top-k
  lists of distinct physical tracts, keep candidate outcomes time-safe, exclude locked temporal
  tests, and label the outcome range as descriptive rather than calibrated.
  Scalable analogue evaluation must retain complete exact references, represent every declared
  query and LSH configuration even when no approximate match is returned, keep fidelity metrics
  within valid ranges, cover every required query category, and preserve all timing and locked-test
  safeguards before an approximate method can be considered for serving.
  Exact tree retrieval must reproduce every job-603 benchmark community and tract-year state in
  the same rank with zero outcome drift, complete ten distinct non-self matches for every query,
  preserve time and locked-test safeguards, and directly measure the 29-query, 1,000-query, and
  full-current populations before it can be selected for serving.
- Serving: use one approved tree run and model-readiness build, publish one availability row per
  current tract and supported horizon, reconcile every available key to one summary and ten
  distinct matches, and activate the release manifest only after every check passes.
- Metadata: table descriptions and comments are visible after the final overwrite.

## Maintenance rule

Any new Databricks job must receive a unique order number, group, lifecycle tag, prerequisites,
refresh guidance, and completion gate here. If a job begins overwriting a new downstream table,
update the source-refresh paths in the same pull request. Keep one-time migrations and backfills
visibly separate from normal refresh jobs.

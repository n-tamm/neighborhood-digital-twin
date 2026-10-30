# Databricks Pipeline Run Order

This is the canonical operating sequence for the project's Databricks jobs. Update this document
in the same change that adds a job, changes a dependency, or changes which tables a job
overwrites. The implementation guides explain how each stage works; this page answers the
operational question: **what should run, in what order, and when should it not run?**

## How jobs are organized in Databricks

Every bundle job has a sortable display name and four tags:

- `project=neighborhood-digital-twin` keeps the project jobs filterable;
- `pipeline_group` is `setup`, `bronze`, `silver`, `gold`, `analysis`, `modeling`, or `metadata`;
- `run_order` matches the number in the display name; and
- `lifecycle` distinguishes one-time, refresh, optional, downstream, and diagnostic jobs.

The display names sort as `000 Setup`, `100-104 Bronze`, `200-205 Silver`, `300-302 Gold`,
`400-401 Analysis`, `500-501 Modeling`, and `900 Metadata`. Jobs increment by one inside each
three-digit layer range,
leaving room to add later jobs without renumbering another layer. These numbers communicate
dependency order; they do not create an automatic dependency between separate jobs. The reserved
ranges are `000-099` for setup and operations, `100-199` for bronze, `200-299` for silver,
`300-399` for gold, `400-499` for analysis, `500-599` for modeling, and `900-999` for metadata.
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
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

Job 500 may read training and validation assignments but publishes validation predictions only.
It must not be changed to inspect the locked temporal tests during model development. Job 501 is
a current-state representation check; historical analogue evaluation will be a later numbered
workflow once its time-safe retrieval contract is implemented.

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
8. Finish with 900.

### New FHFA release

1. Run 100 only after confirming the core acquisition job points to the intended publisher file.
2. Run 200, then 300, 301, and 302.
3. Refresh 400 and 401 if the added year changes coverage or reported figures.
4. Refresh 500 and 501 after the upstream contracts pass.
5. Finish with 900.

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
  validation roles; similarity outputs exclude self-matches and reconcile to the query count.
- Metadata: table descriptions and comments are visible after the final overwrite.

## Maintenance rule

Any new Databricks job must receive a unique order number, group, lifecycle tag, prerequisites,
refresh guidance, and completion gate here. If a job begins overwriting a new downstream table,
update the source-refresh paths in the same pull request. Keep one-time migrations and backfills
visibly separate from normal refresh jobs.

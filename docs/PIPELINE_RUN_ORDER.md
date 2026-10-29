# Databricks Pipeline Run Order

This is the canonical operating sequence for the project's Databricks jobs. Update this document
in the same change that adds a job, changes a dependency, or changes which tables a job
overwrites. The implementation guides explain how each stage works; this page answers the
operational question: **what should run, in what order, and when should it not run?**

## How jobs are organized in Databricks

Every bundle job has a sortable display name and four tags:

- `project=neighborhood-digital-twin` keeps the project jobs filterable;
- `pipeline_group` is `setup`, `bronze`, `silver`, `gold`, `analysis`, or `metadata`;
- `run_order` matches the number in the display name; and
- `lifecycle` distinguishes one-time, refresh, optional, downstream, and diagnostic jobs.

The display names sort as `00 Setup`, `10-14 Bronze`, `20-25 Silver`, `30-32 Gold`, `40-41
Analysis`, and `90 Metadata`. These numbers communicate dependency order; they do not create an
automatic dependency between separate jobs. The bundle job keys used by CLI commands remain
stable even if a display label is clarified later.

## Job inventory

| Order | Group | Bundle job key | Run when | Main prerequisite or caution |
|---:|---|---|---|---|
| 00 | Setup | `organize_project_schemas` | Once for a new or legacy workspace | Safe to rerun, but not part of routine refreshes |
| 10 | Bronze | `core_source_ingestion` | Initial setup or a reviewed core-source refresh | Ingests FHFA, core Census files, and the pilot ACS release, then profiles bronze |
| 11 | Bronze | `historical_acs_ingestion` | Optional bounded ACS batch | Uses configured years, states, and request limit; not a routine prerequisite now |
| 12 | Bronze | `pilot_annual_acs_ingestion` | Initial pilot reconstruction only | The national panel is already complete |
| 13 | Bronze | `national_current_acs_ingestion` | A reviewed current ACS release expansion | Confirm the configured release before running |
| 14 | Bronze | `national_historical_acs_backfill` | One-time national history or explicit repair | Long-running; internally profiles bronze, rebuilds silver and current gold, and applies metadata |
| 20 | Silver | `silver_source_transforms` | After accepted FHFA or ACS bronze changes | Rebuilds the source-specific silver tables and validation metrics |
| 21 | Silver | `geography_relationship_pipeline` | Initial build or relationship-source change | Requires the registered 2010-to-2020 relationship snapshot |
| 22 | Silver | `display_geometry_pipeline` | Initial build or display-geometry change | Display geometry is not approved for spatial analysis |
| 23 | Silver | `connecticut_geography_pipeline` | Initial build or Connecticut reference change | Maintains the reviewed planning-region bridge |
| 24 | Silver | `canonical_geography_pipeline` | After 21 and 22 | Builds the canonical tract dimension and attaches optional display geometry |
| 25 | Silver | `geography_hierarchy_pipeline` | After 24 | Builds country-to-tract hierarchy dimensions |
| 30 | Gold | `gold_current_products` | After relevant silver or geography changes | Rebuilds current profiles and application/model candidate cohorts |
| 31 | Gold | `gold_historical_products` | After relevant silver, tract-alignment, or hierarchy changes | Rebuilds aligned historical state and direct horizon targets |
| 32 | Gold | `gold_model_readiness` | After 31 or a feature/split-contract change | Rebuilds point-in-time features, frozen splits, panel, and readiness summaries |
| 40 | Analysis | `data_readiness_eda` | After relevant silver or current-gold changes | Publishes governed coverage and feasibility summaries |
| 41 | Analysis | `visual_eda` | After 40 or visual-analysis code changes | Rebuilds visual summaries and versioned EDA figures |
| 90 | Metadata | `table_metadata_pipeline` | Last, after any schema-overwriting job | Reapplies table descriptions, grains, and column comments |

## Dependency outline

```text
00 Setup
   |
   +--> 10-14 Bronze acquisition and backfill paths
              |
              v
          20 Silver source tables -------------------------+
                                                            |
10 Core Census sources --> 21 Relationship --+              |
                       --> 22 Display geometry +--> 24 Canonical --> 25 Hierarchy
                       --> 23 Connecticut -----+              |
                                                            |
20 Silver + 23-25 Geography ---------------------> 30 Current gold
20 Silver + 21/23/25 Geography -----------------> 31 Historical gold
31 Historical gold -----------------------------> 32 Model readiness
20/30 Gold -------------------------------------> 40 Readiness EDA --> 41 Visual EDA

All schema-overwriting paths -------------------> 90 Metadata
```

The three geography jobs numbered 21-23 are independent of one another once their source
snapshots exist. Jobs 24 and 25 are ordered because the hierarchy uses the canonical tract
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
session with jobs 10-14. Start at the first stage whose code or input changed and continue only
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

Run jobs 40 and 41 afterward only when the change affects an EDA input, documented finding, or
figure. A documentation-only change requires no Databricks job.

## Source refresh paths

### New or corrected ACS snapshots

1. Confirm the requested release, states, expected request count, API terms, and whether the
   snapshots already exist.
2. Run job 13 for a new national current release, or job 11 for a deliberately bounded repair.
3. Run 20 to rebuild silver source tables.
4. Run 23-25 only if tract identifiers, the Connecticut reference, or canonical geography changed.
5. Run 30, 31, and 32 in order.
6. Run 40 and 41 when analytical summaries or figures need refreshing.
7. Finish with 90.

### New FHFA release

1. Run 10 only after confirming the core acquisition job points to the intended publisher file.
2. Run 20, then 30, 31, and 32.
3. Refresh 40 and 41 if the added year changes coverage or reported figures.
4. Finish with 90.

### Geography-source change

Run only the affected jobs among 21-23, then run 24 and 25 when their inputs changed. Follow with
30, 31, 32, the affected analysis jobs, and 90. Do not use simplified display geometry from job 22
for adjacency, distance, or other analytical spatial work.

## One-time national backfill and failure recovery

Job 14 is not part of a routine refresh. It iterates over the configured national historical ACS
releases and can run for well over an hour. It then profiles the completed bronze data, rebuilds
silver source tables, rebuilds current gold products, and applies metadata. It does not build the
tract geography jobs, historical gold products, model-readiness products, or EDA products.

For a genuinely empty workspace, establish the source and geography foundation first: 00, 10,
11-13 as required by the configured coverage plan, 20, 21-23, 24, and 25. Then run 14 for the
reviewed national historical gap, followed by 31, 32, 40, 41, and 90. Verify coverage at every
layer rather than treating completion status alone as evidence of a correct load.

If the ingestion task inside job 14 succeeds but a later task fails, do not restart the entire
ingestion. Prefer a Databricks repair run beginning at the failed task. The independent recovery
equivalents are:

- failed silver rebuild: run 20;
- failed current-gold rebuild: run 30;
- failed metadata application: run 90;
- historical products not yet built: continue with 31, then 32.

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
- Metadata: table descriptions and comments are visible after the final overwrite.

## Maintenance rule

Any new Databricks job must receive a unique order number, group, lifecycle tag, prerequisites,
refresh guidance, and completion gate here. If a job begins overwriting a new downstream table,
update the source-refresh paths in the same pull request. Keep one-time migrations and backfills
visibly separate from normal refresh jobs.

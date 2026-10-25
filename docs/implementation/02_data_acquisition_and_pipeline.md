# 02 — Data Acquisition and Pipeline

## Purpose

This stage turns approved public sources into repeatable, versioned data assets. The main requirement is not a large download script; it is a traceable path from an external file or API response to a validated table that another contributor can rebuild.

## Current implementation

The first working slice is now in place:

- `src/neighborhood_twin/data/catalog.py` defines the reviewed FHFA, tract-boundary, and tract-relationship endpoints;
- `acquisition.py` downloads or registers uploaded files, checks response size, calculates SHA-256, redacts query secrets, and writes an immutable raw snapshot plus JSON sidecar;
- `acs.py` builds the focused state-level ACS request and keeps each estimate paired with its margin of error;
- `databricks.py` creates the project schema and volume, publishes the manifest table, and validates FHFA and ACS bronze Delta tables;
- `notebooks/01_feasibility/01_ingest_core_sources.py` is the thin Databricks entry point;
- `transform.py` selects the latest accepted source snapshots and prepares validated FHFA,
  normalized ACS, ACS dictionary, and wide ACS convenience tables;
- `notebooks/03_transformation/01_build_silver_source_tables.py` is the independent silver
  job entry point;
- unit tests cover request limits, GEOID construction, key redaction, hashing, immutable
  placement, the manual-upload fallback, and the ACS silver missing-value policy.

The acquisition job remains source-shaped bronze. The separate silver job now translates ACS
missing values, assigns readable measure definitions and universes, and calculates documented
housing shares. The normalized table is the main analytical interface; the wide table is kept
for convenient tract profiles and explicit derived ratios. Neither job harmonizes older tract
vintages or creates a modeling table; those responsibilities remain in the geography and feature
stages.

## Databricks storage contract

Databricks is the canonical team environment for source data and ETL. Use an existing Unity Catalog
catalog with schemas separated by pipeline responsibility:

| Object | Initial name | Purpose |
|---|---|---|
| Catalog | chosen from the shared workspace | Existing governance boundary; the notebook does not create a catalog |
| Bronze schema | `neighborhood_twin_bronze` | Source-shaped tables, manifest, and raw-snapshot volume |
| Silver schema | `neighborhood_twin_silver` | Cleaned, typed, and geographically conformed tables |
| Gold schema | `neighborhood_twin_gold` | Analysis, modeling, and application-ready products |
| Quality schema | `neighborhood_twin_quality` | Append-only checks and pipeline-observability results |
| Test schema | `neighborhood_twin_test` | Reserved; create only when integration tests need persisted fixtures or results |
| Managed volume | `source_snapshots` | Immutable raw source payloads and sidecar manifests |
| Manifest table | `source_snapshot_manifest` | Searchable source version, checksum, request, license, and validation history |
| FHFA bronze table | `bronze_fhfa_tract_hpi` | Source-shaped tract-year HPI records plus snapshot lineage |
| ACS bronze table | `bronze_acs5_tract` | Source variable codes plus ACS release window and snapshot lineage |
| Quality table | `bronze_quality_metrics` | Append-only profiling results by run, source, metric, and optional dimension |
| FHFA silver table | `silver_fhfa_tract_year` | Current standardized FHFA tract-year records with availability flags and lineage |
| ACS measure table | `silver_acs_tract_measure` | Primary normalized ACS table with one tract-release-measure row, uncertainty, definitions, and lineage |
| ACS dictionary | `silver_acs_measure_dictionary` | One governed definition per selected ACS measure, including source codes, universe, unit, and official metadata link |
| ACS wide table | `silver_acs_tract_year` | Generated tract-release convenience table with readable fields and housing ratios |
| Silver quality table | `silver_quality_metrics` | Append-only validation and coverage metrics for each attempted silver build |

Raw file paths follow:

```text
/Volumes/<catalog>/neighborhood_twin_bronze/source_snapshots/
  bronze/<source_id>/retrieval_date=<YYYY-MM-DD>/<sha-prefix>/<source-file>
```

Managed volumes are for raw files. Delta tables are for queryable records. Do not duplicate this design with legacy DBFS mounts, local OneDrive folders, or raw files committed to Git.

The idempotent `organize_project_schemas` job creates the four active schemas and copies a legacy
table only when its new destination does not exist. It does not overwrite organized tables, move
recorded source paths, or delete `neighborhood_twin_dev`. Run it once before using the refactored
jobs; then run `table_metadata_pipeline` so copied tables receive their table and column comments.

## Team setup before the first run

1. Create or choose one Databricks Free Edition workspace and add both team members.
2. Confirm the Unity Catalog catalog both people can use. The notebook defaults to `workspace`, but the real catalog name must be checked in Catalog Explorer.
3. Request a free Census API key. The current API rejects the tract requests without one.
4. Create a Databricks-backed secret scope named `neighborhood-twin` and save the key as `census-api-key`. The widget names can be changed if the workspace uses different names.
5. Install the Databricks CLI and authenticate the local development machine with an OAuth profile. The examples below use the profile name `neighborhood-twin`.
6. Open the local Git checkout in VS Code and select the same profile in the Databricks extension. A Databricks Git-folder clone is not required for this workflow.
7. Validate and deploy the bundle from the repository root:

   ```powershell
   databricks bundle validate --profile neighborhood-twin
   databricks bundle deploy --profile neighborhood-twin
   ```

   For a workspace that already contains the earlier shared schema, run the one-time organizer and
   metadata jobs before normal refreshes:

   ```powershell
   databricks bundle run organize_project_schemas --profile neighborhood-twin
   databricks bundle run table_metadata_pipeline --profile neighborhood-twin
   ```

8. Run the deployed ingestion job:

   ```powershell
   databricks bundle run core_source_ingestion --profile neighborhood-twin
   ```

   After the bronze job passes, run the independent silver transformation job:

   ```powershell
   databricks bundle run silver_source_transforms --profile neighborhood-twin
   ```

   Historical ACS is intentionally separate. Run a reviewed batch only after confirming its
   configured years, states, and request count:

   ```powershell
   databricks bundle run historical_acs_ingestion --profile neighborhood-twin
   databricks bundle run silver_source_transforms --profile neighborhood-twin
   ```

9. In Databricks, confirm that the job appears under **Jobs & Pipelines** and that Catalog Explorer contains the expected schema, volume, manifest, and bronze tables.
10. Record the catalog, schema, pilot states, ACS release, Git commit, and run owner in the team notes.

The root `databricks.yml` is the source-controlled definition of the initial serverless job. The target is named `team` because the job and its outputs belong to the project rather than to a separate local data environment. One person should own bundle deployment during the initial pilot to avoid competing updates to the same job. Both people can develop through Git branches, and the job can be shared with the second teammate through Databricks after that account has joined the workspace.

The first deployment uploads the referenced notebook and source files to the deploying user's bundle directory and creates the job. It does not clone the GitHub repository into the Databricks workspace. Running the job creates the shared schema and volume if they do not already exist.

## First validated Databricks run

The `team` bundle target was validated, deployed, and run successfully in Databricks Free Edition on October 23, 2026. The run used serverless compute and confirmed that the configured secret could authenticate the ACS request and that the initial publisher domains were reachable from the workspace.

The run created and the Unity Catalog API confirmed:

- `workspace.neighborhood_twin_dev.bronze_acs5_tract`;
- `workspace.neighborhood_twin_dev.bronze_fhfa_tract_hpi`;
- `workspace.neighborhood_twin_dev.source_snapshot_manifest`;
- the managed volume `workspace.neighborhood_twin_dev.source_snapshots`.

This establishes the shared ETL and storage path; it does not complete source feasibility review. The next check is the coverage and quality profile listed under **Immediate next work** below. The bundle is currently deployed by one team member. After the second account joins the workspace, verify its catalog access and grant permission to run the job before treating the workflow as fully shared.

The initial pilot defaults to Arizona (`04`), Michigan (`26`), and Pennsylvania (`42`). These states expose different housing markets and preserve Michigan relevance without limiting the final similarity pool to one region. They are a pipeline and coverage test, not the final geographic scope.

## Initial bronze feasibility profile

The first persisted quality profile completed on October 23, 2026. It wrote an append-only set of metrics to `workspace.neighborhood_twin_dev.bronze_quality_metrics` and finished with zero hard failures and zero warnings. This means the declared keys, identifiers, parseability checks, source hashes, and ACS accounting relationships passed. It does not mean every tract has a usable modeling target.

The main results were:

- FHFA contains 2,179,042 tract-year rows for 63,930 tracts from 1975 through 2025. The 10th, 50th, and 90th percentiles of observed history length are 24, 34, and 41 years.
- FHFA has 109,777 rows with no HPI value and 209,441 rows with no annual-change value. These are retained as source information rather than treated as zero or automatically imputed.
- The 2024 ACS pilot contains 8,228 unique tracts across the three requested states, with no duplicate tract-release keys, malformed GEOIDs, or internal housing-total discrepancies.
- The ACS special-value audit found unusable estimate placeholders in 254 median-income records, 704 median-rent records, and 352 median-owner-value records. Their paired margins of error also contain special values. Silver processing must convert these placeholders to nulls while keeping an explicit reason or quality flag.
- 6,340 ACS tracts, or 77.1%, have a same-year FHFA row. Only 5,204 ACS tracts, or 63.2%, also have a non-null 2024 HPI. Usable target coverage is 47.0% in Arizona, 75.2% in Michigan, and 61.1% in Pennsylvania.

A follow-up join showed that the 6,340 same-year matches are also the only pilot ACS tracts with any FHFA history in the current file. The unmatched tracts therefore are not simply missing one recent year. The silver layer should preserve the full ACS tract universe, attach transparent FHFA coverage flags, and form a separate eligible modeling cohort instead of silently dropping uncovered communities. The application should still be able to describe an uncovered tract, but it must not show an FHFA forecast where the target history is unavailable. Later feasibility work will compare this target coverage with housing-stock composition and geography to identify selection bias.

## Validated silver builds

The separate silver job completed successfully in Databricks Free Edition on October 23,
2026. It reads accepted bronze tables and does not rerun acquisition. The refined build
preserved all 2,179,042 FHFA rows and all 8,228 ACS pilot tract-release rows. It produced
172,788 normalized ACS measure rows, exactly 8,228 tracts multiplied by 21 measures, plus a
21-row measure dictionary.

The four current silver products are overwritten from the selected accepted snapshots. Every
data row carries its source snapshot, retrieval timestamp, silver build, and schema version;
the dictionary carries the build and schema version. The silver quality table is append-only,
so prior build results remain available for review. Two consecutive runs of the refined job
preserved the same four table counts and left one current build in each output table.

The latest run recorded 34 passing checks and 11 informational measures, with no warnings or
failures. Hard checks cover schema names and Spark types, snapshot registration and accepted
status, source-to-silver row reconciliation, key uniqueness, GEOID format, ACS parseability,
nonnegative published values, Census housing-account balances, geography-vintage assignment,
derived-ratio ranges, normalized-to-wide row equivalence, dictionary uniqueness, and missing-
reason consistency. The repeat run took about two and a half minutes. Runtime and storage
should be monitored again when historical and national ACS coverage is added.

### Silver source contracts

`silver_fhfa_tract_year` has one row per `geoid × observation_year`. It keeps the FHFA HPI,
annual percentage change, alternative-base indexes, source lineage, and explicit booleans for
HPI and annual-change availability. Missing HPI values remain null and are never converted to
zero. This table describes the source's filtered single-family market rather than all housing.

`silver_acs_tract_measure` is the primary ACS analytical table. Its key is `geoid ×
acs_release_year × measure_name`, and its 29 columns stay usable as the project adds releases
or measures. Each row carries the readable measure name and label, Census group, unit,
statistical universe, estimate, margin of error, relative margin of error, missing reasons,
survey window, geography vintage, and lineage. The survey start year, survey end year, and
release year remain separate because an ACS five-year release is not a single-year measurement.

`silver_acs_measure_dictionary` has one row per selected measure. It records the original
estimate and margin-of-error codes and links to the official Census group metadata used to
verify the table concept, universe, and unit. This lets a contributor understand a field
without decoding names such as `B25064_001E`. The current definitions are checked against the
[2024 ACS five-year group metadata](https://api.census.gov/data/2024/acs/acs5/groups.html), and
each dictionary row links to its specific detailed-table group.

`silver_acs_tract_year` remains available as a generated wide convenience table with one row
per `geoid × acs_release_year`. It is useful for tract profiles and transformations that need
several measures on one row, but it is not the default table for general exploration. Source
codes are renamed to readable fields. Documented Census special values become nulls with
fields such as `median_gross_rent_estimate_missing_reason`; unexpected text stops publication
as a parse failure.

The ACS table also includes occupancy, vacancy, tenure, and housing-structure shares. These
are transparent ratios of published estimates, not new measurements, and no uncertainty is
invented for them. Each underlying estimate retains its margin of error and a relative-MOE
field. Derived-ratio uncertainty will be handled later if the ratios become model inputs.

All 18 count measures are complete across the 8,228 pilot tracts. The three median-dollar
measures have legitimate unavailable values after Census special codes are translated: median
household income is missing for 254 tracts (3.09%), median owner-occupied value for 352
(4.28%), and median gross rent for 704 (8.56%). Those nulls align with their stated universes
and remain visible rather than being filled with zero.

## Historical ACS pilot

The focused Census API remains the preferred acquisition method for the selected 21 measures.
It downloads only the fields the project uses, preserves estimate/MOE pairs, and produced small
state-level responses that fit comfortably within the current Databricks workflow. National
history should still be run in reviewed batches rather than one unbounded request grid.

The first historical batch added the 2014 and 2019 five-year releases for Arizona, Michigan,
and Pennsylvania. Each release contains 7,557 unique tract rows: 1,526 in Arizona, 2,813 in
Michigan, and 3,218 in Pennsylvania. Together with 2024, bronze and silver now contain nine
state/release snapshots and 23,342 tract-release rows. The normalized table contains 490,182
rows, exactly 23,342 multiplied by 21 measures, and the dictionary remains 21 rows.

The historical ingestion rerun reused the accepted snapshots without adding duplicate bronze
rows. The first job attempt had already completed all six acquisitions but failed in its final
display because Spark Connect did not accept a tuple passed as one `isin` value. Expanding the
tuple into separate arguments fixed the display, and the complete job then finished successfully
without changing the persisted row counts.

Both 2014 and 2019 are labeled as 2010-vintage tract geography; 2024 is labeled as 2020-vintage.
The silver quality run reported all 15,114 older-vintage rows as not yet harmonized and excluded
them from direct FHFA coverage joins. This is intentional: matching an older GEOID string directly
to the current 2020-vintage FHFA table could create plausible-looking but invalid comparisons.
After expansion, two consecutive silver runs each recorded 34 passing checks, 12 informational
measures, and no warnings or failures. The current counts and runtime remain manageable, but this
three-release pilot is not enough history for final forecasting or analogue evaluation.

### Findings that affect later modeling

The pilot ACS estimates have meaningful uncertainty. Across the three states, the median and
90th-percentile relative margins of error are 18.7% and 37.7% for median household income,
13.9% and 42.3% for median gross rent, and 10.4% and 27.7% for median owner-occupied value.
The pipeline retains these values but does not impose a universal reliability cutoff yet.
Exploration should examine the full distributions and test whether uncertainty flags or
sensitivity exclusions change the conclusions.

FHFA target coverage is also visibly selective. In the pooled pilot, tracts with a usable
same-year HPI have a median single-family share of 82.5%, compared with 75.5% among uncovered
tracts. Their mean vacancy rate is 8.0% rather than 15.0%, median household income is about
$80,500 rather than $60,300, and median population is 3,937 rather than 2,803. These are
descriptive comparisons, not causal findings, and pooled state differences explain part of
the gap. The direction is also visible within Michigan and Pennsylvania, so target coverage
cannot be assumed to be random.

This does not block the tract-level project. It does require the project to:

- report which tracts and housing-market segments receive forecasts;
- compare model errors and interval coverage across housing composition and geography;
- keep descriptive neighborhood profiles available when FHFA forecasting is unavailable;
- avoid presenting results from FHFA-covered tracts as representative of all communities;
- consider a county or metro fallback only as separately labeled regional context, never as
  an invented tract target.

## October 2026 expansion checkpoint

The reviewed national expansion is now complete. The ACS contract covers every annual five-year
release from 2010 through 2024 for the 50 states and District of Columbia: 15 releases, 51
jurisdictions, and 765 required state-release pairs. Puerto Rico and the island areas remain
outside the supported modeling scope rather than being forced into the national hierarchy.

Bronze contains 1,160,833 rows across 768 immutable snapshots and 765 validated source IDs. Three
2024 pilot-state sources have an earlier byte-identical snapshot, which is valid acquisition
history rather than a duplicate within a source snapshot. Silver selects one validated snapshot
per state and release, producing 1,152,605 tract-release rows and 24,204,705 normalized measure
rows. The latest bronze and silver runs both report zero hard failures; silver also reports zero
warnings.

The national backfill is a separate, resumable Databricks job. Its first run completed all 672
missing source acquisitions, then exposed an overly broad bronze uniqueness check that treated
records from two immutable snapshots as duplicate analytical keys. The corrected rule enforces
uniqueness within `source_snapshot_id + geoid + release`, while silver continues to enforce one
selected snapshot per state and release. A Databricks repair run restarted at validation and did
not rerun the successful 90-minute ingestion.

Four current gold products are also live. The complete current profile retains all 85,528
canonical tracts, while separate tables expose 83,359 initial similarity candidates, 50,601
initial forecasting candidates before FHFA geography reconciliation, and an 8,182-row
Arizona/Michigan/Pennsylvania application cohort. Applying the reviewed Connecticut bridge to
FHFA as well as ACS raises the current forecast screen to 51,263 tracts.
These are transparent availability filters, not final model populations. Their implementation is
described in Stage 05 and their table contracts are maintained in the
[data guide](../data/README.md).

The expanded build exposed one important geography exception. The 2022 ACS adopted Connecticut's
new planning regions as county equivalents, changing its current tract GEOIDs relative to the 2020
canonical identifiers. The implemented pipeline now ingests official 2020 and 2024 TIGER/Line
references and publishes 879 safe one-to-one land-tract mappings. The five current water-only
tracts remain explicit exceptions. The refreshed gold build reports 879 Connecticut bridge
matches and zero unexpected ACS-to-canonical mismatches.
FHFA uses the same current planning-region identifiers for 728 Connecticut tracts. All 728 map
through the bridge, leaving zero unmapped Connecticut FHFA identifiers and restoring 662 current
forecast candidates in the state.

If Databricks blocks a publisher domain, download the official file outside the workspace, upload it to one directory in the managed volume, set the notebook's `uploaded_source_directory` widget, and rerun. Filenames must match the source definitions. The registration path hashes and copies the upload into the same immutable layout and records `acquisition_method=manual_upload`; it does not silently treat a manually uploaded file as a successful HTTP response.

## Acquisition design

Each source gets a small adapter with the same lifecycle:

1. load source configuration;
2. resolve request parameters and destination;
3. retrieve or register a manually downloaded file;
4. validate status, content type, and expected structure;
5. compute size, SHA-256 hash, and schema fingerprint;
6. write an immutable raw snapshot;
7. emit a source manifest;
8. parse to bronze without changing source meaning;
9. validate and publish the silver table.

Downloads should be idempotent. If the expected snapshot and hash already exist, the adapter should reuse them unless refresh is explicitly requested. Retries should use bounded backoff and respect API limits; failed or partial responses never become approved snapshots.

## Date semantics

Do not collapse these into a single `year` field:

- reference year or survey period;
- source publication or vintage date;
- retrieval timestamp;
- date the value would have become available for modeling;
- pipeline build timestamp.

These fields are necessary for leakage-safe reconstruction and later source revisions.

## Bronze responsibilities

Bronze preserves the source payload and its meaning. It may add lineage columns, but should not harmonize geographies, impute values, or calculate model features. Keep source missing codes until they can be translated deliberately.

For APIs, save either the response payload or a deterministic, hashable representation of it when terms permit. Record the request parameters and pagination. For manual sources, record the official landing page, exact filename, instructions, and hash so another person can verify the same object.

## Silver responsibilities

Silver adapters:

- parse types and normalize column names;
- preserve identifiers as zero-padded strings;
- translate documented missing-value codes to nulls with reason fields where useful;
- validate the true source grain and primary key;
- pair ACS estimates with margins of error;
- standardize units without losing the original field or definition;
- attach reference, release, and availability dates;
- quarantine unexpected records rather than dropping them silently.

Geographic harmonization belongs to Stage 03. A silver source table may retain its original tract vintage.

## Local and Databricks execution

Databricks is the authoritative storage and ETL environment because both team members need the same source snapshots and tables. Engine-neutral acquisition, parsing, and validation logic remains locally testable; local development should use temporary directories or small permitted fixtures rather than creating a second canonical data lake.

The normal development loop is local editing in VS Code, GitHub review, bundle validation, and an intentional Databricks deployment. Deploying the bundle updates the shared job definition; it does not move Unity Catalog data back into the local repository. The first team member acts as deployment owner until a reviewed automated deployment identity is justified. The partner can run and inspect the job after receiving Databricks job permissions, while both contributors read the same catalog tables.

Databricks Free Edition uses quota-limited serverless compute and restricts outbound internet access. The implemented upload-registration path is therefore part of the normal pipeline, not an emergency workaround. Whether a snapshot arrived by HTTP or upload, downstream code receives the same hash, immutable location, manifest fields, and bronze validation.

## Data-quality checks

Every source needs checks for:

- required columns and types;
- primary-key uniqueness at the declared grain;
- expected year and geography ranges;
- row-count change from the prior accepted version;
- null and missing-code rates;
- identifier format;
- numeric ranges and units;
- duplicate or conflicting vintages;
- source-specific invariants.

A warning threshold and a hard-failure threshold should be distinct. For example, a modest row-count change may require review, while a missing required column should stop the build.

## Security and licensing

API keys come from environment variables or Databricks secrets, not configuration files, widgets, or notebook source. Logs must avoid printing tokens and full signed URLs. Each manifest links to terms and citation guidance. A source with uncertain redistribution rights can still be reproducible through acquisition code and manifests without committing the data itself.

## Required outputs

- source adapter and configuration;
- immutable snapshot and source manifest;
- bronze table or file;
- validated silver table;
- quality report with row changes and exceptions;
- small permitted fixture covering normal and difficult records;
- rebuild command or job definition.

## Acceptance checks

- A clean pilot run produces the same approved hash and row counts.
- A changed schema fails with a useful message.
- Secrets and absolute local paths are absent from committed output.
- A partial download cannot be mistaken for a valid snapshot.
- Another contributor can rebuild or register the source from the documentation.
- Source grain and date fields remain intact through silver.

## Immediate next work

Bronze, silver, complete national 2010-2024 ACS history, canonical geography, the supported Census
hierarchy, and the first current gold products are complete. The next data work should remain
ordered:

1. profile the expanded ACS uncertainty, missingness, and cohort attrition by state and housing
   composition rather than relying on pooled national summaries;
2. create leakage-safe historical state/target tables for the forecast horizons;
3. choose whether detailed TIGER/Line geometry and national adjacency are required for the first
   model or can follow the nonspatial baselines;
4. add a small, justified set of regional economic or housing-supply sources only where they
   improve a stated research question;
5. monitor Delta storage, job runtime, and free-workspace limits before adding another source or
   materially expanding the feature contract.

## Handoff

Stage 03 receives source-specific silver tables and manifests. It should not need to know how pagination, authentication, or raw file parsing worked.

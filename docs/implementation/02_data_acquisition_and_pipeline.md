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
- unit tests cover request limits, GEOID construction, key redaction, hashing, immutable placement, and the manual-upload fallback.

This is a bronze feasibility pipeline. It does not yet harmonize tract vintages, translate ACS missing-value codes, calculate housing shares, or create the modeling table. Those belong in the silver and geography stages after the pilot establishes actual coverage.

## Databricks storage contract

Databricks is the canonical team environment for source data and ETL. Use an existing Unity Catalog catalog, a shared project schema, and a managed volume:

| Object | Initial name | Purpose |
|---|---|---|
| Catalog | chosen from the shared workspace | Existing governance boundary; the notebook does not create a catalog |
| Development schema | `neighborhood_twin_dev` | Shared tables created during the feasibility phase |
| Managed volume | `source_snapshots` | Immutable raw source payloads and sidecar manifests |
| Manifest table | `source_snapshot_manifest` | Searchable source version, checksum, request, license, and validation history |
| FHFA bronze table | `bronze_fhfa_tract_hpi` | Source-shaped tract-year HPI records plus snapshot lineage |
| ACS bronze table | `bronze_acs5_tract` | Source variable codes plus ACS release window and snapshot lineage |

Raw file paths follow:

```text
/Volumes/<catalog>/neighborhood_twin_dev/source_snapshots/
  bronze/<source_id>/retrieval_date=<YYYY-MM-DD>/<sha-prefix>/<source-file>
```

Managed volumes are for raw files. Delta tables are for queryable records. Do not duplicate this design with legacy DBFS mounts, local OneDrive folders, or raw files committed to Git.

## Team setup before the first run

1. Create or choose one Databricks Free Edition workspace and add both team members.
2. Confirm the Unity Catalog catalog both people can use. The notebook defaults to `workspace`, but the real catalog name must be checked in Catalog Explorer.
3. Request a free Census API key. The current API rejects the tract requests without one.
4. Create a Databricks-backed secret scope named `neighborhood-twin` and save the key as `census-api-key`. The widget names can be changed if the workspace uses different names.
5. Connect this GitHub repository as a Databricks Git folder and check out the same reviewed feature branch. Merge only after review.
6. Open `notebooks/01_feasibility/01_ingest_core_sources.py`, attach serverless notebook compute, confirm the widgets, and run all cells.
7. Record the catalog, schema, pilot states, ACS release, Git commit, and run owner in the team notes.

The initial pilot defaults to Arizona (`04`), Michigan (`26`), and Pennsylvania (`42`). These states expose different housing markets and preserve Michigan relevance without limiting the final similarity pool to one region. They are a pipeline and coverage test, not the final geographic scope.

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

After the first shared run, do not add more source families immediately. First produce a short feasibility profile from the bronze tables:

1. FHFA row count, tract count, year range, missing HPI/annual-change rates, history length, and coverage by state;
2. ACS rows per state, uniqueness of tract/release keys, special missing codes, and margins-of-error distributions;
3. direct FHFA-to-ACS GEOID match rate for the pilot release;
4. raw storage, Delta table size, runtime, and any quota or network failures;
5. a decision on API versus ACS bulk files for national historical acquisition.

Only then should the team expand ACS years, move from three states toward national coverage, build silver housing-composition fields, and add the small set of regional economic series needed for modeling.

## Handoff

Stage 03 receives source-specific silver tables and manifests. It should not need to know how pagination, authentication, or raw file parsing worked.

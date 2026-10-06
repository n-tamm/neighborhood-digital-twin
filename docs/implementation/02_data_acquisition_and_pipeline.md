# 02 — Data Acquisition and Pipeline

## Purpose

This stage turns approved public sources into repeatable, versioned data assets. The main requirement is not a large download script; it is a traceable path from an external file or API response to a validated table that another contributor can rebuild.

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

The local path should support a small, cached pilot through ordinary files and DuckDB, Polars, or pandas. Databricks can use the same configuration and manifests to build Delta bronze and silver tables. Table names, keys, units, and validations should match even if the execution engine differs.

Databricks Free Edition restricts outbound access and compute, so acquisition must have a documented fallback: download locally, verify the hash, and upload/register the snapshot. The pipeline should not depend on an undocumented manual step.

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

API keys come from environment variables, Databricks secrets, or Streamlit secrets—not configuration files or notebooks. Logs must avoid printing tokens and full signed URLs. Each manifest links to terms and citation guidance. A source with uncertain redistribution rights can still be reproducible through acquisition code and manifests without committing the data itself.

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

## Handoff

Stage 03 receives source-specific silver tables and manifests. It should not need to know how pagination, authentication, or raw file parsing worked.

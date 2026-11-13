# `serving_release_manifest`

## Purpose and grain

This Delta table is the activation record for application-serving releases. Its grain is one
serving release, component, and published table. Analogue serving schema 1.0 had three validated
rows: match, summary, and availability. Schema 1.1 has five rows by adding the match-explanation
and annual-trajectory tables.

## Important fields

- `serving_release_id`, `serving_schema_version`, and `serving_built_at_utc` identify the immutable
  release contract.
- `component_name` and `table_name` identify the required published object.
- `row_count`, `serving_as_of_year`, `horizons_csv`, and `top_k` describe its validated scope.
- source build IDs and `retrieval_method` connect the release to the approved analytical evidence.
- `release_status` is `validated` only after all pre-publication checks pass.

## Activation rule

Job 700 writes this table last. Application code must select a release with validated manifest
rows for every required table and then filter all serving reads to that same release ID. A data
partition without a complete manifest is an inactive partial attempt, not the newest release.

## Sample

See [`serving_release_manifest.jsonl`](../../data/samples/serving_release_manifest.jsonl). It
contains the complete five-row activation manifest for validated schema-1.1 release
`analogue-20261113T132155097077Z`.

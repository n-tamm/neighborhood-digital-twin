# Application Serving Bundle Contract

The serving bundle is the only supported data boundary between batch analytics and the interactive application. It is immutable after publication and contains only approved, deployable outputs.

## Required contents

```text
bundle/
├── manifest.json
├── geography.parquet
├── current_state.parquet
├── history.parquet
├── forecasts.parquet
├── analogues.parquet
├── explanations.parquet
└── scenario_spec.json
```

Files may be omitted only when the manifest declares the corresponding feature unavailable and the application handles that state. A small static metadata file may be added without changing the central contract.

## Manifest fields

- `bundle_version` and `schema_version`;
- creation timestamp, pipeline commit, and run ID;
- observation cutoff and geography vintage;
- state, feature, and model versions;
- supported metros, years, horizons, and application features;
- file paths, row counts, byte sizes, and checksums;
- quality-gate result and known exclusions;
- minimum compatible application version.

## Table requirements

All tract-level files use string GEOIDs. Time-series and forecast tables state the reference period and units. Forecasts include point estimates, interval bounds, horizon, model version, and display/suppression status. Analogues identify both the query state and historical candidate, distance or similarity, rank, and method version. Explanation fields must say what they explain and cannot be reused across incompatible model versions.

Geometry should be simplified for the application's zoom levels while preserving the canonical GEOID. The bundle must not contain personally identifiable information, secrets, unrestricted raw data, or fields excluded by source terms.

## Validation

Before publication, verify:

- required manifest fields and declared files exist;
- checksums, row counts, types, and keys match;
- GEOIDs agree across tables and geometry;
- interval lower bounds do not exceed point estimates or upper bounds where that ordering is required;
- analogue queries have unique ranks and do not retrieve prohibited future states;
- every displayed result has a quality status and version metadata;
- a fixture application can load the bundle and complete its main user flow.

## Compatibility and failure behavior

The application must check schema and minimum application versions at startup. Unknown major versions fail closed with a clear message. Missing optional features produce a labeled unavailable state, while a checksum or required-table failure prevents the bundle from loading.

## Publication

Publish the bundle under a versioned, immutable name and update a small release pointer only after validation. Retain the previous known-good bundle for rollback. Record the public location and checksum in release notes.


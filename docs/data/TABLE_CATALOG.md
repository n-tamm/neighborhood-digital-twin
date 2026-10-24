# Table Catalog

This catalog describes the tables implemented in `workspace.neighborhood_twin_dev`. Table and
column descriptions are also attached directly to the Databricks tables. Counts change when a
pipeline is rerun, so the defining information here is each table's grain and key rather than a
fixed row total.

## Governance and bronze

### `source_snapshot_manifest`

- **Grain and key:** one row per immutable source snapshot; keyed by `source_snapshot_id`.
- **Purpose:** records where a source came from, when it was retrieved, how it is licensed, where
  its raw object is stored, and whether it passed acquisition checks.
- **Main structure:** source identity, retrieval metadata, content hash, governed volume path,
  licensing fields, validation status, and validation messages.
- **Use:** begin here when reproducing or auditing an ingestion. Analytical code should not join
  this table directly unless it needs source-level lineage.

### `bronze_fhfa_tract_hpi`

- **Grain and key:** one row per snapshot, tract GEOID, and observation year.
- **Purpose:** preserves the source-shaped annual FHFA tract HPI file with snapshot lineage.
- **Main structure:** tract, state, year, annual change, several HPI bases, and source fields.
- **Caution:** FHFA tract HPI describes single-family price movement, not the level or composition
  of the entire housing market. Sparse or unavailable values remain null.

### `bronze_acs5_tract`

- **Grain and key:** one row per snapshot, tract GEOID, and ACS release year.
- **Purpose:** preserves the selected ACS API response before numeric missing-value rules and
  readable naming are applied.
- **Main structure:** Census API variable codes, geography fields, release-window fields, and
  source lineage.
- **Caution:** each release pools five years of survey responses; adjacent annual releases overlap
  by four years and must not be treated as independent annual samples.

### `bronze_census_tract_relationship_2010_2020`

- **Grain and key:** one row per unique 2010-tract to 2020-tract relationship edge.
- **Purpose:** keeps the official Census relationship records needed to understand tract splits,
  merges, and stable mappings across the decennial boundary change.
- **Main structure:** source and target GEOIDs, names and areas, overlapping-part areas, and
  snapshot lineage.
- **Caution:** this is a relationship graph, not a one-row tract dimension.

### `bronze_census_tract_display_geometry_2020`

- **Grain and key:** one row per displayable 2020 tract GEOID.
- **Purpose:** stores parsed attributes and WKB from the simplified national cartographic archive.
- **Main structure:** names and FIPS codes, land/water area, bounding box, geometry type, geometry,
  and lineage.
- **Caution:** the source is deliberately simplified for mapping and is not suitable for precise
  spatial analysis.

### `bronze_quality_metrics`

- **Grain and key:** one row per quality run, table, metric, and dimension.
- **Purpose:** keeps append-only acquisition and bronze feasibility checks so past runs are still
  inspectable.
- **Main structure:** run ID, profiled table, metric group and name, value, status, expectation,
  and notes.

## Silver analytical source tables

### `silver_fhfa_tract_year`

- **Grain and key:** one row per 2020 tract GEOID and observation year.
- **Purpose:** provides typed annual FHFA history for forecasting and housing-market trajectory
  features.
- **Main structure:** readable HPI measures, availability flags, geography vintage, and build and
  snapshot lineage.
- **Caution:** this table should support a housing-price component of the twin, not stand in for a
  complete neighborhood or housing-market outcome.

### `silver_acs_tract_measure`

- **Grain and key:** one row per tract GEOID, ACS release year, and governed measure.
- **Purpose:** is the primary ACS analytical product. Its long format makes definitions,
  uncertainty, missingness, and cross-release comparisons easier to manage.
- **Main structure:** tract and release fields, measure name and definition, estimate, margin of
  error, relative margin of error, missing reasons, and lineage.
- **Use:** prefer this table for focused analysis, profiling, and any workflow that benefits from
  selecting measures rather than carrying a very wide row.

### `silver_acs_measure_dictionary`

- **Grain and key:** one row per governed ACS measure; keyed by `measure_name`.
- **Purpose:** gives readable definitions and preserves the Census estimate and margin-of-error
  codes used during acquisition.
- **Main structure:** ordering, project name, source group and concept, universe, unit, source
  variable codes, metadata release, and metadata URL.

### `silver_acs_tract_year`

- **Grain and key:** one row per tract GEOID and ACS release year.
- **Purpose:** provides a convenient wide form of the governed ACS measures for exploration,
  feature engineering, and current-profile construction.
- **Main structure:** geography and release identifiers, estimate/MOE/missing-reason fields for
  each selected measure, derived housing rates and shares, and lineage.
- **Caution:** the long measure table remains the source of truth when definitions or uncertainty
  need to be handled programmatically.

### `silver_quality_metrics`

- **Grain and key:** one row per quality run, table, metric, and dimension.
- **Purpose:** records schema, integrity, balance, missingness, temporal coverage, and
  reconciliation results for silver builds.

### `silver_tract_relationship_2010_2020`

- **Grain and key:** one row per unique 2010-tract to 2020-tract edge.
- **Purpose:** turns the official relationship file into typed mapping edges with overlap shares
  and conservative flags for stable and dominant mappings.
- **Main structure:** source/target GEOIDs and areas, part areas, source and target land shares,
  mapping type, stability flags, and lineage.
- **Use:** this is the correct starting point for putting pre-2020 measures onto a 2020 tract
  framework. Do not equate matching GEOIDs with unchanged boundaries without checking the flags.

### `silver_tract_display_geometry_2020`

- **Grain and key:** one row per displayable 2020 tract GEOID.
- **Purpose:** supplies lightweight geometry and bounding boxes for application maps.
- **Caution:** `geometry_role` explicitly limits this table to display; use full-resolution TIGER
  geometry for analytical spatial work.

### `geography_quality_metrics`

- **Grain and key:** one row per geography quality run, metric, and dimension.
- **Purpose:** preserves relationship and display-geometry validation and coverage results.

### `silver_canonical_tract_2020`

- **Grain and key:** exactly one row per relationship-defined 2020 tract GEOID.
- **Purpose:** defines the complete stable tract backbone used for joins. Display geometry is
  optional and cannot determine whether a tract exists.
- **Main structure:** tract identifiers and names, areas, optional display geometry and bounding
  box, coverage flags, source IDs, and build lineage.
- **Caution:** current ACS tract identifiers in Connecticut changed after the state adopted new
  county-equivalent planning regions. That bridge is a separate required geography task.

### `canonical_geography_quality_metrics`

- **Grain and key:** one row per canonical geography quality run and metric.
- **Purpose:** records uniqueness, identifier validity, source reconciliation, and display coverage
  for the canonical tract build.

## Gold current products

### `gold_tract_profile_current`

- **Grain and key:** exactly one row per canonical 2020 tract GEOID.
- **Purpose:** is the main current-state product for modeling and application prototypes. It joins
  a compact, readable set of ACS housing and community fields with summarized FHFA history while
  retaining every canonical tract.
- **Main structure:** place identity, current ACS estimates and uncertainty, housing-mix rates,
  recent and historical HPI fields, coverage flags, transparent candidate flags, and build lineage.
- **Caution:** absent source coverage remains null and is explained by flags. This table is a
  feature-ready profile, not a trained model output.

### `gold_similarity_candidate_current`

- **Grain and key:** one row per candidate 2020 tract GEOID.
- **Purpose:** offers a reproducible starting cohort for similarity experiments. A tract must have
  current ACS coverage, positive population and housing-unit estimates, and at least eight of the
  twelve governed similarity inputs.
- **Caution:** this is an availability screen, not a declaration that the eventual feature set or
  matching method is valid. Those choices still require modeling and evaluation.

### `gold_forecast_candidate_current`

- **Grain and key:** one row per candidate 2020 tract GEOID.
- **Purpose:** identifies current-profile tracts with at least ten usable, recent FHFA observations
  for initial forecasting experiments.
- **Caution:** it is a prototype cohort for outcome forecasting. Training examples still need
  point-in-time feature construction and time-aware splits.

### `gold_application_demo_tract`

- **Grain and key:** one row per displayable, current-profile tract in the configured demo states.
- **Purpose:** gives the application team a small but realistic table for map, filter, detail-panel,
  and API work before nationwide performance is necessary.
- **Current configuration:** Arizona, Michigan, and Pennsylvania.
- **Caution:** this table is a development convenience. It does not narrow the national similarity
  goal or define the final application's coverage.

### `gold_quality_metrics`

- **Grain and key:** one row per gold quality run, table, and metric.
- **Purpose:** records nonempty output, GEOID uniqueness, full-profile reconciliation, and current
  ACS-to-canonical join coverage before gold tables are published. Unmatched Connecticut GEOIDs
  are reported as a known warning, while unmatched current ACS identifiers outside reviewed
  exceptions are a hard failure.

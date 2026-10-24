# 03 — Geography and Time Alignment

## Purpose

Neighborhood analysis fails quietly when tract boundaries, regional membership, and source dates are treated as simple join columns. This stage creates a canonical spatial and temporal frame while preserving the uncertainty introduced by harmonization.

## Current implementation

The first part of this stage is live in Databricks. The `geography_relationship_pipeline` job reads the registered national [Census 2010-to-2020 tract relationship file](https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.2020.html), validates its [official record layout](https://www.census.gov/programs-surveys/geography/technical-documentation/records-layout/2020-comp-record-layout.html), and publishes three managed Delta products:

- `bronze_census_tract_relationship_2010_2020`, which preserves the 16 source columns and adds snapshot lineage;
- `silver_tract_relationship_2010_2020`, which uses readable typed fields, calculates land-overlap shares, classifies mapping structure, and retains build lineage;
- `geography_quality_metrics`, which records hard integrity checks and descriptive mapping coverage for every run.

The national output contains 126,450 unique relationship rows connecting 74,134 source tracts to 85,528 target tracts. A repeat run left one bronze snapshot, one manifest row, 126,450 silver rows, and one current silver build, so the stage is idempotent at its declared grains. The latest successful run recorded eight passing checks, 69 informational diagnostics, and no warnings or failures.

The live data also exposed 597 relationship rows involving a zero-land-area tract. These represent 352 source and 368 target water-only tracts, all with nonzero water area. Their land shares are intentionally null and reported separately; unexpected nulls or out-of-range shares still stop publication.

## Relationship interpretation

Each source-target edge is labeled `one_to_one`, `split`, `merge`, or `complex` from its exact graph degrees. This is useful structural information, but very small boundary slivers can make an otherwise similar tract look complex. The silver table therefore carries two additional flags:

- `is_dominant_source_mapping` identifies the largest target overlap when it contains at least 95% of the source tract's land;
- `is_stable_measure_mapping` is deliberately stricter: the source and target GEOID must be the same, the edge must rank first for the source tract, and both source and target land shares must be at least 95%.

Nationally, 62,544 source tracts have a dominant 95% land-overlap mapping and 60,512 meet the conservative stable-measure rule. In the current pilot, the stable rule retains 1,227 of 1,526 Arizona source tracts, 2,415 of 2,813 Michigan tracts, and 2,873 of 3,218 Pennsylvania tracts. These are coverage facts, not evidence that every retained ACS value is automatically comparable.

The Census relationship file provides land and water overlap only. It does not contain population or housing-unit allocation factors. For that reason:

- land shares are diagnostics and boundary-overlap descriptors;
- they must not be used to average or redistribute medians, rates, ratios, indexes, or margins of error;
- the stable subset can support a transparent sensitivity analysis for nonadditive measures;
- count harmonization remains deferred until the team chooses and validates a defensible population or housing-weight source and conservation rule.

This decision protects the application from presenting a mathematically convenient area-weighted value as though it represented where people or housing units moved across tract boundaries.

## Display geometry

The separate `display_geometry_pipeline` job now parses the registered national 1:500,000 Census cartographic-boundary archive with pinned `pyshp` and Shapely dependencies. It publishes:

- `bronze_census_tract_display_geometry_2020`, containing the source attributes, original CRS text, WKB geometry, bounds, validity fields, and snapshot lineage;
- `silver_tract_display_geometry_2020`, containing readable tract and county identifiers, names, areas, WKB geometry, bounds, and an explicit `display_only_cartographic_1_to_500000` role;
- run metrics in the existing `geography_quality_metrics` table.

The output contains 85,187 unique GEOIDs, including 84,784 polygons and 403 multipolygons. No geometry is empty or invalid, no GEOID is duplicated, and all bounds fall within longitude and latitude limits. A second run preserved one bronze snapshot, one manifest row, 85,187 silver rows, and one current build.

The relationship universe contains 341 tracts without a cartographic display feature. Of those, 340 have zero land area and positive water area. The remaining feature is Florida tract `12057980100`, a mostly-water special-use tract with 513,480 square meters of land and 16,360,255 square meters of water. The display layer therefore remains optional in the future canonical tract dimension rather than defining which tracts exist.

The Census describes cartographic boundaries as simplified small-scale mapping files and advises against using them for precise geographic analysis. This project will use this table for application maps and lookup only. Adjacency, distance, area, and other spatial model features require a separate reviewed analysis-geometry source, likely detailed TIGER/Line data for the supported scope.

## Canonical geography

The selected modeling backbone is the 2020 census tract. The implemented
`silver_canonical_tract_2020` table starts from all 85,528 distinct targets in the official
relationship file and attaches display geometry when available. It has one row per GEOID, no
duplicate or malformed keys, and reconciles exactly to the relationship target universe. Geometry
is available for 85,187 tracts; the 341 missing display features do not cause row loss.

Current publisher geography is not assumed to remain frozen simply because a source labels its
tracts as 2020 Census geography. In the 2022 ACS, Connecticut replaced its eight former counties
with nine planning regions. The tract boundaries mostly remained the same, but the county segment
of the tract GEOID changed. The current 2024 ACS therefore has 884 Connecticut GEOIDs that do not
directly match the canonical table, while the canonical table has 883 former-county Connecticut
GEOIDs.

That requirement is now implemented from the official 2020 and 2024 Connecticut TIGER/Line tract
archives. Both sources contain the same 879 unique positive-land-area tract codes, so the silver
bridge maps those land tracts one-to-one and fails if either vintage becomes ambiguous or
incomplete. The 2020 source contains four water-only tracts and the current source contains five;
those records are reconciled but never assigned demographic profiles. This leaves 879 governed
bridge matches, five expected current water-only exceptions, and zero unexpected current ACS
mismatches. The bridge retains both GEOIDs so source identity is never overwritten or hidden.

Maintain two geometry products:

- analysis geometry at sufficient quality for adjacency and spatial checks;
- simplified display geometry for the public app.

Do not use heavily simplified display polygons to construct scientific neighbors.

## Cross-vintage harmonization

Older source values may refer to earlier tract boundaries. Use official relationship files where possible and retain:

- source and target geography vintage;
- source and target GEOID;
- land, population, or housing weight used;
- mapping type: one-to-one, split, merge, or complex;
- weight-sum and coverage diagnostics;
- crosswalk version.

The aggregation rule depends on the measure. Counts can be allocated with appropriate weights and recombined. Rates, medians, and indexes generally cannot be treated as additive. Define the rule by field family, test it on known totals, and mark values whose transformation is too uncertain.

Run a sensitivity check on at least one alternative treatment, such as restricting to stable tracts or using a different defensible weight. The point is to show whether crosswalk choices change conclusions.

## Regional context

Create versioned mappings for county, state, Census region, and CBSA or another metro definition. Regional features remain labeled by their original grain. A county permit total attached to a tract is `county_permits`, not `tract_permits`.

Metro definitions can change over time. Decide whether membership is fixed to a current vintage for comparability or time-varying for historical accuracy, then document the tradeoff.

## Spatial relationships

Construct a tract neighbor table with a declared method, such as Queen contiguity, and consider a fallback for islands or disconnected polygons. The table should contain source tract, neighbor tract, weight, method, geometry version, and build version.

Possible secondary relationships include distance bands or nearest centroids, but do not combine them silently with contiguity. Row-standardization or other weight transformations belong in explicit features, not the raw relationship contract.

## Time model

Use a documented forecast origin rather than joining everything on a vague calendar year. For every observation distinguish:

- the period the statistic describes;
- the release or vintage;
- when it was available to the model;
- the forecast origin;
- the target horizon and end period.

ACS five-year releases overlap. Treat them as smoothed, rolling estimates rather than independent annual samples. Prefer lagged levels and slow changes, retain margins of error, and include a non-overlapping-release sensitivity check when practical.

Macro series may be revised. For a strict historical backtest, use ALFRED vintages or a pinned-data policy where revisions would materially change what the model knew. If current revised history is used, disclose it and avoid claiming a perfect real-time simulation.

## Point-in-time join

For each tract and forecast origin, select the most recent source value whose availability date is on or before the origin. Record the selected source vintage and lag. Do not forward-fill indefinitely; set source-specific maximum ages and expose staleness as a feature or quality flag.

## Required outputs

- canonical tract table and geometry metadata;
- source-to-canonical crosswalk tables;
- county, state, region, and metro membership;
- tract adjacency table;
- point-in-time calendar and join rules;
- geography and timing quality report;
- pilot maps for unmatched, complex, and low-confidence cases.

## Acceptance checks

- GEOIDs are valid and unique at the declared grain.
- Crosswalk weights sum within documented tolerance.
- Known aggregate totals are approximately conserved when the measure allows it.
- Invalid or empty geometries are reported and handled explicitly.
- Adjacency is reproducible from the stated geometry and method.
- No selected source release occurs after its row's forecast origin.
- Temporal lags and stale observations are measurable, not hidden.

## Immediate next work

1. Decide the supported scope for detailed TIGER/Line analysis geometry; national display coverage
   does not require national adjacency in the first model.
2. If spatial model features remain in scope, acquire and validate detailed analysis geometry and
   construct adjacency with explicit handling for islands and disconnected tracts.
3. Define a field-family harmonization matrix for counts, medians, rates, ratios, indexes, and
   margins of error before transforming historical ACS values across 2010/2020 boundaries.
4. Use the conservative stable subset as the first historical sensitivity analysis, then decide
   whether a population- or housing-weighted crosswalk is justified for additive counts.
5. Create the aligned tract-release state and target tables needed for time-aware modeling.

## Handoff

Exploration and feature construction receive canonical tract IDs, regional membership, neighbors, source vintages, and point-in-time aligned source values. They should not perform ad hoc crosswalks in notebooks.

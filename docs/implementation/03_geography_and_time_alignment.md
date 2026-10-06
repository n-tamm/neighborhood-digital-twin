# 03 — Geography and Time Alignment

## Purpose

Neighborhood analysis fails quietly when tract boundaries, regional membership, and source dates are treated as simple join columns. This stage creates a canonical spatial and temporal frame while preserving the uncertainty introduced by harmonization.

## Canonical geography

The proposed analytical geography is the 2020 census tract. Confirm that choice during feasibility and record it in a decision document. Every tract identifier should be a validated 11-character GEOID stored as a string.

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

## Handoff

Exploration and feature construction receive canonical tract IDs, regional membership, neighbors, source vintages, and point-in-time aligned source values. They should not perform ad hoc crosswalks in notebooks.

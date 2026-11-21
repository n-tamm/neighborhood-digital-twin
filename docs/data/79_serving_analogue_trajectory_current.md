# `serving_analogue_trajectory_current`

## Purpose and grain

This Delta table stores the observed annual FHFA path after each historical match. Its grain is one
serving release, current query, horizon, match rank, and elapsed-year offset. A one-year match has
offsets zero and one; a three-year match has offsets zero through three.

## Main structure

- query, candidate, origin year, and match rank connect the path to the ranked result;
- `trajectory_year_offset` supports aligned comparison across different historical calendar years;
- `trajectory_observation_year` preserves the actual year;
- HPI, cumulative log change, and cumulative percentage change describe the observed path;
- observation, path-completeness, and endpoint flags make gaps explicit;
- readable candidate geography supports application labels; and
- source-snapshot and serving-release fields preserve lineage.

## Construction and validation

The origin, intermediate annual observations, and direct horizon endpoint come from the canonical
historical FHFA target product. The direct target supplies the endpoint even if an intermediate
annual HPI is unavailable. Every match must have one row for each declared offset and exactly one
endpoint. The endpoint must be observed and reproduce the matched later outcome within numerical
tolerance. Missing intermediate years remain explicit rather than being interpolated.

## Interpretation

This is what happened to the historical FHFA single-family index after the candidate year. It is
not a forecast, confidence interval, causal scenario, property valuation, or record of the full
housing market.

## Sample

See [`serving_analogue_trajectory_current.jsonl`](../../data/samples/serving_analogue_trajectory_current.jsonl).
It contains one complete three-year path, including its origin, two intermediate years, and
validated endpoint.

## Validated release

Current release `analogue-20261121T163609734965Z` contains 2,803,140 rows. Publication revalidated
the expected offset count for every path, one observed endpoint per match, and endpoint agreement
with the published later outcome. Intermediate three-year gaps remain explicit rather than being
interpolated. Job 900 reapplied the table description and all column comments after publication.

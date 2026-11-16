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

Release `analogue-20261113T132155097077Z` contains 2,803,140 rows. All 467,190 one-year match paths
are complete. At three years, 444,093 of 467,190 paths are complete and 23,097 retain at least one
explicit missing intermediate observation; there are 29,804 missing intermediate points in total.
Every endpoint is observed and reconciles to the published match outcome. Job 900 confirmed
comments on all 26 columns.

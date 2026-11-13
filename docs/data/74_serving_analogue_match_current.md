# `serving_analogue_match_current`

## Purpose and grain

This Delta table holds the approved ranked historical analogues used by the application. Its grain
is one serving release, current query tract, horizon, and match rank. A complete available query
has ten distinct candidate tracts.

## Important fields

- `query_geoid_2020`, `query_origin_year`, and `horizon_years` identify the current question.
- `candidate_geoid_2020`, `candidate_origin_year`, and `candidate_target_end_year` identify the
  historical tract-period and when its later outcome became known.
- `similarity_distance` and `match_rank` describe retrieval order; smaller distance is closer.
- `candidate_target_cumulative_log_change` and `candidate_target_annualized_change_pct` are
  observed later FHFA single-family HPI outcomes, not predictions for the query tract.
- `serving_release_id`, `serving_schema_version`, source build IDs, and the retrieval method provide
  release lineage.

Readable tract, county, state, region, and cohort fields are duplicated here deliberately so the
application does not need to join a wide modeling table for a match list.

## Construction and checks

Job 700 uses the exact KD-tree policy approved by job 604. It excludes the query tract, future
candidate outcomes, and locked temporal-test candidates. Publication requires ranks one through
ten, ten unique candidate GEOIDs, and exact reconciliation to the availability and summary tables.

## Interpretation

These rows answer “which earlier communities looked most similar?” They do not say that the query
tract will follow the same path, and the candidate outcome covers FHFA's single-family market only.

## Sample

See [`serving_analogue_match_current.jsonl`](../../data/samples/serving_analogue_match_current.jsonl).
It contains the ten ranked one-year matches for one tract and intentionally selects only the most
useful contract fields.

# `serving_analogue_summary_current`

## Purpose and grain

This Delta table contains one application-ready summary per serving release, current query tract,
and horizon. It reduces ten historical matches into readable distance, age, geographic-reach, and
later-outcome context.

## Important fields

- `analogue_match_count` and `distinct_candidate_tract_count` must both equal ten.
- `analogue_median_log_change` and `analogue_inverse_distance_log_change` summarize observed later
  outcomes using two simple rules.
- cumulative percentage versions translate those values into more familiar terms.
- `analogue_outcome_p10_*` and `analogue_outcome_p90_*` describe the central spread of match
  outcomes.
- `mean_similarity_distance`, `median_similarity_distance`, candidate-year bounds, and
  `cross_state_match_share` help a user judge what kind of evidence produced the summary.
- release and source fields identify the exact approved build.

## Interpretation

`outcome_range_is_calibrated_interval` is always false and `analogue_role` labels this evidence as
historical context rather than the primary forecast. The 10th-to-90th percentile range is a small
descriptive match range, not a statistical confidence or prediction interval.

## Sample

See [`serving_analogue_summary_current.jsonl`](../../data/samples/serving_analogue_summary_current.jsonl).
It includes both supported horizons for three example tracts.

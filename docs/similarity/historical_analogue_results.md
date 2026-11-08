# Historical Analogue Results

## Status

The first development workflow published and validated 640 ranked matches, 224 predictions, four
retrieval-summary rows, and 147 sliced scorecard rows on November 3, 2026. It evaluated 16 queries
at each of the one- and three-year horizons. Each query has ten matches under each representation
and seven prediction methods: four analogue estimates and three forecast comparators. The
successful Databricks job run is `603664480500122`, and the published MLflow run ID is
`ffad7ef8d1bd4d68b56dc61e203c795b`.

## Questions this run answers

The result review will separate three questions that are easy to blur together:

1. **Did retrieval behave as designed?** Each validation query must have ten time-safe matches per
   representation, no self-match, and no candidate outcome that occurs after the query date.
2. **Are the returned examples reasonably varied and understandable?** Distance spread,
   candidate age, cross-state share, same-county share, PCA variance, and raw/PCA overlap describe
   what each representation is doing.
3. **Did later analogue outcomes add forecasting value?** Median and inverse-distance estimates
   are compared with zero change, current state trend, and regularized linear predictions using
   MAE, RMSE, bias, tail error, and skill on the identical query sample.

Passing the first question is a correctness requirement. The second supports interpretation. The
third determines whether historical analogue outcomes deserve a forecast-like role or should be
presented only as contextual examples.

## What the first result shows

All retrieval contract checks passed. No candidate was the query tract, every candidate outcome
ended by the query origin, all queries came from the validation period, and every query received
the declared ten matches in each representation.

The matches are genuinely national rather than disguised local lookups. Cross-state matches make
up 95.0% to 97.5% of results, while same-county matches range from 0.6% to 3.1%. The average
candidate is about 3.7 to 4.6 years older than its query. This is useful for the application's
historical comparison idea, although individual cases still need human review for obvious
mismatches.

Six PCA components retain 83.45% of weighted feature variance at one year and 83.97% at three
years. The two representations agree on only 20.8% of one-year top-ten matches and 27.1% of
three-year matches. PCA is therefore not a harmless compression of the direct representation; it
changes which historical evidence a user would see.

## Later-outcome comparison

The table below reports cumulative-log-change MAE on the 16-query sample for each horizon. Lower
is better.

| Method | One year | Three years |
|---|---:|---:|
| State current trend | **0.0758** | **0.0587** |
| Regularized linear forecast | 0.0763 | 0.0735 |
| Analogue median, weighted standardized | **0.0839** | 0.0947 |
| Analogue inverse distance, PCA | 0.0859 | **0.0919** |
| Analogue inverse distance, weighted standardized | 0.0862 | 0.0982 |
| Analogue median, PCA | 0.0905 | 0.1020 |
| Zero change | 0.1166 | 0.1518 |

Every analogue method improves materially on zero change, with MAE skill ranging from 22.4% to
28.0% at one year and 32.8% to 39.5% at three years. However, none beats the state-trend or
regularized-linear comparator on this sample. The direct weighted-space median is the strongest
analogue at one year; the PCA inverse-distance mean is strongest at three years. That inconsistency
is another reason not to freeze a single analogue forecasting rule from this first small run.

The outcome comparison supports a useful but limited conclusion: the historical matches carry
more signal than assuming no change, but the current forecast baselines remain more accurate.
Right now, the strongest application role is to show comparable historical communities and the
range of what happened to them, with any analogue-derived estimate labeled as secondary context
rather than the main forecast.

## Interpretation guardrails

- The first run is validation-only and uses a deterministic stratified sample, not every tract.
- One-year evidence is primary and three-year evidence is secondary. The five-year analogue test
  is unavailable under the current history and split without relaxing leakage protection.
- The target is cumulative change in FHFA's single-family HPI. It is not a forecast of all housing
  or a complete measure of neighborhood change.
- The 10th-to-90th percentile range of match outcomes is descriptive historical variation, not a
  calibrated prediction interval.
- Similarity is descriptive evidence, not a causal statement that one community will follow
  another.

## Decision after review

Job 601 completed the planned case review and bounded stability test. Its corrected publication
contains 6,720 variant matches, 672 query-level stability rows, and 600 rows of feature-level case
evidence. Small family-weight changes retain 93.4% of weighted neighbors on average and are exact
under the shortlist-boundary proof. Weighted-standardized retrieval is therefore the provisional
application default. PCA remains an internal comparison because alternate component counts retain
only 50.9% of the six-component list on average and reviewed examples sometimes hide a large
original-family gap.

The application should also return distinct physical communities rather than multiple years from
one tract. Seventeen of 32 baseline query lists contain a repeated tract; enforcing uniqueness
retains 93.1% of neighbors, is exactness-certified, and restores ten distinct communities.

Job 602 subsequently expanded the sample to 88 one-year and 90 three-year queries, required ten
distinct communities, and ensured that every eligible housing, size, and uncertainty category was
represented. Weighted analogues had lower overall MAE than PCA at both horizons, while the
regularized-linear forecast remained more accurate. Weighted standardized distance and the
distinct-community rule are therefore frozen for current-neighborhood retrieval. Analogue outcomes
remain secondary historical context, and the locked temporal test remains unopened.

# Historical Analogue Results

## Status

The first Databricks development run is in progress. This file will be updated from the published
Delta scorecard and retrieval summary when job `502` succeeds. Performance values are not copied
from notebook display text or estimated during implementation.

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

The team will use this evidence to choose among three honest product roles:

- retain both representations if they produce complementary but understandable examples;
- select one representation if it is more stable, interpretable, and useful; or
- keep historical matches as context without an analogue forecast if their later outcomes do not
  improve on simple comparators.

An application-serving table and current-neighborhood lookup will be designed only after that
decision. The locked temporal test remains unopened until the representation and prediction rule
are frozen.

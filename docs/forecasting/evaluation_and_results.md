# Forecast Evaluation and Current Results

## What is being evaluated

The target is cumulative log change in FHFA single-family tract HPI from a forecast origin to its
future endpoint. One year is the primary horizon. Three years is a secondary horizon with fewer
independent historical origins.

The workflow deliberately separates four kinds of evidence:

- **Training folds** tune the one-year tree without reading validation outcomes.
- **Validation origins** compare methods and support the frozen selection.
- **Calibration origins** estimate an absolute-residual interval radius after selection.
- **Locked origins** provide the final, once-opened test. Their results are never used to choose a
  replacement method or improve the reported score.

## How to read the metrics

| Metric | Plain-language meaning |
|---|---|
| MAE | Average absolute miss in cumulative log HPI change; the primary point-error metric |
| RMSE | Similar to MAE but places more weight on unusually large misses |
| 90th-percentile absolute error | A tail-error threshold; 90% of absolute misses are smaller |
| Mean signed error | Average actual minus predicted change; negative values mean overprediction |
| R-squared | Squared-error improvement over predicting the evaluation-set mean |
| Empirical interval coverage | Share of locked outcomes falling inside the published interval |
| Mean interval width | How broad the uncertainty range is after converting it to annualized points |

No single metric is sufficient. A method can improve MAE but be biased, unstable across years, or
poorly calibrated. Counts and subgroup slices are retained for the same reason.

## Corrected validation evidence

Job 500 run `f51ad8ff85c44fe5bbd665b20520f6e4` evaluated only rows whose labels were available before
their validation origin. Cross-2020 features are allowed only for the governed stable-tract
cohort; valid FHFA targets are not discarded merely because an endpoint falls in a new decade.

| Horizon | Frozen method | Validation MAE | Validation RMSE | Main reason for selection |
|---|---|---:|---:|---|
| 1 year | Gradient-boosted trees | 0.0733 | 0.0929 | Best combined MAE, tail error, and balance across 2021-2022 |
| 3 years | State current trend | 0.0666 | 0.0896 | Clearly better overall than the fitted tree and linear model in 2017-2018 |

The one-year result was not uniform: state trend won 2021 and the tree won 2022. The three-year
result showed that a transparent market baseline could outperform more complex tract models in
development. Both points matter when interpreting the later locked test.

## Interval calibration

Job 504 used a 90% split-conformal absolute-residual interval. The one-year calibration origin had
41,017 observations and produced a cumulative-log radius of 0.1222. The three-year calibration
origin had 39,563 observations and produced a radius of 0.2675.

These are distribution-free residual intervals, but they are not timeless guarantees. Each
horizon has many tracts but only one independent calibration origin, so a market-regime change can
still break coverage.

## Locked-test results

| Horizon | Locked period | Observations | Champion MAE | Zero MAE | State-trend MAE | Coverage | Result |
|---|---|---:|---:|---:|---:|---:|---|
| 1 year | 2024-2025 | 42,082 | 0.0599 | 0.0627 | 0.0592 | 89.4% | Release gate passed |
| 3 years | 2022-2025 | 45,887 | 0.2943 | 0.1566 | 0.2943 | 48.2% | Release gate failed |

The one-year tree beats zero change, and its 89.4% coverage is close to the stated 90% level. The
state-trend baseline is slightly better on locked MAE, so the correct conclusion is not that the
tree dominates every simple method. The pre-frozen tree is retained and the state baseline is
shown beside it in the application.

The three-year method failed in a practically important way. Mean predicted cumulative log change
was 0.442, while mean observed change was 0.149. Persisting the unusually strong 2022 statewide
trend for three years caused systematic overprediction. The interval also captured fewer than
half of the outcomes.

## Release gate

Job 605 applies the same fixed minimum requirements to every horizon:

1. At least 1,000 locked observations.
2. Champion MAE no worse than zero-change MAE.
3. Empirical coverage no more than ten percentage points below the nominal interval coverage.

The gate does not search for a new model after reading the test. It publishes the one-year horizon
and records the three-year reasons as
`worse_than_zero_change_mae;interval_coverage_below_threshold`.

## Required interpretation slices

The scorecards retain results by Census region, held-out state role, stable versus post-2020
cohort, housing composition, ACS uncertainty, and origin year. The one-year locked result is
fairly consistent across these slices. The three-year failure appears across regions and cohorts,
which supports the regime-failure interpretation rather than a single geography bug.

## What the evidence supports

- A usable one-year forecast with an honestly evaluated uncertainty interval.
- A visible state-trend comparator rather than a claim that complexity always wins.
- Withholding the three-year forecast from the product.
- Reporting regime sensitivity as a substantive result.

It does not support an individual-home valuation, a causal neighborhood forecast, an investment
recommendation, or retuning the three-year method against the locked outcome.

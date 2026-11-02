# Figure 3: Forecast Bias and Tail Error

**File:** `03_forecast_bias_and_tail_error.png`

## Question

Do the state-trend and regularized-linear methods make systematically signed errors or have large
misses hidden by their average MAE?

## Construction

The left panel shows mean signed annualized error, defined as actual minus predicted change.
Positive values indicate underprediction. The right panel shows the 90th-percentile absolute error
on the cumulative log-change scale. Only state trend and regularized linear are shown because they
are the strongest simple multi-horizon comparator and fitted model in the current run.

## Current result

The one-year linear model underpredicts by about 2.74 annualized percentage points on average.
This is important even though it has the lowest one-year MAE.

## Limits

- Mean bias can hide offsetting positive and negative errors.
- A 90th percentile describes the tail threshold, not the single worst case.
- Annualized signed error and cumulative-log tail error use different but intentional scales.

**Source:** [`forecast_baseline_scorecard`](../../data/48_evaluation_forecast_baseline_scorecard.md)

**Residual convention:** [Forecasting module](../../forecasting/forecasting_module.md)

# Figure 1: Forecast Validation MAE by Model and Horizon

**File:** `01_forecast_mae_by_horizon.png`

## Question

Which implemented method has the lowest average absolute validation error at each horizon?

## Construction

The grouped bars use overall scorecard rows for all seven methods and the one-, three-, and
five-year horizons. Every method within a horizon is evaluated on the same governed validation
rows, with decade-crossing targets excluded. The vertical measure is mean absolute cumulative
log-change error; lower is better.

## Current result

In the November 7, 2026 validation run, gradient-boosted trees has the lowest MAE at one year
(0.0707) and three years (0.0721). Regularized linear is lowest at five years (0.1033), compared
with 0.1286 for the tree. The five-year result remains exploratory because only two training
origins and one validation origin support the fit.

## Interpretation limits

- Compare methods within a horizon, not raw cumulative errors across different horizon lengths.
- Lowest MAE does not establish calibration, low bias, or stable performance.
- These are validation results; locked temporal tests remain unopened.

**Source:** [`forecast_baseline_scorecard`](../../data/48_evaluation_forecast_baseline_scorecard.md)

**Related results:** [Forecast evaluation](../../forecasting/evaluation_and_results.md)

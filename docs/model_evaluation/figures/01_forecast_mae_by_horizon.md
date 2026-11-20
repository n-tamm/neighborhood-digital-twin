# Figure 1: Forecast Validation MAE by Model and Horizon

**File:** `01_forecast_mae_by_horizon.png`

## Question

Which implemented method has the lowest average absolute validation error at each horizon?

## Construction

The grouped bars use overall scorecard rows for all seven methods and the active one- and
three-year horizons. Every method within a horizon is evaluated on the same governed validation
rows, with decade-crossing targets excluded. The vertical measure is mean absolute cumulative
log-change error; lower is better.

## Current result

In the November 7, 2026 validation run, gradient-boosted trees has the lowest MAE at one year
(0.0707) and three years (0.0721). Earlier five-year results are excluded from active evaluation.

## Interpretation limits

- Compare methods within a horizon, not raw cumulative errors across different horizon lengths.
- Lowest MAE does not establish calibration, low bias, or stable performance.
- These are validation results from before finalization. Locked temporal-test results were opened
  later under the frozen model contract and are reported in the final forecast figure build.

**Source:** [`forecast_baseline_scorecard`](../../data/48_evaluation_forecast_baseline_scorecard.md)

**Related results:** [Forecast evaluation](../../forecasting/evaluation_and_results.md)

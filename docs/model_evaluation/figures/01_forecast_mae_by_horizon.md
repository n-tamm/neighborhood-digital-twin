# Figure 1: Forecast Validation MAE by Model and Horizon

**File:** `01_forecast_mae_by_horizon.png`

## Question

Which implemented method has the lowest average absolute validation error at each horizon?

## Construction

The grouped bars use overall scorecard rows for all six methods and the one-, three-, and
five-year horizons. Every method within a horizon is evaluated on the same governed validation
rows. The vertical measure is mean absolute cumulative log-change error; lower is better.

## Current result

Regularized linear is lowest at one year with MAE 0.0724, compared with 0.0757 for state trend. At
three years, state trend is narrowly lowest at 0.0666, compared with 0.0679 for linear. The
five-year linear MAE is 0.0952 but remains exploratory because only three training origins support
the fit.

## Interpretation limits

- Compare methods within a horizon, not raw cumulative errors across different horizon lengths.
- Lowest MAE does not establish calibration, low bias, or stable performance.
- These are validation results; locked temporal tests remain unopened.

**Source:** [`forecast_baseline_scorecard`](../../data/48_evaluation_forecast_baseline_scorecard.md)  
**Related results:** [Forecast evaluation](../../forecasting/evaluation_and_results.md)

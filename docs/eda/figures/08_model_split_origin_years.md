# Figure 8: Independent Forecast-Origin Years

**File:** `08_model_split_origin_years.png`

## Question

How many independent forecast-origin years support training, validation, calibration, and locked
testing for each horizon?

## Construction

The heatmap counts distinct `forecast_origin_year` values in each horizon and frozen temporal
role. It intentionally counts years rather than tract rows.

## Interpretation

The decade-safe split has nine one-year training origins, three three-year origins, and only two
five-year origins. One year is primary; five years remains especially exploratory. Millions of
repeated tract rows provide cross-sectional detail but do not create additional independent market
periods.

Calibration and locked-test cells show reserved data. Their presence in the assignment contract
does not mean those outcomes have been used for model choice.

## Limits

- The figure counts periods but does not show how different the economic conditions are among
  those periods.
- One origin can contain many tracts with spatially correlated outcomes.
- The five-year limitation cannot be solved by adding a more complex algorithm.

**Source contract:** [`gold_model_split_assignment`](../../data/44_gold_model_split_assignment.md)

**Detailed design:** [Forecast target and split design](../../forecasting/target_and_split_design.md)

# Figure 4: Forecast Accuracy in Development and Held-Out States

**File:** `04_forecast_geographic_transfer.png`

## Question

Does forecast error change in complete states excluded from model fitting?

## Construction

The heatmap compares MAE for state trend and regularized linear across the same validation periods
in development states and the four governed geographic holdouts: Maine, North Dakota, West
Virginia, and New Mexico. Rows are method-horizon combinations; columns are geographic roles.

## Interpretation

The figure is a transfer diagnostic. A large held-out gap would warn that a favorable overall
result depends on places used in training. Similar errors would be encouraging but would not prove
transfer to every U.S. market.

## Limits

- The holdouts are four relatively small states and do not represent every urban, rural, or metro
  setting.
- This is development evidence, not the locked temporal test.
- Counts and housing composition may differ between the two columns and should accompany the
  error comparison.

**Split design:** [Target and split design](../../forecasting/target_and_split_design.md)  
**Source:** [`forecast_baseline_scorecard`](../../data/48_evaluation_forecast_baseline_scorecard.md)

# Figure 7: Forecast Accuracy by Validation Origin

**File:** `07_forecast_temporal_stability.png`

## Question

Is the performance of state trend, regularized linear, and gradient-boosted trees consistent across
the independent forecast-origin years for the active horizons?

## Construction

Each panel corresponds to an active horizon and plots MAE by validation origin for the three
methods. A point summarizes many tract predictions but only one independent market origin.

## Interpretation

The figure prevents the national row count from being mistaken for temporal replication. A method
that wins overall but loses badly in one origin may be relying on a particular market period. The
one-year and three-year horizons each have two validation origins. Five-year results are not part
of the active evaluation.

## Limits

- Two origins provide only a basic stability check; one origin cannot establish stability.
- Tracts within an origin remain geographically and economically related.
- The locked-test origins are deliberately absent.

**Source:** [`forecast_baseline_scorecard`](../../data/48_evaluation_forecast_baseline_scorecard.md)

**Temporal design:** [Target and split design](../../forecasting/target_and_split_design.md)

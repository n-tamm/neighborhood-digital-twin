# Figure 5: One-Year Forecast Accuracy by Housing Composition

**File:** `05_forecast_housing_composition.png`

## Question

Does one-year forecast error vary with the proportion of tract housing represented by
single-family units?

## Construction

The grouped bars compare state-trend and regularized-linear MAE across the shared single-family
housing-share bands: under 25%, 25% to under 50%, 50% to under 75%, 75% or more, and missing when
present. The view is limited to the primary one-year horizon.

## Interpretation

Errors are higher in the under-25% single-family band. This reinforces the need to show housing
composition next to an FHFA-based forecast and to avoid describing the target as the entire local
housing market.

## Limits

- The figure does not distinguish whether the difference comes from target representativeness,
  feature relationships, history depth, or another correlated factor.
- Error is only calculated where a target exists; missing target coverage is a separate issue.
- The bands are based on estimated ACS shares and therefore carry sampling uncertainty.

**Coverage context:** [EDA housing-composition coverage](../../eda/figures/02_housing_composition_coverage.md)

**Source:** [`forecast_baseline_scorecard`](../../data/48_evaluation_forecast_baseline_scorecard.md)

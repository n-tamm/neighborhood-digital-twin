# Forecasting Module

**Code file:** [`src/neighborhood_twin/forecasting.py`](../../src/neighborhood_twin/forecasting.py)  
**Current schema version:** `1.2.0`

## Responsibility

The module contains reusable forecast logic. It validates the input contract, builds the five
fixed baselines, fits the horizon-specific regularized linear pipelines, adds readable prediction
and residual fields, and builds sliced evaluation scorecards. It does not read or write a
Databricks table directly; orchestration and publication belong to the notebook.

## Feature contract

`LINEAR_FEATURE_COLUMNS` is the authoritative ordered registry of 26 linear-model inputs.
`validate_feature_registry()` fails before fitting when the modeling panel does not contain every
required column. This prevents a silently changed feature set.

## Main functions

| Function | Responsibility |
|---|---|
| `cumulative_log_from_annual_rate` | Converts an annual percent rate into cumulative log change for a horizon |
| `annualized_rate_from_cumulative_log` | Converts cumulative log change into a readable annualized percentage |
| `housing_composition_band` | Applies the shared single-family-share bands used in evaluation |
| `acs_uncertainty_band` | Bands the largest available relative MOE among income, value, and rent |
| `baseline_predictions` | Produces the five fixed-rule predictions on observed validation rows |
| `_linear_model_predictions` | Fits one training-only Spark ML pipeline per horizon and scores validation rows |
| `_add_prediction_fields` | Adds annualized values, residuals, slices, schema version, run ID, and build time |
| `build_forecast_scorecard` | Aggregates overall and subgroup metrics and joins zero-change skill references |
| `build_forecast_baseline_run` | Reconciles the complete run and returns prediction and scorecard DataFrames |

Private functions are implementation details even though they are documented here. External code
should call `build_forecast_baseline_run()` rather than assembling a partial pipeline.

## Linear Spark pipeline

For each horizon, `_linear_model_predictions()` selects rows that are both
`eligible_for_point_model_fit` and target-observed, then fits:

```text
Median Imputer
    -> Vector Assembler
    -> Standard Scaler (center and scale)
    -> L2-Regularized Linear Regression
```

The same fitted pipeline transforms the validation rows. The scaler uses `withMean=True` and
`withStd=True`; the regression disables a second internal standardization step.

## Prediction and residual conventions

The signed residual is `target - prediction`. Positive mean residual therefore means the model
underpredicts, while negative means it overpredicts. Both cumulative-log and annualized-percentage
versions are retained. Absolute errors are added once at row level so every scorecard slice uses
the same definition.

## Scorecard slices

The module aggregates overall performance and the following dimensions:

- modeling cohort;
- held-out versus development states;
- housing-composition band;
- state and Census region;
- forecast-origin year; and
- ACS uncertainty band.

Each scorecard row records observation and distinct-tract counts. Those counts are necessary for
interpreting small state or subgroup results, but they do not replace the number of independent
forecast-origin years.

## Safety checks

- The input feature registry must be complete.
- A negative regularization parameter is rejected.
- Locked-evaluation flags must agree with the frozen split contract.
- Published predictions are rejected if any non-validation temporal role appears.
- A run fails if no horizon can be fit.

## Testing boundary

Unit tests cover pure conversions and contract behavior where possible. Full Spark model fitting
and publication run in Databricks because local Python is not intended to reproduce the national
Spark environment.

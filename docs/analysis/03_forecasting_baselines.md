# Forecasting Baselines

The current forecast workflow asks a deliberately narrow question: can tract history and public
neighborhood context improve on simple expectations about future FHFA single-family HPI change?
It establishes a fair benchmark before the team considers a nonlinear model or publishes any
forecast in the application.

These are development results. The workflow does not use calibration rows, open the locked
temporal tests, calibrate uncertainty, or publish an application-serving model.

## Prediction target

For each tract, forecast-origin year, and horizon, the target is cumulative log change:

```text
target = log(HPI at origin + horizon / HPI at origin)
```

In simple terms, the model predicts how much the tract's measured single-family HPI changes over
the next one, three, or five years. A positive value means the index increased and a negative
value means it decreased. The application can convert a model output to an annualized percentage:

```text
annualized change (%) = (exp(predicted log change / horizon) - 1) * 100
```

The target is not a home price, a forecast for every property type, or a causal estimate of what
would happen under an intervention.

## Implemented methods

All six methods predict the same target and are compared on the same validation population.

| Method | What it predicts | Why it is included |
|---|---|---|
| `zero_change` | No HPI movement | Establishes the simplest error and skill reference |
| `latest_change_persistence` | The latest one-year tract change continues for the full horizon | Tests short-term momentum |
| `recent_three_year_mean` | The tract's recent three-year mean annual change continues | Smooths a single unusually strong or weak year |
| `county_current_trend` | The current county mean annual change continues | Tests whether local market context is enough |
| `state_current_trend` | The current state mean annual change continues | Provides a broad and interpretable regional baseline |
| `regularized_linear` | A fitted combination of 26 tract, regional, ACS, and quality features | Tests whether a modest multivariable model improves on the fixed rules |

The five fixed methods do not learn coefficients. Their prediction is computed directly from the
point-in-time row. The regularized linear method is fit separately for each horizon, so the
one-year model does not recursively feed its predictions into the three- or five-year model.

## Linear model pipeline

The linear workflow is a Spark ML pipeline fit only on rows marked
`eligible_for_point_model_fit` with an observed target. For each horizon it performs:

1. median imputation learned from the training rows;
2. assembly of the 26 approved numeric features;
3. centering and standardization learned from the training rows; and
4. linear regression with L2 regularization (`regParam = 0.05`, `elasticNetParam = 0.0`) and a
   maximum of 100 iterations.

L2 regularization shrinks unstable coefficients toward zero without removing a feature entirely.
This is useful when housing and affordability measures overlap, but it does not make the model
nonlinear or prove that a coefficient is causal.

### Feature families

| Family | Implemented inputs |
|---|---|
| HPI level and history | Origin annual change; 1-, 3-, and 5-year changes; recent 3-year mean; recent 5-year volatility; history observation and gap counts |
| Regional market context | County and state mean annual change at the origin |
| Population and housing supply | Total population and housing units |
| Occupancy and tenure | Occupancy, vacancy, owner-occupancy, and renter-occupancy rates |
| Housing structure | Single-family, multifamily, and mobile-home shares |
| Affordability and value | Median household income, owner-occupied value, and gross rent |
| Data quality and timing | ACS measurement age and relative margins of error for income, value, and rent |

The source list is fixed in
[`LINEAR_FEATURE_COLUMNS`](../../src/neighborhood_twin/forecasting.py). The model uses raw
point-in-time values from the gold panel; imputation and scaling are not precomputed across future
or evaluation rows.

## Training and validation sequence

```text
gold_modeling_panel
        |
        +--> preassigned training rows --> fit imputer, scaler, and one linear model per horizon
        |
        +--> preassigned validation rows --> six predictions on identical eligible rows
                                              |
                                              v
                                  residuals and sliced scorecard
```

The split is based on forecast-origin years rather than a random tract-row split. One-year
validation uses 2021 and 2022 origins, three-year validation uses 2017 and 2018, and five-year
validation uses 2014. Maine, North Dakota, West Virginia, and New Mexico provide a geographic
transfer slice. The model is still selected on validation evidence; this held-out-state slice is
not a substitute for the unopened final temporal test.

Only validation predictions are published. The output contains 1,369,401 rows across 59,562
tracts and six methods. The training rows, calibration origins, and locked-test predictions are
not copied into the prediction table.

## Evaluation measures

No single number determines whether the model is useful.

| Measure | Plain-language interpretation |
|---|---|
| MAE | Average absolute miss on the cumulative log-change scale. This is the primary comparison because it is less dominated by extreme errors than RMSE. |
| RMSE | Similar to MAE but gives larger misses more weight. A large MAE/RMSE gap points to a tail-error problem. |
| Median absolute error | The typical miss. It can remain small even when a subset of places performs poorly. |
| 90th-percentile absolute error | A threshold below which 90% of absolute errors fall. It surfaces bad-tail behavior. |
| Mean signed error | Average actual minus predicted change. Positive values indicate underprediction; negative values indicate overprediction. |
| Annualized percentage-point error | The error transformed to a more readable yearly rate. It should not be confused with a percent error in a property's price. |
| R-squared | Improvement in squared error relative to predicting the validation target mean. Negative values mean the model is worse than that mean benchmark on this measure. |
| Skill versus zero change | `1 - model error / zero-change error`. Positive values improve on zero change; zero ties it; negative values are worse. |
| Directional lift | Direction accuracy minus the accuracy of always choosing the majority direction. It prevents a mostly rising market from making an uninformative model look strong. |

The scorecard repeats these measures overall and by forecast-origin year, stable versus broad
cohort, Census region, held-out versus development state, housing-composition band, ACS
uncertainty band, and state. These slices check whether a favorable average hides a population
where the target is less representative or the model transfers poorly.

## Current validation results

| Horizon | Lowest current MAE | Interpretation |
|---|---|---|
| 1 year | Regularized linear: 0.0724 | Best current one-year average absolute error; state trend is close at 0.0757 |
| 3 years | State trend: 0.0666 | The simple state baseline narrowly beats the linear model at 0.0679 |
| 5 years | Regularized linear: 0.0952 | Exploratory because only three independent training origins support the fit |

The one-year linear result improves MAE by about 39% over zero change, but its R-squared is
negative and it underpredicts by about 2.74 annualized percentage points on average. Those facts
are not contradictory: it can reduce absolute error relative to zero while still missing
cross-sectional variation and carrying systematic bias.

Raw directional accuracy is not useful evidence here. Approximately 90.2% of one-year targets
and more than 97% of longer-horizon targets are positive. A model can exceed 90% accuracy simply
by predicting increases almost everywhere, and the implemented methods add almost no lift over
that majority rule.

The current results support continued one-year model work, a cautious three-year comparison, and
only a simple exploratory five-year result. They do not yet identify a champion model.

## Outputs and reproducibility

- Workflow: `500 Modeling | Forecast Baselines`
- Implementation: [`forecasting.py`](../../src/neighborhood_twin/forecasting.py)
- Databricks notebook:
  [`01_run_forecast_baselines.py`](../../notebooks/05_modeling/01_run_forecast_baselines.py)
- Prediction table:
  [`workspace.neighborhood_twin_model.forecast_baseline_prediction`](../data/47_model_forecast_baseline_prediction.md)
- Scorecard table:
  [`workspace.neighborhood_twin_evaluation.forecast_baseline_scorecard`](../data/48_evaluation_forecast_baseline_scorecard.md)
- MLflow experiment: `/Shared/neighborhood-digital-twin/forecast-baselines`

MLflow records the target, evaluation role, regularization value, feature registry, run ID, and
overall validation metrics. The Delta outputs carry the same run ID so a score or figure can be
traced to its source experiment.

## Current boundaries

- The locked temporal tests have not been opened.
- Prediction intervals and calibration metrics have not been implemented.
- A nonlinear forecast candidate and feature-family ablations have not been implemented.
- True tract-neighbor features are not present because the current geometry is display-only.
- The prediction table is a development artifact, not a serving contract for the application.

# Gradient-Boosted-Tree Forecast Challenger

## Decision

Add a fixed-parameter Spark ML `GBTRegressor` as a development challenger beside the existing
fixed baselines and regularized linear model. The candidate is fit independently for each forecast
horizon and predicts cumulative log change in tract FHFA single-family HPI. It is not a selected
champion, a production model, or an application forecast.

The initial configuration is intentionally small and fixed: maximum depth 4, 50 boosting
iterations, step size 0.05, subsampling rate 0.8, and seed 699. This is a focused comparison, not
hyperparameter search. Do not tune against the locked temporal test.

## Data and leakage controls

- Read the existing `gold_modeling_panel` and the frozen split assignments.
- Fit only on observed targets marked `eligible_for_point_model_fit`; that flag restricts training
  to the temporal training role and development geographies.
- Require the forecast origin and target endpoint to fall in the same calendar decade; crossing
  targets are explicitly censored and cannot enter training or evaluation.
- Fit median imputation on each horizon's training fold, then apply it to validation rows.
- Use only the registered point-in-time `LINEAR_FEATURE_COLUMNS`; do not include keys, target
  values, split flags, or future observations as predictors.
- Score only observed validation rows. Do not score calibration or locked temporal-test rows in
  this development workflow.
- Preserve the validation-only prediction and sliced scorecard contracts. Compare methods on the
  same available rows and against the fixed zero-change reference.

## Evaluation and promotion gate

The primary horizon is one year; three years is secondary and five years exploratory. Review MAE
first, then RMSE, signed bias, tail error, geographic transfer, temporal stability, cohort and
housing-composition slices, and coverage. Directional accuracy must be interpreted alongside its
majority-direction reference. An improvement on a single aggregate metric is not sufficient to
promote a candidate.

The first decade-safe validation run (Nov 7, 2026; forecast run ID
`a53368b80ebc4cbaa05992d5a3356500`) produced these overall results:

| Horizon | Origin year(s) | Observations | GBT MAE | GBT RMSE | MAE skill vs zero | RMSE skill vs zero | Signed bias |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 year | 2021-2022 | 101,703 | 0.070714 | 0.090240 | 40.4% | 35.4% | 0.030564 |
| 3 years | 2014-2015 | 83,254 | 0.072093 | 0.093268 | 56.3% | 51.9% | -0.017595 |
| 5 years | 2013 | 42,274 | 0.128631 | 0.160293 | 52.5% | 49.5% | -0.080170 |

The candidate has the lowest MAE and RMSE at one and three years. At five years, regularized linear
is better (MAE 0.103251; RMSE 0.133171), and the boosted-tree result is exploratory because only
two independent training origins and one validation origin are available. The tree beats the
strongest simple baseline in MAE and RMSE at all horizons, but that does not make it the five-year
winner. Signed bias is `target - prediction`, so positive values indicate underprediction. These
metrics are evidence for continued evaluation, not a model-selection or promotion decision.

Do not select or register a champion based solely on these validation results. Feature-family
ablations, uncertainty calibration, a preregistered selection rule, and a separately authorized
locked-test evaluation remain future work.

## Scope boundary

This decision changes only the forecasting workflow and forecast evaluation diagnostics. It does
not modify the similarity workflow, its inputs, matching logic, outputs, or evaluation.

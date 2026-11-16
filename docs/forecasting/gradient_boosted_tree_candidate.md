# Gradient-Boosted-Tree Forecast Challenger

## Decision

Use Spark ML `GBTRegressor` as a development challenger beside the existing fixed baselines and
regularized linear model. The candidate is fit independently for the active one- and three-year
forecast horizons and predicts cumulative log change in tract FHFA single-family HPI. Its depth
and iteration count are selected with a bounded, training-only expanding-origin search when there
are enough purge-safe folds. It is not a selected champion, a production model, or an application
forecast.

The search compares `(maxDepth, maxIter)` pairs `(2, 30)`, `(2, 50)`, `(4, 30)`, `(4, 50)`,
`(6, 30)`, and `(6, 50)`. Step size (0.05), subsampling rate (0.8), and seed (699) are held fixed;
the existing `(4, 50)` configuration is included as a reference. The objective is the unweighted
mean MAE across the most recent three eligible training-origin folds. Shallower trees and fewer
iterations win exact MAE ties. Do not tune against frozen validation, calibration, or locked-test
outcomes.

## Data and leakage controls

- Read the existing `gold_modeling_panel` and the frozen split assignments.
- Fit only on observed targets marked `eligible_for_point_model_fit`; that flag restricts training
  to the temporal training role and development geographies.
- Require the forecast origin and target endpoint to fall in the same calendar decade; crossing
  targets are explicitly censored and cannot enter training or evaluation.
- Fit median imputation on each horizon's training fold, then apply it to validation rows.
- Within training, evaluate each candidate on the held-out origin year after fitting only on
  earlier origins whose target endpoint is strictly before that fold's origin year. This purges
  overlapping outcome windows as well as preventing future-origin features from entering a fold.
- Require at least two nonempty, purge-safe temporal folds to select parameters. If a horizon has
  fewer folds, retain the original depth-4/50-iteration settings and record that tuning was
  skipped; do not substitute random row folds or the frozen validation set.
- Use only the registered point-in-time `LINEAR_FEATURE_COLUMNS`; do not include keys, target
  values, split flags, or future observations as predictors.
- Score only observed validation rows. Do not score calibration or locked temporal-test rows in
  this development workflow.
- Preserve the validation-only prediction and sliced scorecard contracts. Compare methods on the
  same available rows and against the fixed zero-change reference.

## Evaluation and promotion gate

The primary horizon is one year and three years is secondary. Five-year results from earlier
exploratory runs are excluded from active model comparisons. Review MAE first, then RMSE, signed
bias, tail error, geographic transfer, temporal stability, cohort and housing-composition slices,
and coverage. Directional accuracy must be interpreted alongside its majority-direction
reference. An improvement on a single aggregate metric is not sufficient to promote a candidate.

The November 13, 2026 run (`5005b56099074eb897988c44b472f654`) found three purge-safe one-year folds:
2017, 2018, and 2020. The mean fold MAE for each candidate was:

| Max depth | Iterations | Expanding-origin CV MAE |
|---:|---:|---:|
| 2 | 30 | 0.051933 |
| **2** | **50** | **0.051742** |
| 4 | 30 | 0.052117 |
| 4 | 50 | 0.052070 |
| 6 | 30 | 0.052192 |
| 6 | 50 | 0.052114 |

Depth 2 with 50 iterations was selected for the one-year model. The active three-year horizon does
not produce two nonempty, purge-safe folds, so it retains the original depth-4/50-iteration
settings. This fallback setting is not a tuned result.

The tuned model's validation results are below. The one-year regularized-linear comparator has
MAE 0.071993 and RMSE 0.091062; at three years the GBT leads both metrics.

| Horizon | Origin year(s) | Observations | GBT MAE | GBT RMSE | MAE skill vs zero | RMSE skill vs zero | Mean signed error |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 year | 2021-2022 | 101,703 | 0.071727 | 0.091479 | 39.6% | 34.5% | 0.029120 |
| 3 years | 2014-2015 | 83,254 | 0.072093 | 0.093268 | 56.3% | 51.9% | -0.017595 |

Compared with the prior fixed depth-4/50-iteration one-year GBT (MAE 0.070714; RMSE 0.090240),
the CV-selected model scored slightly worse on the untouched validation years. That result is
reported rather than used to retune against validation. Positive mean signed error is
`target - prediction`, indicating underprediction. These metrics are validation evidence, not a
model-selection or promotion decision. Historical five-year scorecard rows remain archived but
are not used in current candidate decisions.

Do not select or register a champion based solely on these validation results. Feature-family
ablation results below are exploratory training-CV evidence only; uncertainty calibration, a
preregistered selection rule, and a separately authorized locked-test evaluation remain future
work.

### Feature-family ablation (training CV)

A separate one-year analysis dropped one registered feature family at a time from the 26-feature
model and compared it with the full model. It used the already selected depth-2/50-iteration
settings, the same three purged training-origin folds (2017, 2018, and 2020), and fold-specific
median imputation. Each variant scored the same 40,923, 40,959, and 44,116 held-out rows,
respectively. The table reports the unweighted mean of the three fold MAEs; positive deltas mean
that removing the family worsened MAE.

| Inputs | Features | Mean fold MAE | Delta vs. full |
|---|---:|---:|---:|
| Full feature set | 26 | 0.051742 | — |
| Drop HPI history | 18 | 0.054092 | +0.002350 |
| Drop regional context | 24 | 0.053190 | +0.001448 |
| Drop community scale | 24 | 0.051742 | 0.000000 |
| Drop occupancy and tenure | 22 | 0.051777 | +0.000035 |
| Drop housing structure | 23 | 0.051742 | 0.000000 |
| Drop affordability | 23 | 0.051683 | -0.000058 |
| Drop data timing and quality | 22 | 0.051742 | 0.000000 |

Removing HPI history or regional context produced the clearest deterioration. The tiny apparent
improvement from dropping affordability (0.000058 MAE) is not sufficient evidence to remove that
family; the other three unchanged results indicate no measured change on these folds, not that
those features are generally uninformative. Retain the full feature set for now.

This is not an independent estimate: these folds also selected the depth and iteration settings,
and the full-feature MAE equals that selection objective. The ablation did not read frozen
validation, calibration, or locked-test outcomes and did not write forecast predictions or
scorecards. The Databricks notebook is
[07_run_forecast_feature_ablation.py](../../notebooks/05_modeling/07_run_forecast_feature_ablation.py);
the one-time run was `49049616857892` and its MLflow run was
`b94172fcb75a4f4fb34c411470640915`.

## Scope boundary

This decision changes only the forecasting workflow and forecast evaluation diagnostics. It does
not modify the similarity workflow, its inputs, matching logic, outputs, or evaluation.

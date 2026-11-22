# Two-Model Finalization and Interval Contract

The forecasting project has two supervised approaches: L2-regularized linear regression and
gradient-boosted trees. Both models are fit independently at the one- and three-year horizons.
Zero change, persistence, recent growth, county trend, and state trend are baselines used to
interpret performance. A baseline is never substituted for either project model.

## Frozen model specifications

| Horizon | Model | Settings |
|---|---|---|
| 1 year | Regularized linear | L2 parameter 0.05, standardized inputs, 100 maximum iterations |
| 1 year | Gradient-boosted trees | Depth 2, 50 iterations, step size 0.05, subsampling 0.8, seed 699 |
| 3 years | Regularized linear | L2 parameter 0.05, standardized inputs, 100 maximum iterations |
| 3 years | Gradient-boosted trees | Depth 4, 30 iterations, step size 0.05, subsampling 0.8, seed 699 |

The settings were established from the training and validation workflow. Later-period outcomes
must not be used to tune these parameters.

## Why both models remain in the project

The linear model provides a readable additive comparison and is less flexible. The boosted-tree
model can learn nonlinear relationships and interactions among the same point-in-time features.
Showing both lets the report and application answer a useful question: does added flexibility
meaningfully improve the forecast, and does that answer change between one and three years?

Validation MAE favored the tree among the two project models at both horizons: 0.0733 versus
0.0766 at one year, and 0.0807 versus 0.1033 at three years. The state-trend baseline achieved
0.0666 at three years. That is important evidence that the three-year task is difficult and that
tract features did not beat a broad market rule in that development period. It does not convert
the state trend into the project's model.

## Model-specific intervals

Job 504 estimates a 90% split-conformal absolute-residual interval separately for each model and
horizon:

1. Fit the frozen model using development-state labels whose endpoints occur before the reserved
   calibration origin.
2. Score the calibration origin without changing the model or its parameters.
3. Calculate the finite-sample-corrected 90th percentile of absolute calibration residuals for
   that model and horizon.
4. Add and subtract the radius from later-period and current predictions.
5. Measure empirical coverage and interval width overall and across the declared evaluation
   slices.

The interval uses held-out residuals rather than training error and does not assume normally
distributed residuals. Its main limitation is temporal: each horizon has many tracts but only one
independent calibration origin. It is therefore a calibrated uncertainty range, not a guarantee
or a complete probability distribution.

## Later-period evaluation and warnings

MAE, RMSE, signed error, 90th-percentile absolute error, interval coverage, and interval width are
calculated for each of the four model-horizon combinations. Zero-change and state-trend errors are
retained beside them as benchmarks. The threshold record flags whether a result has at least
1,000 observations, MAE no worse than zero change, and coverage within ten percentage points of
the 90% target.

Missing a threshold creates an application warning; it does not delete the forecast or promote a
baseline. The app publishes both supervised model outputs for every model-ready tract at both
horizons so users can compare the models and understand weak evidence directly.

## Correction recorded on November 22, 2026

An earlier finalization configuration selected one method per horizon and incorrectly configured
`state_current_trend` as the three-year champion. That treated a strong validation baseline as if
it were one of the project's forecasting models and caused the three-year supervised outputs to
be absent from serving. Version 2 corrects the contract by carrying both supervised models through
calibration, evaluation, current scoring, and application serving. The prior state-trend result
remains useful baseline evidence but is not described as a linear or nonlinear model result.

Because the 2022–2025 and 2024–2025 outcomes have already been inspected, the corrected comparison
must not be called a new untouched model-selection test. The specifications were fixed before the
correction and are not tuned from those outcomes. A genuinely new untouched three-year test will
require a later observed endpoint.

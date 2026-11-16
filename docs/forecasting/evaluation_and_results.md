# Forecast Evaluation and Current Results

## Metric definitions

| Metric | Interpretation |
|---|---|
| MAE | Average absolute miss in cumulative log change; primary method comparison |
| RMSE | Root mean squared miss; reacts more strongly to large errors |
| Median absolute error | Typical absolute miss |
| 90th-percentile absolute error | Tail threshold below which 90% of absolute misses fall |
| Mean signed error | Average actual minus predicted change; positive means underprediction |
| Annualized error | Error transformed into annual percentage points for readability |
| R-squared | Squared-error improvement over predicting the validation target mean |
| Skill versus zero | `1 - candidate error / zero-change error`; positive values improve on zero |
| Directional lift | Directional accuracy minus an always-majority-direction rule |

These metrics answer different questions. A method can improve MAE relative to zero change while
having negative R-squared or systematic bias. Selection therefore cannot use one number.

Active model evaluation now includes only one- and three-year horizons. Five-year results from
earlier exploratory runs are excluded from current comparisons and reports; their original
scorecard records remain historical artifacts.

## Current decade-safe validation results

The latest published scorecard, built November 13, 2026
(`5005b56099074eb897988c44b472f654`), evaluates target windows whose origin and endpoint are in
the same calendar decade. The active validation origins are 2021-2022 (one year) and 2014-2015
(three years). The GBT uses the training-only tuning procedure described in the
[candidate design](gradient_boosted_tree_candidate.md); no validation or locked-test outcome was
used to select its parameters.

| Horizon | Lowest MAE | Lowest RMSE | Observations | Interpretation |
|---|---|---|---:|---|
| 1 year | Gradient-boosted trees: 0.0717 | Regularized linear: 0.0911 | 101,703 | GBT has marginally lower MAE; linear has lower RMSE. |
| 3 years | Gradient-boosted trees: 0.0721 | Gradient-boosted trees: 0.0933 | 83,254 | Only three training origins; the GBT retains fixed parameters because there are not enough purged tuning folds. |

GBT improves over zero-change MAE by 39.6% and 56.3% at one and three years. For the newly tuned
one-year model, MAE is slightly worse than the prior fixed depth-4/50-iteration GBT (0.0717 versus
0.0707), and its RMSE (0.0915) is also slightly worse (previously 0.0902). The one-year validation
result therefore does not show an improvement from tuning; validation remains an evaluation set,
not a basis for another parameter choice.

Mean signed log error (`actual - prediction`) for the tree is +0.0291 at one year and -0.0176 at
three years. Positive values indicate underprediction. These are validation findings, not a
champion decision or an estimate from the locked temporal test.

## Directional accuracy

Approximately 90.2% of one-year validation outcomes are positive and 94.6% at three years. Raw
directional accuracy is consequently high for the active methods, while lift over the
majority-direction rule is near zero. Direction accuracy alone is not evidence that the model
distinguishes which tracts will appreciate.

## Required interpretation slices

Review overall metrics alongside:

- forecast-origin year, which reveals temporal instability;
- held-out versus development states, which tests geographic transfer;
- stable versus broad geography cohort;
- single-family housing-share band;
- ACS uncertainty band;
- Census region and state; and
- observation and tract counts.

The [model-evaluation figure documentation](../model_evaluation/README.md) explains each current
diagnostic separately.

The published evaluation figures have not yet been rerendered from the November 13 tuned run; the
metrics above are from the current scorecard, while those visual diagnostics still reflect the
prior forecast build.

## What the current run establishes

- The tree has the lowest validation MAE at one and three years and the lowest RMSE at three
  years; regularized linear has the lowest one-year RMSE.
- All compared target windows remain within a calendar decade; cross-decade targets are censored
  and excluded from fitting and validation.
- Directional accuracy has little lift over the majority-direction baseline.
- Results do not justify promoting a champion or opening the locked temporal test.

## What it does not establish

- A separate one-year feature-family ablation used training-only temporal folds; it did not alter
  the published validation scorecard or justify removing any feature family. See the
  [training-CV results](gradient_boosted_tree_candidate.md#feature-family-ablation-training-cv).
- No prediction interval has been calibrated.
- No champion has been frozen.
- No locked temporal test has been opened.
- No forecast has been approved for application serving.

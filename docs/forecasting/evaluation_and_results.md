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

## Current decade-safe validation results

The November 7, 2026 run (`a53368b80ebc4cbaa05992d5a3356500`) evaluates only target windows whose
origin and endpoint are in the same calendar decade. Validation origins are 2021-2022 (one year),
2014-2015 (three years), and 2013 (five years).

| Horizon | Lowest MAE | RMSE | Observations | Interpretation |
|---|---|---:|---:|---|
| 1 year | Gradient-boosted trees: 0.0707 | 0.0902 | 101,703 | Best validation MAE and RMSE; nine training origins |
| 3 years | Gradient-boosted trees: 0.0721 | 0.0933 | 83,254 | Best validation MAE and RMSE; only three training origins |
| 5 years | Regularized linear: 0.1033 | 0.1332 | 42,274 | Exploratory; only two training origins and one validation origin |

Gradient-boosted trees improve over zero-change MAE by 40.4%, 56.3%, and 52.5% for the one-,
three-, and five-year horizons. At five years, regularized linear is better than the tree (MAE
0.1033 versus 0.1286). The tree is therefore not a universal winner.

Signed annualized error for the tree is +3.77 percentage points at one year, -0.59 at three years,
and -1.67 at five years. Positive values mean underprediction. These are validation findings, not
a champion decision or an estimate from the locked temporal test.

## Directional accuracy

Approximately 90.2% of one-year validation outcomes are positive, 94.6% at three years, and 97.3%
at five years. Raw directional accuracy is consequently high for the active methods, while lift
over the majority-direction rule is near zero. Direction accuracy alone is not evidence that the
model distinguishes which tracts will appreciate.

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

## What the current run establishes

- The tree has the lowest validation MAE and RMSE at one and three years.
- Regularized linear is better at five years, where evidence is especially temporally thin.
- All compared target windows remain within a calendar decade; cross-decade targets are censored
  and excluded from fitting and validation.
- Directional accuracy has little lift over the majority-direction baseline.
- Results do not justify promoting a champion or opening the locked temporal test.

## What it does not establish

- No feature-family ablation has been evaluated.
- No prediction interval has been calibrated.
- No champion has been frozen.
- No locked temporal test has been opened.
- No forecast has been approved for application serving.

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
having negative R-squared and systematic bias. Selection therefore cannot use one number.

## Current overall validation results

| Horizon | Lowest MAE | Current interpretation |
|---|---|---|
| 1 year | Regularized linear: 0.0724 | Best current average absolute error; state trend is close at 0.0757 |
| 3 years | State trend: 0.0666 | Simple state context narrowly beats linear at 0.0679 |
| 5 years | Regularized linear: 0.0952 | Exploratory because only three training origins support the fit |

The one-year linear model improves MAE by about 39% over zero change, but its R-squared is negative
and its mean signed annualized error shows underprediction of about 2.74 percentage points. It is
the strongest current MAE baseline, not a frozen champion.

## Directional accuracy

Approximately 90.2% of one-year validation outcomes are positive. The positive share is roughly
97.8% and 98.1% at three and five years. Raw directional accuracy above 90% can therefore be
achieved without distinguishing tracts. The implemented methods add almost no directional lift
over that majority rule, so raw direction accuracy is not evidence of useful classification.

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

- A modest linear model improves one-year MAE over fixed baselines.
- State trend remains a strong comparator and is best at three years.
- Average error alone hides one-year underprediction and weak squared-error fit.
- Directional accuracy is dominated by the positive target base rate.
- Five-year evidence is too temporally thin for a strong product claim.

## What it does not establish

- No nonlinear candidate or feature-family ablation has been evaluated.
- No prediction interval has been calibrated.
- No champion has been frozen.
- No locked temporal test has been opened.
- No forecast has been approved for application serving.

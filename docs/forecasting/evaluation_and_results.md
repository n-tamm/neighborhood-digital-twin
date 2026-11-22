# Forecast Evaluation and Results

## What is being evaluated

The target is cumulative log change in FHFA single-family tract HPI from a forecast origin to its
future endpoint. One year is the primary horizon. Three years is secondary and has fewer
independent historical origins.

The project evaluates two supervised models at both horizons:

- L2-regularized linear regression; and
- gradient-boosted trees.

Five simple methods—zero change, latest-change persistence, recent three-year mean, county trend,
and state trend—are baselines. They help show whether the supervised models add value; they are not
application replacements for those models.

## Evidence sequence

- **Training folds** fit and tune without reading validation outcomes.
- **Validation origins** compare both supervised models and all baselines during development.
- **Calibration origins** estimate model- and horizon-specific interval radii.
- **Later evaluation origins** test fixed specifications under later market conditions.
- **Current scoring** refits the fixed specifications using labels available before the 2025
  origin and generates current one- and three-year forecasts.

The later evaluation periods were originally opened under an incorrect one-champion-per-horizon
serving design. The corrected workflow scores both already specified supervised models without
retuning. These outcomes must not be described as a new untouched selection set.

## How to read the metrics

| Metric | Plain-language meaning |
|---|---|
| MAE | Average absolute miss in cumulative log HPI change; the primary error metric |
| RMSE | Similar to MAE but gives unusually large misses more weight |
| 90th-percentile absolute error | A tail-error threshold; 90% of absolute misses are smaller |
| Mean signed error | Average actual minus predicted change; negative values mean overprediction |
| R-squared | Squared-error improvement over predicting the evaluation-set mean |
| Empirical interval coverage | Share of later outcomes inside the model's calibrated interval |
| Mean interval width | Typical breadth of the annualized uncertainty range |

No single metric is enough. A model can have a reasonable MAE while remaining biased, unstable
across origins, weak in held-out states, or poorly calibrated.

## Validation results

Job 500 run `f51ad8ff85c44fe5bbd665b20520f6e4` used only labels available before each validation
origin. The supervised-model comparison is:

| Horizon | Model | Validation MAE | Validation RMSE |
|---|---|---:|---:|
| 1 year | Gradient-boosted trees | 0.0733 | 0.0929 |
| 1 year | Regularized linear | 0.0766 | 0.0954 |
| 3 years | Gradient-boosted trees | 0.0807 | 0.1032 |
| 3 years | Regularized linear | 0.1033 | 0.1290 |

The tree has the lower validation error among the two project models at both horizons. The
state-trend baseline has a three-year MAE of 0.0666, lower than either supervised model in this
development period. The correct interpretation is that broad market momentum was difficult to
beat at three years—not that state trend became the project's nonlinear or linear model.

## Evaluation thresholds

Job 605 records three checks separately for every model-horizon pair:

1. at least 1,000 later-period observations;
2. model MAE no worse than zero-change MAE; and
3. empirical coverage no more than ten percentage points below the nominal 90% interval.

A missed check produces an evaluation warning in the app. It does not suppress the result or
promote a baseline. This keeps poor performance visible and lets users compare the two actual
models honestly.

## Required slices

The scorecards retain results by Census region, held-out-state role, stable versus post-2020
cohort, housing composition, ACS uncertainty, and origin year. Counts accompany every slice. The
report should emphasize overall results first and use slices to identify where a model is less
reliable or where apparent performance depends on geography or data quality.

## What the evidence can support

The workflow can support a tract-level single-family HPI forecast, comparison of linear and
nonlinear behavior, calibrated uncertainty ranges, and transparent baseline context. It does not
support an individual-home valuation, a forecast of all housing types, a causal claim about why a
neighborhood changed, or an investment recommendation.

The exact version-2 later-period metrics and serving counts must be added here after jobs 504, 605,
606, and 701 complete successfully under the corrected two-model contract.

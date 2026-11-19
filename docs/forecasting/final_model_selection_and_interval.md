# Final Model Selection and Interval Contract

This decision was frozen from job 500 validation evidence on November 19, 2026, before job 504
read calibration outcomes or opened either locked temporal test. The source MLflow run is
`f51ad8ff85c44fe5bbd665b20520f6e4`.

## Frozen choices

| Horizon | Selected method | Frozen settings |
|---|---|---|
| 1 year | Gradient-boosted trees | depth 2, 50 iterations, step size 0.05, subsampling 0.8, seed 699 |
| 3 years | State current trend | Directly carries the origin-year statewide mean annual FHFA HPI change across the horizon |

The project does not require both horizons to use the same model family. Each horizon answers a
different forecasting problem and has different historical support.

## One-year decision

The one-year tree had the lowest overall MAE (0.07326), RMSE (0.09289), and 90th-percentile
absolute error (0.14887). Regularized linear had MAE 0.07660 and RMSE 0.09543. State trend had MAE
0.07567 and RMSE 0.09844. The tree therefore improves on linear by about 4.4% in MAE and also
reduces the larger misses.

The result is not uniform across time. State trend is best in the 2021 validation origin, while
the tree is best in 2022. The tree's origin-level MAE varies from 0.08142 to 0.06321; state trend
varies more sharply from 0.05658 to 0.09916. The tree is selected because it has the better
combined error, tail error, and temporal balance—not because it wins every year. Its positive
annualized signed error of 3.92 percentage points indicates underprediction on average and remains
an important limitation for interval evaluation.

## Three-year decision

State trend clearly outperforms the fitted models overall. Its MAE is 0.06659 and RMSE is 0.08961,
compared with 0.08073 and 0.10319 for the tree and 0.10327 and 0.12900 for regularized linear. State
trend is best by a wide margin in 2017 and is essentially tied with the tree in 2018. It also has
the smallest annualized signed error at -0.24 percentage points.

Selecting the baseline is a substantive result. The available tract and ACS features do not add
enough stable three-year information to beat the statewide market signal. The application should
show that result honestly instead of presenting a more complex model merely because one was fit.

## Interval method

Job 504 uses a 90% split-conformal absolute-residual interval separately for each horizon:

1. Fit the frozen method using development-state labels whose endpoints occur before the reserved
   calibration origin.
2. Score the calibration origin without changing the model choice or parameters.
3. Calculate the finite-sample-corrected 90th percentile of absolute calibration residuals in the
   development states.
4. Add and subtract that radius from later point predictions.
5. Measure empirical coverage and average interval width on the locked temporal test overall and
   across geography, cohort, housing mix, ACS uncertainty, and Census region.

The interval makes no normal-error assumption and uses held-out residuals rather than fitted
training errors. Its main limitation is temporal: each horizon has only one independent
calibration origin, even though that origin contains many tracts. The app therefore calls it a
calibrated uncertainty interval, not a guarantee or a complete distribution of future outcomes.

## Locked-test rule

The one-year 2024 origin and three-year 2022 origin were untouched by model selection and interval
design. Job 504 opened them once under this frozen contract. Their results are final evidence and
will not trigger parameter changes or a second preferred model. Any later research iteration must
receive a new contract version and must not replace the original locked-test result.

## Final locked result and release consequence

Job 504 opened the frozen tests under finalization run
`73a193b64d154d868d8e94c039858861`. Job 605 then applied the same release requirements to both
horizons without choosing a replacement model.

| Horizon | Locked MAE | Zero-change MAE | Empirical coverage | Release |
|---|---:|---:|---:|---|
| 1 year | 0.0599 | 0.0627 | 89.4% | Published |
| 3 years | 0.2943 | 0.1566 | 48.2% | Withheld |

The one-year tree passes because it improves on zero change and its coverage is consistent with
the 90% target. State trend is slightly better on one-year locked MAE at 0.0592, so the application
shows that baseline beside the frozen tree.

The three-year state-trend method overpredicted the 2022-2025 period and failed both the accuracy
and uncertainty requirements. It remains the reported locked result but is not an application
forecast. The project will not use that outcome to retroactively promote another development
candidate.

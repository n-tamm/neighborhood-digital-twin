# 06 — Forecasting Implementation

## Purpose and target

The implemented forecast estimates cumulative change in FHFA's single-family tract House Price
Index. One year is the primary product horizon; three years was evaluated as a secondary horizon.
The result is a neighborhood-market index forecast, not an individual property valuation, a
multifamily forecast, or an investment recommendation.

The stored target is:

```text
log(HPI at the target endpoint / HPI at the forecast origin)
```

The application converts that value to an annualized percentage for readability while retaining
the cumulative-log value for evaluation and lineage.

## Point-in-time data contract

The estimator reads `gold_modeling_panel`, which joins three governed products:

- point-in-time ACS, HPI history, and regional context from `gold_model_feature_historical`;
- direct future HPI outcomes from `gold_forecast_target_historical`; and
- frozen temporal and geographic roles from `gold_model_split_assignment`.

Features use only source releases available by the forecast origin. Labels used for fitting must
end strictly before the origin being scored. No random row split is allowed because neighboring
years from the same tract share history and ACS five-year estimates overlap.

Pre-2020 ACS releases use the governed 59,607-tract stable 2010-to-2020 cohort. A modeling row may
cross the tract redesign only when its feature history satisfies that stable-cohort rule. FHFA
outcomes are not discarded solely because their endpoint falls in a new calendar decade.

## Frozen temporal roles

| Horizon | Training | Validation | Calibration | Purged | Locked test | Current scoring |
|---|---|---|---|---|---|---|
| 1 year | 2011-2020 | 2021-2022 | 2023 | None | 2024 | 2025 |
| 3 years | 2011-2016 | 2017-2018 | 2019 | 2020-2021 | 2022 | 2025 |

Maine, North Dakota, West Virginia, and New Mexico provide deterministic regional geographic
transfer checks. They are not substitutes for the later temporal test.

## Development methods

Job 500 compares all methods on identical validation rows:

1. Zero change.
2. Latest tract change persistence.
3. Recent three-year tract mean.
4. County current trend.
5. State current trend.
6. L2-regularized linear regression.
7. Spark gradient-boosted trees.

The two fitted candidates use median imputation learned inside their training data. The linear
pipeline also standardizes features inside the fold. GBT tuning uses purged expanding-origin
training folds; validation and locked outcomes never select its depth or iteration count.

The feature registry covers recent HPI history, county/state context, community scale, occupancy
and tenure, housing structure, affordability, ACS timing, and ACS margins of error. Simplified
map geometry is never an input.

## Frozen selection

The corrected job-500 validation run is `f51ad8ff85c44fe5bbd665b20520f6e4`.

- **One year:** GBT, depth 2 and 50 iterations. Validation MAE 0.0733 and RMSE 0.0929.
- **Three years:** state current trend. Validation MAE 0.0666 and RMSE 0.0896.

Selections were written down before job 504 read either calibration or locked outcomes. The
project permits a different model family by horizon because the amount and behavior of historical
evidence differ.

## Finalization and uncertainty

Job 504 refits each frozen method separately for calibration, locked testing, and current scoring.
For fitted models, every training label must end before the scored origin. The direct state-trend
baseline has no fitted training cutoff but uses only origin-year information.

The interval method is a 90% split-conformal absolute-residual interval:

1. Score the reserved calibration origin with the frozen method.
2. Calculate the finite-sample corrected 90th percentile of absolute residuals.
3. Add and subtract that radius from later cumulative-log predictions.
4. Evaluate locked coverage and interval width without changing the method.

The one-year radius is 0.1222 from 41,017 calibration rows. The three-year radius is 0.2675 from
39,563 rows. These intervals do not assume normally distributed errors, but each horizon still
has only one independent calibration year.

## Locked result

Finalization run `73a193b64d154d868d8e94c039858861` produced:

| Horizon | Champion MAE | Zero-change MAE | Empirical coverage | Main finding |
|---|---:|---:|---:|---|
| 1 year | 0.0599 | 0.0627 | 89.4% | Useful and approximately calibrated |
| 3 years | 0.2943 | 0.1566 | 48.2% | Large overprediction and failed uncertainty |

The three-year miss was systematic: mean prediction was 0.442 cumulative log change, compared
with 0.149 observed. The unusually strong 2022 state trend did not persist through 2025.

## Release gate and serving

Job 605 creates one release decision per horizon. A horizon must have at least 1,000 locked rows,
beat or tie zero change on MAE, and achieve coverage no more than ten percentage points below its
nominal target. The job does not search for another model.

The one-year horizon passes. The three-year horizon fails accuracy and coverage and is withheld.
Job 701 therefore publishes:

- 46,719 one-year current forecasts from a 2025 origin;
- point, lower, upper, and state-baseline fields;
- locked-test and release-gate context for explanation;
- one availability row per current tract and horizon; and
- a complete manifest written only after both serving tables reconcile.

The application reads these compact serving products, never the wide modeling panel.

## Evaluation outputs

Validation scorecards include MAE, RMSE, signed bias, tail error, R-squared, zero-change skill,
origin-year stability, geographic transfer, stable/broad cohort, housing composition, Census
region, state, and ACS uncertainty.

Locked scorecards retain the same important slices plus interval coverage and annualized interval
width. Job 606 renders three final figures covering validation versus locked MAE, locked interval
coverage, and mean observed versus predicted change.

## Spatial scope

County and state market context is implemented through point-in-time aggregate features. True
tract adjacency, spatial lag models, and distance-weighted neighbor effects are not implemented.
The available tract geometry is simplified for display and explicitly prohibited from modeling.

## Future research boundary

A later three-year iteration could test damped persistence, change relative to a state/national
path, or regime-aware calibration. It must receive a new contract and future evaluation data. The
reported 2022-2025 locked result cannot be replaced or relabeled after seeing its outcome.

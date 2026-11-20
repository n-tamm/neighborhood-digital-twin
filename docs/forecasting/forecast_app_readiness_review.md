# Forecast and Application Readiness Review

This review records the state of the forecasting work after the November 2026 branch merge and
defines what must happen before a forecast appears in the application. It does not select a model
or open the locked temporal test.

## What is implemented

The forecasting workflow now fits fixed baselines, a regularized linear model, and a Spark
gradient-boosted-tree challenger for the active one- and three-year horizons. The target is
cumulative log change in FHFA tract-level single-family HPI. Preprocessing is fit from training
rows, model comparisons use published validation rows, and the tree search uses expanding-origin
training folds whose outcome windows end before the held-out fold begins.

The one-year tree selected depth 2 and 50 iterations from three training folds. The three-year
history does not contain enough purge-safe folds for tuning, so that model retains the fixed depth
4 and 50 iteration settings. A one-year feature-family ablation also ran on the training folds.
It found the clearest losses after removing HPI history or regional context; the remaining changes
were too small to support removing a feature family.

## What the current validation results say

The November 13 scorecard does not identify a clear one-year winner. The tree has MAE 0.07173 and
the linear model has MAE 0.07199, a difference of about 0.00027 log points, or 0.37% of the linear
model's MAE. The linear model has slightly lower RMSE, less signed bias, and better R-squared. The
ranking also changes by validation year: the state-trend baseline is best in 2021, while the tree
is best in 2022. Treat the one-year models as practically tied until the team applies a written
selection rule to the full metric and subgroup evidence.

The three-year tree is more promising. Its MAE is 0.07209, compared with 0.08365 for regularized
linear and 0.08526 for state trend, and it is best in both validation origins. That evidence is
still limited: the tree used fixed rather than tuned settings and only three independent training
origins are available under the current split.

Directional accuracy is not a useful deciding metric because most validation outcomes are
positive. A model can appear directionally accurate by nearly always predicting appreciation.
MAE, RMSE, signed bias, tail error, origin-year consistency, geographic transfer, and subgroup
behavior should drive the decision.

## Why forecasts and uncertainty are absent from the app

The current app behavior is intentional. The merged work publishes development predictions and
evaluation scorecards, not an approved current-neighborhood forecast product. The following pieces
do not exist yet:

- a frozen champion or an explicit rule for choosing between the one-year tree and linear model;
- a calibrated uncertainty interval;
- a final locked-test result produced only after the model and interval method are frozen;
- current-origin inference for every eligible tract;
- a versioned serving table, release manifest, and availability reason; and
- compact driver or baseline fields that the app can explain without reading the modeling panel.

The app therefore keeps its forecast tab in an explained unavailable state. It must not display a
validation prediction or an analogue outcome as if either were a forecast for the selected tract.

## Decision gate: calendar-decade censoring

The merged workflow excludes every target whose origin and endpoint fall in different calendar
decades. For example, it discards a fully observed 2019-to-2022 target. This removes substantial
history and leaves only three three-year training origins.

This rule needs a source-backed review before the forecast pipeline is rerun. FHFA publishes the
annual Census-tract HPI as one longitudinal dataset rather than separate decade-specific series:
[FHFA HPI datasets](https://www.fhfa.gov/data/hpi/datasets). In the project's silver data, the FHFA
series also remains continuous across 2019 and 2020 under the source's 2020 tract geography. The
project already limits cross-vintage ACS comparisons to the governed stable-tract cohort.

That evidence suggests the decade rule may be applying an ACS tract-vintage concern to an FHFA
outcome that is already reported on a consistent geography. This is an inference, not a completed
decision. The team should either document a FHFA or geography source that requires the restriction,
or remove the blanket censor while preserving the stable-cohort rule wherever point-in-time ACS
features cross the 2020 redesign. Changing this policy requires new target and split contract
versions and a rebuild of jobs 301, 302, 500, and dependent forecast evaluation outputs.

## Required sequence before application integration

1. Resolve and version the calendar-decade target rule before comparing models again.
2. Rebuild historical targets, split assignments, and the modeling panel if that rule changes.
3. Rerun the baseline and tree workflow on identical validation rows, then refresh every forecast
   figure from that same run. Retire five-year rows from active reports rather than mixing them
   into the one- and three-year decision.
4. Apply a preregistered selection rule. At one year, prefer the simpler linear model unless the
   tree shows a meaningful, consistent benefit beyond a marginal aggregate-MAE difference. Make a
   separate horizon decision if the three-year evidence supports the tree.
5. Fit an interval method using only the reserved calibration origins. Report empirical coverage
   and average interval width overall and by origin year, geography cohort, housing mix, and ACS
   uncertainty. Widen or suppress intervals where calibration is not credible.
6. Freeze the point model, preprocessing, features, interval method, and selection rationale.
   Only then run the locked temporal test once and report it without retuning.
7. Score the latest eligible tract-origin rows and publish a versioned forecast release. At
   minimum, each row needs tract, horizon, as-of year, point estimate, lower and upper bounds,
   baseline comparison, model and feature versions, release status, and an unavailable reason.
8. Add the release to the app repository layer and contract tests. The forecast screen should show
   the point estimate and interval together, explain the target in plain language, compare it with
   a simple baseline, keep historical analogues separate, and show an explicit unavailable state
   where coverage fails.

## Repository follow-up

The merged local demonstration notebook and feature-ablation notebook also need the repository's
exact AI-assistance disclosure. The model label used by the contributor must be confirmed rather
than guessed. The forecast evaluation figures should be regenerated after the target contract and
final validation run are settled; the currently committed images predate the November 13 tuned
run.

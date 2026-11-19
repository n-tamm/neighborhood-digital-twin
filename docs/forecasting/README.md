# Forecasting Documentation

This folder explains the implemented forecast workflow from target construction through the live
application release. The project forecasts cumulative change in FHFA's tract-level single-family
House Price Index. It does not estimate an individual home value or the price path of every type
of housing in a neighborhood.

## Read in this order

1. [Target and split design](target_and_split_design.md) defines what is predicted and which
   origin years are used for training, validation, calibration, locked testing, and current
   scoring.
2. [Baseline model design](baseline_model_design.md) explains the transparent comparison methods
   and fitted candidates.
3. [Baseline workflow](baseline_workflow.md) describes job 500 and its validation-only outputs.
4. [Gradient-boosted-tree candidate](gradient_boosted_tree_candidate.md) records the training-fold
   tuning and feature-family ablation.
5. [Final model selection and interval](final_model_selection_and_interval.md) records the choices
   frozen before calibration and the locked test.
6. [Evaluation and current results](evaluation_and_results.md) gives the validation, locked-test,
   uncertainty, and release findings.
7. [Forecast and application readiness review](forecast_app_readiness_review.md) explains the
   production gate and what the app now publishes or withholds.
8. [Forecasting module](forecasting_module.md) documents the reusable implementation.

## Implemented Databricks sequence

```text
301 Historical gold targets
    -> 302 Point-in-time features and split assignments
    -> 500 Validation-only model comparison
    -> freeze one method per horizon
    -> 504 Calibration, locked test, and current scoring
    -> 605 Locked-test release gate
    -> 606 Final evaluation figures
    -> 701 Forecast serving release
    -> Databricks application
```

Job 500 cannot read the locked temporal roles. Job 504 runs only after the selections and interval
method are written down. Job 605 does not choose a replacement model; it decides whether each
already evaluated horizon is safe to publish. This distinction is important because the
three-year method failed its locked test and remains part of the reported result even though it is
not served in the application.

## Current product state

- One-year gradient-boosted-tree forecasts are published for 46,719 model-ready 2025 tracts.
- Each published point estimate includes a 90% split-conformal interval and a state-trend baseline.
- The one-year locked MAE is 0.0599, compared with 0.0627 for zero change; interval coverage is
  89.4%.
- The three-year state-trend method has locked MAE 0.2943, compared with 0.1566 for zero change,
  and only 48.2% interval coverage. It is explicitly withheld.
- The app shows an availability reason instead of substituting an analogue outcome, validation
  result, or unapproved model.

The final figures are documented in
[the model evaluation report](../../reports/MODEL_EVALUATION_FIGURES.md).

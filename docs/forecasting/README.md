# Forecasting Documentation

This folder explains the implemented forecast workflow from target construction through the
application release. The project forecasts cumulative change in FHFA's tract-level single-family
House Price Index. It does not estimate an individual home value or the price path of every type
of housing in a neighborhood.

## Read in this order

1. [Target and split design](target_and_split_design.md) defines the forecast target and temporal
   roles.
2. [Baseline model design](baseline_model_design.md) separates the simple comparison methods from
   the two supervised project models.
3. [Baseline workflow](baseline_workflow.md) describes job 500 and its validation outputs.
4. [Gradient-boosted-tree candidate](gradient_boosted_tree_candidate.md) records training-fold
   tuning and feature-family ablation.
5. [Two-model finalization and interval contract](final_model_selection_and_interval.md) explains
   why both supervised models continue through evaluation and serving.
6. [Evaluation and current results](evaluation_and_results.md) explains metrics, results, and
   limits.
7. [Forecast application readiness](forecast_app_readiness_review.md) describes the serving and
   application contract.
8. [Forecasting module](forecasting_module.md) documents the reusable implementation.

## Implemented Databricks sequence

```text
301 Historical gold targets
    -> 302 Point-in-time features and split assignments
    -> 500 Validation comparison: five baselines + linear + boosted trees
    -> freeze both supervised specifications at both horizons
    -> 504 Model-specific calibration, later evaluation, and current scoring
    -> 605 Evaluation thresholds for each model and horizon
    -> 606 Side-by-side evaluation figures
    -> 701 Both models published at one and three years
    -> Databricks application
```

Job 500 keeps later evaluation roles out of model development. Job 504 fits and scores the same
regularized-linear and gradient-boosted-tree specifications at both horizons. Job 605 attaches
quality warnings; it does not select a champion, replace a model with a trend, or suppress a
forecast. Job 701 publishes both supervised outputs when the tract is model-ready.

## Model and baseline roles

- **Project models:** regularized linear regression and gradient-boosted trees.
- **Primary horizon:** one year.
- **Secondary horizon:** three years.
- **Baselines:** zero change, latest-change persistence, recent three-year mean, county trend, and
  state trend.
- **Uncertainty:** one split-conformal interval calibrated separately for each model and horizon.

The state trend is intentionally visible in evaluation and forecast charts as a reference point.
It is not the project's three-year model.

The final evaluation figures are documented in
[the model evaluation report](../../reports/MODEL_EVALUATION_FIGURES.md).

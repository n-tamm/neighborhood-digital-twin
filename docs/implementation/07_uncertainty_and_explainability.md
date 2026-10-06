# 07 — Uncertainty and Explainability

## Purpose

A forecast without measured uncertainty is too easy to overread. This stage estimates intervals, checks their calibration, and prepares model-driver explanations that help users understand the prediction without turning association into a causal claim.

## Uncertainty method

Two practical options fit the capstone:

- **Quantile regression:** train models for lower, median, and upper conditional quantiles.
- **Split conformal calibration:** use held-out residuals to wrap a point model with empirically calibrated intervals.

Start with the method that works cleanly with the selected estimator and time split. If quantile models cross or produce unstable tails, add ordering checks and consider conformal calibration. Use a later calibration period that is separate from model fitting and the locked test.

Intervals are horizon-specific. Do not assume the one-year residual distribution scales mechanically to three or five years.

## Calibration evaluation

Report:

- empirical coverage for the chosen nominal levels, such as 50%, 80%, and 90%;
- average and median interval width;
- coverage and width by year, metro, region, history length, missingness, and ACS quality;
- interval score or another metric that balances coverage and width;
- relationship between interval width and realized error;
- performance during unusually strong or weak housing periods.

Overall coverage can hide poor calibration for specific places. If a subgroup is persistently undercovered, widen intervals, recalibrate by a defensible group, or disclose the limitation.

## Explainability method

Use model-appropriate global and local methods after the forecast model is frozen:

- permutation importance for out-of-sample global reliance;
- SHAP values for tree-model global and local contributions when runtime permits;
- coefficients for the regularized linear baseline;
- feature-family ablation as the strongest evidence that a group adds predictive value.

An explanation should show the reference or baseline prediction and the features that moved the model higher or lower. It should not say a variable caused the future HPI change. Correlated fields can divide or swap importance, so show grouped results where that makes interpretation more stable.

## Stability checks

- compare importance across time folds and metros;
- group correlated variables into understandable families;
- test whether local explanations change sharply under small, plausible input perturbations;
- verify that missingness indicators do not dominate without a clear interpretation;
- compare the nonlinear explanation with the direction of the linear baseline where useful.

## Public explanation contract

The app-ready explanation should contain:

- tract and forecast origin;
- model and feature version;
- baseline or expected prediction;
- final point prediction and interval;
- top positive and negative contributions with units or plain labels;
- data-quality warnings;
- a short statement that contributions describe model behavior, not causal effects.

Limit the public view to a handful of stable, interpretable drivers. Full diagnostic values can remain in research artifacts.

## Required outputs

- calibrated interval object or quantile models;
- interval table tied to each prediction;
- calibration plots and slice tables;
- global feature and feature-family findings;
- local explanation contract for the app;
- model-card sections covering uncertainty and interpretability;
- documented failure and fallback behavior.

## Acceptance checks

- calibration data was not used to fit the point model;
- the locked test was not used to choose nominal levels or recalibration groups;
- interval bounds are ordered and use the same outcome scale as the forecast;
- empirical coverage is reported beside width;
- explanation values reconcile with the model output within method tolerance;
- public labels avoid causal language;
- missing or unreliable explanations fail gracefully rather than showing zero importance.

## Handoff

Evaluation receives frozen point and interval predictions. The serving bundle receives compact, versioned explanations and calibration metadata. Scenario outputs should use the same outcome scale and uncertainty definitions.

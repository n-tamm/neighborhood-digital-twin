# 10. Evaluation, Validation, and Responsible Use

This stage turns model output into defensible evidence. Evaluation is not a final accuracy check; it is the process used to decide whether a component is reliable enough to appear in the application and how cautiously it should be described.

## Stage objective

Create one evaluation protocol that covers forecasts, uncertainty intervals, historical analogues, trajectory clusters, and scenario responses. The protocol should be frozen before final model selection so the team does not unknowingly tune to the test results.

## Questions this stage must answer

- Does the system beat simple, decision-relevant baselines?
- Does it still work for later years, unfamiliar metros, and different neighborhood types?
- Are uncertainty ranges calibrated, or merely visually convincing?
- Are the analogue and cluster results stable enough to interpret?
- Can a user tell the difference between an observed fact, a forecast, and a hypothetical scenario?
- Where is performance weak enough that the application should warn the user or withhold a result?

## Evaluation design

### 1. Freeze the prediction setting

Record the unit of analysis, target definition, forecast origin, horizons, eligible features, data-availability lag, geography, and final evaluation periods. A prediction made for year `t + 3` may only use information that would have been available at the end of year `t`.

### 2. Use time-aware splits

The primary design should be rolling-origin evaluation. Train on an expanding historical window, predict the next period or horizon, advance the cutoff, and repeat. Keep the final time block untouched until major feature and model choices have been made.

### 3. Test geographic transfer

Add a metro or regional holdout when the data volume allows it. This is different from a random tract split: nearby tracts share market conditions, policy environments, and spatial spillovers, so random splitting can substantially overstate generalization.

### 4. Compare against honest baselines

At minimum, compare each forecast horizon against:

- last observed value or no-change forecast;
- metro-wide trend applied to the tract;
- regularized linear model using the same information set;
- a simple historical growth-rate forecast.

Advanced models earn a place in the product only if they improve performance, calibration, stability, or interpretability enough to justify their complexity.

## Component-specific evaluation

### Forecasts

Use MAE as the primary readable error metric and report RMSE when large misses matter. Consider MASE or a comparable scaled metric when comparing targets with different units. Report performance by horizon and against every baseline, not just as one pooled score.

### Direction and transition

If the product labels trajectories such as growing, stable, or declining, measure balanced accuracy, macro F1, and confusion matrices. Define transition thresholds before evaluation so that labels are not adjusted to make results look better.

### Uncertainty

For each nominal interval, report empirical coverage and average interval width. Include calibration plots by horizon. Narrow intervals with poor coverage are not useful, while very wide intervals can be technically calibrated but practically empty.

### Analogues and clusters

Evaluate whether nearest neighbors are stable under small changes in features, scaling, time windows, and random seeds. Check whether retrieved communities are plausible on held-out attributes that were not used for matching. For clustering, combine quantitative stability measures with short profiles reviewed by people who understand the data; a high silhouette score alone does not make clusters meaningful.

### Scenario engine

Test invariants and boundary behavior rather than claiming causal accuracy. For example, changing an unrelated display setting must not change a model result, impossible values must be rejected, and a zero-change scenario must reproduce the baseline prediction. Document where a response is counterintuitive and whether it reflects model behavior, correlated inputs, or an implementation defect.

## Required slices

Results should be broken out where sample size permits by:

- metro and Census region;
- baseline price or rent level;
- urbanicity or density;
- income and racial-composition bands;
- data completeness;
- growth, stability, and decline periods;
- target horizon.

These slices are diagnostic. They should not be used to rank demographic groups or assign quality scores to communities.

## Statistical uncertainty

Use block bootstrap or another method that respects temporal and spatial dependence when placing uncertainty around aggregate metrics. Record both the central estimate and variation across folds, seeds, or time windows. A small mean improvement that disappears across folds should be described as inconclusive.

## Leakage audit

Before accepting a model, verify:

- every feature has a documented publication or availability lag;
- transforms are fitted on training data only;
- revised historical values are not treated as if they were known in real time unless explicitly accepted and documented;
- spatial aggregates exclude the target outcome from the prediction period;
- analogue search does not use future attributes;
- test geographies and dates did not influence feature selection.

Record the completed audit in the model card.

## Responsible-use review

Housing and neighborhood models can reinforce harmful ideas even when they use public, aggregate data. The product must not produce a single neighborhood desirability score, recommend exclusion based on protected characteristics, support tenant screening, or present model output as a causal statement. Demographic fields may be important for understanding unequal outcomes, but they require a clear analytical purpose and careful presentation.

The interface should:

- distinguish observations, estimates, forecasts, and user-entered scenarios;
- expose uncertainty and data freshness near the result;
- avoid redlining-like color scales and simplistic good/bad labels;
- state that tract-level statistics do not describe every resident;
- explain important limitations in ordinary language;
- suppress or qualify results with inadequate coverage.

## Required outputs

- frozen evaluation plan and split definitions;
- baseline comparison table by target and horizon;
- geographic and demographic slice analysis;
- interval calibration report;
- analogue and cluster stability analysis;
- leakage checklist;
- completed model card and limitations document;
- application-facing warning and suppression rules.

## Exit criteria

This stage is complete when results can be reproduced from versioned inputs, every displayed component has a stated evaluation method, weaknesses are documented alongside strengths, and the team has explicitly decided what the application will and will not claim.


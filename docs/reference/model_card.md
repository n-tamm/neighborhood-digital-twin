# Model Card

This document begins as the review template for the first released forecasting system. Replace `TBD` entries with evidence from the selected experiment; create a separate section or card if analogue, clustering, or scenario components use materially different models.

## Model identity

| Item | Value |
|---|---|
| Model name | TBD |
| Model version | TBD |
| Serving-bundle version | TBD |
| Code commit | TBD |
| Training cutoff | TBD |
| Geography coverage and vintage | TBD |
| Owner and reviewer | TBD |

## Intended use

The planned model estimates tract-level housing trajectory outcomes over defined future horizons. It supports exploration, comparison, and scenario sensitivity in the Neighborhood Digital Twin application. It is not intended to appraise an individual property, guarantee an investment return, screen tenants, determine credit, establish insurance terms, or rank the worth of communities or residents.

## Targets and outputs

Document each target, horizon, unit, transformation, point prediction, uncertainty interval, and suppression condition. State exactly when the forecast is considered to originate and what information is allowed at that time.

## Data

| Topic | Evidence |
|---|---|
| Training sources and versions | TBD; link to manifests |
| Training period | TBD |
| Unit of analysis | Census tract-year, subject to final contract |
| Inclusion and exclusion rules | TBD |
| Missing-data handling | TBD |
| Geography and boundary handling | TBD |
| Publication-lag handling | TBD |

## Model and feature approach

Describe the selected algorithm, hyperparameters, feature families, transformations, spatial features, and calibration method. Link to the experiment configuration and explain why this model was chosen over the simplest credible baseline.

## Evaluation

Report performance for every supported horizon using rolling temporal splits and any geographic holdout. Include:

- baseline and candidate metrics;
- variation across folds or seeds;
- interval coverage and width;
- performance slices by metro, price level, urbanicity, demographic context, and missingness where sample size allows;
- ablation results for major feature families and spatial information;
- known failure patterns and examples.

Do not report only the winning aggregate score.

## Fairness and affected groups

Explain how errors or interface choices could affect residents, prospective buyers, planners, and neighborhoods historically affected by housing discrimination. Record whether demographic variables are used as predictors, analysis fields, or both, and justify that choice. Summarize any material disparities in error, interval coverage, missingness, or result suppression.

## Limitations

At minimum, address ecological fallacy, ACS sampling uncertainty, revised data, tract boundary change, omitted local conditions, spatial dependence, unusual market shocks, inability to infer causality, and the risk that historical patterns reproduce historical inequities.

## Leakage and reproducibility review

- [ ] Feature availability is point-in-time correct.
- [ ] Training-only transformations are verified.
- [ ] Spatial aggregates cannot see the target period.
- [ ] Hyperparameter selection excludes the final test block.
- [ ] Source, feature, model, and bundle versions are recorded.
- [ ] The released predictions reproduce from the declared artifacts.

## Monitoring and retirement

Define the data-through date shown to users, conditions that trigger retraining, drift or quality checks, unsupported-geography behavior, rollback version, and criteria for retiring the model. Free-tier hosting uptime is not a model-quality guarantee.

## Approval

| Role | Name | Date | Decision or conditions |
|---|---|---|---|
| Model owner | TBD | TBD | TBD |
| Independent reviewer | TBD | TBD | TBD |


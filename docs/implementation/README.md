# Technical Implementation Guide

These documents describe the intended build sequence. The numbering reflects dependencies, not a rigid rule that one stage must be completely finished before another begins. Small vertical slices are encouraged, but later work should not quietly redefine earlier contracts.

| Stage | Guide | Main output |
|---:|---|---|
| 00 | [Implementation overview](00_implementation_overview.md) | Shared lifecycle, contracts, and gates |
| 01 | [Data discovery and feasibility](01_data_discovery_and_feasibility.md) | Scope recommendation and feasibility evidence |
| 02 | [Data acquisition and pipeline](02_data_acquisition_and_pipeline.md) | Versioned bronze and silver source tables |
| 03 | [Geography and time alignment](03_geography_and_time_alignment.md) | Canonical tract geography and point-in-time joins |
| 04 | [Data exploration](04_data_exploration.md) | Coverage, bias, missingness, and relationship findings |
| 05 | [Neighborhood state, features, and targets](05_neighborhood_state_features_and_targets.md) | Gold tract-year state, feature, and target contracts |
| 06 | [Forecasting and spatial modeling](06_forecasting_and_spatial_modeling.md) | Baselines, candidate models, and spatial ablations |
| 07 | [Uncertainty and explainability](07_uncertainty_and_explainability.md) | Calibrated intervals and model-driver outputs |
| 08 | [Representations, analogues, and clustering](08_representations_analogues_and_clustering.md) | Evaluated historical-analogue system |
| 09 | [Scenario engine](09_scenario_engine.md) | Bounded, tested sensitivity distributions |
| 10 | [Evaluation, validation, and ethics](10_evaluation_validation_and_ethics.md) | Locked results, slices, ablations, and risk review |
| 11 | [Application and visualization](11_application_and_visualization.md) | Integrated map-driven public experience |
| 12 | [Deployment and operations](12_deployment_and_operations.md) | Public app, static fallback, and runbooks |
| 13 | [Integrations and extensions](13_integrations_and_extensions.md) | Rules for adding optional capabilities safely |
| 14 | [Capstone delivery](14_capstone_delivery.md) | Final report, visuals, demo, release, and reproducibility evidence |

## How to use a stage guide

Before implementation, turn the stage's outputs and acceptance checks into issues. Assign one owner to the output contract even when several people contribute. When the stage changes a shared assumption, write a decision record. At the end, link the evidence—tests, report, table, figure, or deployed view—rather than marking the stage complete from memory.

The guides separate required MVP work from optional extensions. An extension should not delay a required contract or weaken the final evaluation.

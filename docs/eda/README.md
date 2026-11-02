# Exploratory Data Analysis

This folder documents the implemented exploratory-data-analysis workflow and each of its twelve
published visuals. It is organized so a reader can understand one figure without opening
Databricks, while still being able to trace the figure to its inputs and rendering code.

## Reading order

1. Read [EDA workflow](workflow.md) for the job sequence, governed inputs, publication process,
   and shared visual rules.
2. Read the figure notes in numerical order. Figures 1-3 establish the available population,
   Figures 4-6 explain time, measurement, and geography constraints, Figures 7-8 establish model
   readiness, and Figures 9-12 show geographic coverage and observed housing-market patterns.
3. Use the [figure inventory](../../reports/EDA_FIGURES.md) for the current build ID, Databricks
   paths, export commands, and visual-review record.

## Figure documentation

| Figure | Documentation | Main question |
|---:|---|---|
| 1 | [Pipeline attrition](figures/01_pipeline_attrition.md) | Where does the current tract universe narrow? |
| 2 | [Housing-composition coverage](figures/02_housing_composition_coverage.md) | How does FHFA coverage vary with housing stock? |
| 3 | [Included versus excluded tracts](figures/03_forecast_included_excluded.md) | Is the forecast-eligible population observably different? |
| 4 | [HPI temporal behavior](figures/04_hpi_temporal_behavior.md) | How much do tract HPI changes vary over time and place? |
| 5 | [ACS measurement uncertainty](figures/05_acs_measurement_uncertainty.md) | Which inputs have the greatest sampling uncertainty? |
| 6 | [Tract-vintage coverage](figures/06_tract_vintage_coverage.md) | Which cohort is valid across the 2020 boundary redesign? |
| 7 | [Model-feature completeness](figures/07_model_feature_completeness.md) | Which approved model inputs require imputation? |
| 8 | [Forecast-origin counts](figures/08_model_split_origin_years.md) | How much independent temporal evidence supports each horizon? |
| 9 | [Forecast-candidate maps](figures/09_forecast_candidate_maps.md) | Where is current forecast eligibility available in the pilot states? |
| 10 | [Tract HPI change maps](figures/10_hpi_change_maps.md) | How do post-2020 gains compare with the latest annual movement? |
| 11 | [County HPI trend story](figures/11_county_hpi_trend_story.md) | Do cumulative gains imply continued momentum? |
| 12 | [State forecast coverage](figures/12_state_forecast_coverage.md) | How does current model reach vary nationally? |

All figures are descriptive or readiness evidence. None establishes causality, final model
performance, or a neighborhood ranking.

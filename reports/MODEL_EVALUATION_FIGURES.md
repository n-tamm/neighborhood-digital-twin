# Model Evaluation Figures

The project has a seven-figure development build and a three-figure final forecast build. The
development build compares all baselines and both supervised models on validation data. The final
build compares regularized linear regression and gradient-boosted trees at one and three years
using later-period error and model-specific uncertainty.

## Corrected final forecast build

Job 606 produces three figures after jobs 504 and 605 complete under the version-2 two-model
contract:

1. **Supervised-model validation and later-period MAE.** Two horizon panels compare linear and
   boosted-tree validation and later-period error with zero-change and state-trend baselines.
2. **Model-specific interval coverage.** Four bars show one- and three-year coverage for both
   supervised models. Hatching marks a missed evaluation threshold without implying that the
   forecast was deleted.
3. **Mean observed and predicted later-period change.** Each horizon compares the observed mean
   with both supervised-model means to make error direction understandable.

The corrected build completed on November 22, 2026:

- **Figure build:** `forecast-final-20261122T163847149439Z`
- **Databricks job run:** `346673047634854`
- **Forecast finalization run:** `29c68a5af1e74daab6e06ff7aa2aa9e9`
- **Managed-volume root:**
  `/Volumes/workspace/neighborhood_twin_evaluation/model_evaluation_figures/final_forecast/build_id=forecast-final-20261122T163847149439Z`
- **Reviewed application copies:** `app/assets/data_science/02_forecast_validation_vs_locked_mae.png`,
  `03_forecast_interval_coverage.png`, and `04_forecast_observed_vs_predicted.png`

The previous build `forecast-final-20261119T173650231784Z` is superseded because it treated the
three-year state-trend baseline as the project model.

## Validation-era build

Job 600 publishes seven diagnostics from the validation scorecard and similarity summary:

- **Current build:** `20261121T204651124557Z`
- **Databricks job run:** `213227950122594`
- **Manifest:** `workspace.neighborhood_twin_evaluation.model_evaluation_figure_manifest`

The figures cover MAE by method and horizon, skill relative to zero change, bias and tail error,
held-out-state transfer, housing-composition slices, similarity representation diagnostics, and
forecast-origin stability. These are development results and should not be presented as current
tract forecasts.

## Reproduce

```powershell
databricks bundle run model_evaluation_figures --profile neighborhood-twin -t team
databricks bundle run forecast_final_evaluation_figures --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

Both workflows publish their manifest only after every expected PNG passes file-size and count
checks. They read governed evidence and do not fit or replace a model.

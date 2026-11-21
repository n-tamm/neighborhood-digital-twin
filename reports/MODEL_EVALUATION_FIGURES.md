# Model Evaluation Figures

The project has two complementary forecast figure sets. The original seven-figure build explains
validation-era method comparison and similarity diagnostics. The newer three-figure build records
the final forecast story after model choices were frozen: locked accuracy, interval coverage, and
the direction of the three-year failure.

## Final forecast build

- **Build:** `forecast-final-20261119T173650231784Z`
- **Finalization run:** `73a193b64d154d868d8e94c039858861`
- **Databricks volume:**
  `/Volumes/workspace/neighborhood_twin_evaluation/model_evaluation_figures/final_forecast/build_id=forecast-final-20261119T173650231784Z/`
- **Manifest:**
  `workspace.neighborhood_twin_evaluation.forecast_final_evaluation_figure_manifest`
- **Optional local review copy (Git-ignored):**
  `reports/generated/model-evaluation/forecast-final-20261119T173650231784Z/`

### 1. Validation and locked-test forecast error

**File:** `01_validation_vs_locked_mae.png`

This is the main model-performance figure. It shows that the one-year tree remained useful, while
the frozen three-year state-trend method went from the strongest validation result to a locked MAE
of 0.294—substantially worse than zero change at 0.157. The figure should be used when explaining
why a method can look good in development but still fail under a new market regime.

### 2. Locked interval coverage

**File:** `02_locked_interval_coverage.png`

The one-year 90% interval covered 89.4% of locked outcomes. The three-year interval covered only
48.2%, below the 80% release minimum. This figure connects uncertainty evaluation directly to the
application decision.

### 3. Mean observed and predicted locked-period change

**File:** `03_locked_mean_observed_vs_predicted.png`

This figure explains the three-year failure in plain terms. The model carried the strong 2022
state trend forward and predicted mean cumulative log growth of 0.442, while the 2022-2025
outcome averaged 0.149. It is a systematic overprediction, not a few isolated tract errors.

## Validation-era build

Job 600 publishes seven versioned diagnostics from the current validation scorecard and similarity
summary:

- **Current build:** `20261121T204651124557Z`
- **Databricks job run:** `213227950122594`
- **Manifest:** `workspace.neighborhood_twin_evaluation.model_evaluation_figure_manifest`
- **Validation:** seven unique figure sequences, one forecast run, one similarity run, and file
  sizes from 106,671 to 162,530 bytes

1. MAE by method and horizon.
2. Skill relative to zero change.
3. Bias and 90th-percentile error.
4. Held-out-state geographic transfer.
5. One-year error by housing composition.
6. Similarity representation diagnostics.
7. Forecast-origin stability.

These figures answer development questions and must be labeled as validation evidence. They do
not replace the final three figures above.

## Reproduce

```powershell
databricks bundle run model_evaluation_figures --profile neighborhood-twin -t team
databricks bundle run forecast_final_evaluation_figures --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

Both workflows publish their manifest only after every expected PNG passes a file-size and count
check. The final-forecast workflow reads frozen results and never fits or changes a model.

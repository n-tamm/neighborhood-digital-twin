# Forecast Baseline Workflow

**Databricks job:** `500 Modeling | Forecast Baselines`

**Notebook:** [`01_run_forecast_baselines.py`](../../notebooks/05_modeling/01_run_forecast_baselines.py)

## Inputs

The notebook reads `workspace.neighborhood_twin_gold.gold_modeling_panel` by default. Its widgets
allow catalog, schema, input table, output table, regularization, and MLflow experiment paths to be
changed explicitly. The default regularization is `0.05`.

## Execution sequence

1. Locate the deployed repository `src` directory and import the reusable package.
2. Resolve widget values and read the governed modeling panel.
3. Create the parent Workspace folder for the shared MLflow experiment if it does not exist.
4. Start a run in `/Shared/neighborhood-digital-twin/forecast-baselines`.
5. Log the target, validation-only role, locked-test prohibition, regularization value, feature
   count, and exact feature registry.
6. Call `build_forecast_baseline_run()`.
7. Log overall model-and-horizon metrics to MLflow.
8. Overwrite the model prediction and evaluation scorecard Delta tables.
9. Fail publication if a non-validation prediction or empty scorecard slice is present.

## Outputs

| Output | Schema | Role |
|---|---|---|
| [`forecast_baseline_prediction`](../data/47_model_forecast_baseline_prediction.md) | `neighborhood_twin_model` | One validation prediction per tract, origin, horizon, and method |
| [`forecast_baseline_scorecard`](../data/48_evaluation_forecast_baseline_scorecard.md) | `neighborhood_twin_evaluation` | One model, horizon, slice, and slice-value summary |
| MLflow run | Shared experiment | Parameters, aggregate metrics, run ID, and comparison lineage |

The initial prediction table contains 1,369,401 validation predictions across 59,562 tracts and
six methods. The scorecard contains 1,248 sliced rows.

## Reproduction

After upstream model-readiness tables exist and the bundle is deployed:

```powershell
databricks bundle run forecast_baselines --profile neighborhood-twin -t team
databricks bundle run model_evaluation_figures --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

The evaluation job should follow because its figures must use the new forecast run. The metadata
job should follow because the model job overwrites current Delta schemas.

## Operational boundaries

- The job is independent of the similarity job once both upstream inputs exist.
- It does not run source acquisition or rebuild the gold modeling panel.
- It does not serialize or register an application model.
- It does not publish predictions for calibration or locked-test roles.

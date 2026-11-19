# Forecast Baseline Workflow

**Databricks job:** `500 Modeling | Forecast Baselines`

**Notebook:** [`01_run_forecast_baselines.py`](../../notebooks/05_modeling/01_run_forecast_baselines.py)

## Inputs

The notebook reads `workspace.neighborhood_twin_gold.gold_modeling_panel` by default. That panel
must be rebuilt from the governed historical targets, stable-cross-vintage feature rules, and
split assignments before fitting. Its
widgets allow catalog, schema, input table, output table, regularization, and MLflow experiment
paths to be changed explicitly. The model runner filters to the active one- and three-year
horizons, even if an existing input panel also contains legacy five-year rows. The default
regularization is `0.05`.

## Execution sequence

1. Locate the deployed repository `src` directory and import the reusable package.
2. Resolve widget values and read the governed modeling panel.
3. Create the parent Workspace folder for the shared MLflow experiment if it does not exist.
4. Start a run in `/Shared/neighborhood-digital-twin/forecast-baselines`.
5. Log the target, validation-only role, locked-test prohibition, GBT search space and selected
   per-horizon parameters/CV evidence, feature count, and exact feature registry.
6. Call `build_forecast_baseline_run()`.
7. Log overall model-and-horizon metrics to MLflow.
8. Overwrite the model prediction and evaluation scorecard Delta tables.
9. Fail publication if a non-validation prediction or empty scorecard slice is present.

## Outputs

| Output | Schema | Role |
|---|---|---|
| [`forecast_baseline_prediction`](../data/47_model_forecast_baseline_prediction.md) | `neighborhood_twin_model` | One validation prediction per tract, origin, active horizon, and method |
| [`forecast_baseline_scorecard`](../data/48_evaluation_forecast_baseline_scorecard.md) | `neighborhood_twin_evaluation` | One model, active horizon, slice, and slice-value summary |
| MLflow run | Shared experiment | Parameters, aggregate metrics, run ID, and comparison lineage |

The corrected November 19, 2026 run (`f51ad8ff85c44fe5bbd665b20520f6e4`) scores the active one-
and three-year horizons. Every fitted label ends before its validation origin. Cross-2020 feature
rows are restricted to the stable tract cohort, while fully observed FHFA outcomes remain usable.
The run's scorecard is the frozen development evidence used by job 504; it does not include the
locked-test outcome.

The GBT tuning implementation uses the latest three eligible training origins as expanding
validation folds and only earlier origins with target endpoints strictly before the held-out
origin for fitting. It selects by mean fold MAE from a six-configuration depth/iteration grid.
Horizons with fewer than two usable purged folds retain the fixed depth-4/50-iteration settings.
The tuning choices, fold years, selected CV MAE, and each grid candidate's CV MAE are logged to
MLflow; the published validation scorecard remains the untouched final comparison.

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

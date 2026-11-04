# Model Evaluation Figure Workflow

**Databricks job:** `600 Evaluation | Model Diagnostics`

**Notebook:** [`03_render_model_evaluation.py`](../../notebooks/05_modeling/03_render_model_evaluation.py)

## Purpose

The workflow creates a matched, versioned visual review of the current forecast and similarity
runs. It does not retrain models, recalculate matches, or select a champion. It reads governed
evaluation tables, verifies run lineage, renders seven PNGs, and publishes a manifest.

## Inputs

- `workspace.neighborhood_twin_evaluation.forecast_baseline_scorecard`
- `workspace.neighborhood_twin_evaluation.similarity_baseline_summary`

The renderer expects exactly one current run ID from each input. The output manifest records both
IDs, so a figure set can be traced to the model runs that produced it.

## Publication sequence

1. Read and validate the current scorecard and similarity summary.
2. Resolve their forecast and similarity MLflow run IDs.
3. Create a unique evaluation build directory in the managed volume.
4. Render the seven figures with stable filenames and shared style rules.
5. Record title, purpose, path, byte size, build ID, and both source run IDs.
6. Fail unless exactly seven figures are present and every file exceeds 10,000 bytes.
7. Overwrite `model_evaluation_figure_manifest` only after the checks pass.

## Outputs

- Volume: `workspace.neighborhood_twin_evaluation.model_evaluation_figures`
- Manifest:
  [`workspace.neighborhood_twin_evaluation.model_evaluation_figure_manifest`](../data/51_evaluation_model_evaluation_figure_manifest.md)
- Current build and export instructions:
  [Model Evaluation Figures](../../reports/MODEL_EVALUATION_FIGURES.md)

## Reproduction

Jobs 500 and 501 must finish successfully before the evaluation figure job:

```powershell
databricks bundle run forecast_baselines --profile neighborhood-twin -t team
databricks bundle run similarity_baselines --profile neighborhood-twin -t team
databricks bundle run model_evaluation_figures --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

Forecast and similarity can run independently after their upstream tables exist. The figure job
must wait for both so its manifest describes one consistent pair of runs.

## Current boundary

The workflow displays development evidence from jobs 500 and 501. It does not yet visualize the
separate job-502 historical-analogue results, calibrated uncertainty, a nonlinear comparison,
application evaluation, or locked temporal test results.

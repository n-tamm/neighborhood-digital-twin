# Forecasting Documentation

This folder documents the implemented forecast baseline, from target definition through the
published validation results. The files separate analytical design decisions from code behavior
so a model change can update the affected document without rewriting one large overview.

## Documentation map

1. [Target and split design](target_and_split_design.md) defines the outcome, horizons, analytical
   cohorts, temporal roles, geographic holdouts, and leakage controls.
2. [Baseline model design](baseline_model_design.md) explains why each of the seven implemented
   methods exists and what comparison it provides.
3. [Forecasting module](forecasting_module.md) documents
   [`src/neighborhood_twin/forecasting.py`](../../src/neighborhood_twin/forecasting.py), including
   preprocessing, features, predictions, and scorecard construction.
4. [Baseline workflow](baseline_workflow.md) documents the Databricks notebook, MLflow tracking,
   output tables, and publication guards.
5. [Evaluation and current results](evaluation_and_results.md) defines each metric and records what
   the current validation run does and does not establish.
6. [Local meeting-demo notebook](../../notebooks/05_modeling/06_local_forecast_demo.ipynb) downloads
   and caches a deterministic 500-tract subset of the governed one-year `gold_modeling_panel`
   training and validation rows. It reuses the production feature registry, fits local
   scikit-learn equivalents, and explains subset metrics and limitations. It also renders the
   published forecasting-relevant EDA figures 2, 3, 4, 5, 7, and 8 from small aggregate-table
   downloads. Install local dependencies with `py -3.11 -m pip install -e ".[local-forecast]"`;
   Databricks CLI OAuth is needed only to download or refresh the local cache. These subset results
   are not the national Spark ML scorecard. The separate
   [command-line demo](../../scripts/forecast_demo.py) remains a synthetic-data proof of concept.
7. The equivalent [command-line demo](../../scripts/forecast_demo.py) is available when a
   notebook interface is not convenient.

The current implementation is for development only. Calibration, prediction intervals, final model
selection, and locked-test evaluation are not yet implemented.

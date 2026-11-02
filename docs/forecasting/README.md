# Forecasting Documentation

This folder documents the implemented forecast baseline, from target definition through the
published validation results. The files separate analytical design decisions from code behavior
so a model change can update the affected document without rewriting one large overview.

## Documentation map

1. [Target and split design](target_and_split_design.md) defines the outcome, horizons, analytical
   cohorts, temporal roles, geographic holdouts, and leakage controls.
2. [Baseline model design](baseline_model_design.md) explains why each of the six implemented
   methods exists and what comparison it provides.
3. [Forecasting module](forecasting_module.md) documents
   [`src/neighborhood_twin/forecasting.py`](../../src/neighborhood_twin/forecasting.py), including
   preprocessing, features, predictions, and scorecard construction.
4. [Baseline workflow](baseline_workflow.md) documents the Databricks notebook, MLflow tracking,
   output tables, and publication guards.
5. [Evaluation and current results](evaluation_and_results.md) defines each metric and records what
   the current validation run does and does not establish.

The current implementation is a development baseline. Calibration, prediction intervals, a
nonlinear candidate, final model selection, and locked-test evaluation are not yet implemented.

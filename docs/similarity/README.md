# Similarity Documentation

This folder documents the implemented current-state neighborhood similarity baseline. The
workflow compares two representations of the same public features for a small, deterministic set
of review queries. It is a representation test, not yet a historical-analogue or recommendation
system.

## Documentation map

1. [Representation design](representation_design.md) explains the feature set, transformations,
   raw standardized space, PCA space, distance rule, and current design boundaries.
2. [Similarity module](similarity_module.md) documents
   [`src/neighborhood_twin/similarity.py`](../../src/neighborhood_twin/similarity.py) function by
   function.
3. [Baseline workflow](baseline_workflow.md) documents the Databricks notebook, deterministic
   query selection, MLflow tracking, and output tables.
4. [Evaluation and current results](evaluation_and_results.md) explains the unsupervised
   diagnostics and the current raw-versus-PCA findings.

The future time-safe historical-analogue workflow, later-outcome evaluation, app-serving matches,
and clustering are not implemented and are not presented here as current results.

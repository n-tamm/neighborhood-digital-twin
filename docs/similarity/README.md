# Similarity Documentation

This folder documents the implemented current-state neighborhood similarity baseline. The
workflow compares two representations of the same public features for a small, deterministic set
of review queries. A separate historical-analogue implementation is now being added so matches
can be evaluated by what happened after an earlier community state.

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
5. [Historical analogue design](historical_analogue_design.md) freezes the time-safety rule,
   historical feature representation, candidate policy, outcome estimates, and evaluation design
   for the retrospective workflow.

The current-state baseline remains useful as a representation check. Historical results will be
documented separately after the new Databricks workflow completes. App-serving matches and
clustering are not yet implemented.

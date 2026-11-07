# `historical_analogue_audit_match`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.historical_analogue_audit_match`
- **Grain and key:** one validation query tract, origin, horizon, audit variant, and match rank.
- **Purpose:** preserves the individual historical matches returned under every declared stability
  and candidate-policy variant.

The table is generated from the exact query set published by job 502. It contains two rerun
baselines, ten small feature-family weight changes, five feature-family ablations, two alternate
PCA dimensions, and two distinct-candidate-tract variants. Each row retains the candidate's
location, historical year, known later FHFA outcome, distance, rank, model settings, and source
run lineage.

The exactness fields matter. The two baselines are exact national searches. Small weight and
distinct-tract variants are marked exact only when their top-ten boundary is strictly inside a
mathematical lower bound for every candidate excluded from the baseline shortlist. Ablations and
alternate PCA dimensions are bounded stress tests and should not be described as exact national
retrieval.

The first live job-601 publication is pending. A repository sample and observed row counts should
be added only after that run passes baseline reconciliation and table validation.

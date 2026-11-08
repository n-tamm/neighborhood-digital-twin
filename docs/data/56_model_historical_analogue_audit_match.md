# `historical_analogue_audit_match`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.historical_analogue_audit_match`
- **Sample:** [historical_analogue_audit_match.jsonl](../../data/samples/historical_analogue_audit_match.jsonl)
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

The validated November 7 audit contains 6,720 rows: 32 queries, 21 variants, and ten matches per
query and variant. It has one audit run ID and one source job-502 run ID. Read-only reconciliation
found no self-matches, future outcomes, nonvalidation queries, or incomplete top-ten groups.

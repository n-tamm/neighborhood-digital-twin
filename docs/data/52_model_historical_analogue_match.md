# `historical_analogue_match`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.historical_analogue_match`
- **Sample:** [historical_analogue_match.jsonl](../../data/samples/historical_analogue_match.jsonl)
- **Grain and key:** one validation query tract, query origin, horizon, representation, and match
  rank.
- **Purpose:** preserves the individual earlier tract-year examples behind each historical
  analogue estimate.

Every candidate uses the same horizon as the query, comes from the geographic-development states,
has a different tract identifier, and has a later outcome ending no later than the query origin.
The table includes query and candidate geography, cohort, candidate age, rank, distance, observed
later candidate outcome, and MLflow run lineage.

This table is the evidence behind the summary estimate. Distances can be compared within the same
representation and run, but not between weighted standardized and PCA spaces as though they share
one unit. The candidate outcome is FHFA single-family HPI change and should not be described as
whole-market or causal neighborhood change.

The November 3 development run contains 640 rows: 16 queries per horizon, two horizons, two
representations, and ten matches per query and representation.

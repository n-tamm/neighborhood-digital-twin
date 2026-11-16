# `current_analogue_match`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.current_analogue_match`
- **Sample:** [current_analogue_match.jsonl](../../data/samples/current_analogue_match.jsonl)
- **Grain and key:** one selected current query tract, query origin year, horizon, and match rank.
- **Purpose:** retains the ten exact historical communities returned under the frozen
  weighted-standardized representation, including candidate location, year, distance, observed
  later FHFA outcome, time-safety fields, and MLflow lineage.
- **Safeguards:** the same tract is excluded, each result uses a distinct candidate tract, the
  candidate outcome must end by the query as-of year, and locked temporal-test rows are prohibited.

This is model evidence rather than a compact application serving table. It is limited to current
queries that have model-ready FHFA and ACS features. The candidate outcome describes what happened
historically and does not guarantee the selected neighborhood will follow the same path.

The first validated run contains 60 rows: ten matches for each of three selected 2025 query tracts
at the one- and three-year horizons. Direct checks found no incomplete top tens, repeated physical
candidates within a result, self-matches, future outcomes, locked test rows, or representation
drift. The run ID is `ff3ad7a038ce4d4180110a7a9adcbab1`.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

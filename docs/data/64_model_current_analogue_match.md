# `current_analogue_match`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.current_analogue_match`
- **Sample:** Added after the first validated live run.
- **Grain and key:** one selected current query tract, query origin year, horizon, and match rank.
- **Purpose:** retains the ten exact historical communities returned under the frozen
  weighted-standardized representation, including candidate location, year, distance, observed
  later FHFA outcome, time-safety fields, and MLflow lineage.
- **Safeguards:** the same tract is excluded, each result uses a distinct candidate tract, the
  candidate outcome must end by the query as-of year, and locked temporal-test rows are prohibited.

This is model evidence rather than a compact application serving table. It is limited to current
queries that have model-ready FHFA and ACS features. The candidate outcome describes what happened
historically and does not guarantee the selected neighborhood will follow the same path.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

# `gold_application_demo_tract`

[Back to the data documentation index](README.md)

- **Layer:** Gold current products
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_application_demo_tract`
- **Sample:** [gold_application_demo_tract.jsonl](../../data/samples/gold_application_demo_tract.jsonl)

- **Grain and key:** one row per displayable, current-profile tract in the configured demo states.
- **Purpose:** gives the application team a small but realistic table for map, filter, detail-panel,
  and API work before nationwide performance is necessary.
- **Current configuration:** Arizona, Michigan, and Pennsylvania.
- **Caution:** this table is a development convenience. It does not narrow the national similarity
  goal or define the final application's coverage.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

# `forecast_release_gate`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.forecast_release_gate`
- **Sample:** [forecast_release_gate.jsonl](../../data/samples/forecast_release_gate.jsonl)
- **Grain and key:** one active horizon and finalization run.
- **Purpose:** records the reproducible decision to publish or withhold a forecast horizon.

A horizon must have at least 1,000 locked observations, perform no worse than the zero-change baseline on MAE, and achieve at least 80 percent empirical coverage for its nominal 90 percent interval. The one-year model passes: its locked MAE is 0.0599 versus 0.0627 for zero change, and coverage is 89.4 percent. The three-year model fails: its MAE is 0.2943 versus 0.1566 for zero change, and coverage is 48.2 percent.

The failed horizon remains visible as an unavailable state rather than being replaced after the fact. This table is the only approval source used by the serving workflow, which keeps application behavior aligned with the documented evaluation.

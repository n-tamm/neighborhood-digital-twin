# `serving_forecast_current`

[Back to the data documentation index](README.md)

- **Layer:** Application serving
- **Databricks table:** `workspace.neighborhood_twin_serving.serving_forecast_current`
- **Sample:** [serving_forecast_current.jsonl](../../data/samples/serving_forecast_current.jsonl)
- **Grain and key:** one serving release, current tract, and approved horizon.
- **Purpose:** gives the application a compact, release-approved forecast contract without querying the wide modeling panel.

The current release contains 46,719 one-year forecasts from 2025 to 2026. Each row includes the selected model, point estimate, calibrated lower and upper bounds, baseline comparison, location labels, locked-test evidence, scope notes, and source lineage. No three-year row is published because that horizon failed the locked release gate.

The target is change in FHFA single-family tract HPI, not an individual property value or a measure of every type of housing. The driver summary is a global feature-family finding and must not be presented as a tract-level causal explanation.

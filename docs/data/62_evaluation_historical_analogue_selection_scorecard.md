# `historical_analogue_selection_scorecard`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.historical_analogue_selection_scorecard`
- **Grain and key:** one prediction method, horizon, evaluation slice, and slice value.
- **Purpose:** measures later-outcome accuracy for analogue estimates and forecast comparators on
  the identical expanded validation queries.

Metrics include MAE, RMSE, median and 90th-percentile absolute error, signed bias, R-squared,
directional behavior, and skill over zero change. Results are sliced by time, region, transfer
role, modeling cohort, housing composition, community size, and ACS uncertainty.

This table supports representation selection; it does not open the locked temporal test. Live
results and a real sample will be added after the first validated job-602 publication.

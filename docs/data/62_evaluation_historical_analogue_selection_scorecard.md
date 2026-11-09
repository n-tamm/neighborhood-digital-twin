# `historical_analogue_selection_scorecard`

[Back to the data documentation index](README.md)

- **Layer:** Evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.historical_analogue_selection_scorecard`
- **Sample:** [historical_analogue_selection_scorecard.jsonl](../../data/samples/historical_analogue_selection_scorecard.jsonl)
- **Grain and key:** one prediction method, horizon, evaluation slice, and slice value.
- **Purpose:** measures later-outcome accuracy for analogue estimates and forecast comparators on
  the identical expanded validation queries.

Metrics include MAE, RMSE, median and 90th-percentile absolute error, signed bias, R-squared,
directional behavior, and skill over zero change. Results are sliced by time, region, transfer
role, modeling cohort, housing composition, community size, and ACS uncertainty.

The validated table contains 322 rows. Weighted analogue MAE is lower than PCA overall at both
horizons: 0.0788 versus 0.0823 at one year and 0.1022 versus 0.1098 at three years when comparing
each representation's better aggregation rule. The regularized-linear forecast remains more
accurate at 0.0682 and 0.0801, so analogues remain secondary historical context. This table does
not open the locked temporal test.

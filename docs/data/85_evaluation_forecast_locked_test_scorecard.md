# `forecast_locked_test_scorecard`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.forecast_locked_test_scorecard`
- **Sample:** [forecast_locked_test_scorecard.jsonl](../../data/samples/forecast_locked_test_scorecard.jsonl)
- **Grain and key:** one horizon, evaluation slice, and slice value.
- **Purpose:** summarizes final point error, bias, baseline comparisons, and interval performance on the locked period.

The 34-row table contains overall and diagnostic slices. On 42,082 one-year rows, the gradient-boosted champion has MAE 0.0599 in cumulative log change and 89.4 percent interval coverage, close to its 90 percent target. On 45,887 three-year rows, the state-trend champion has MAE 0.2943 and only 48.2 percent coverage. Its strong negative signed error shows systematic overprediction in this locked period.

The one-year result is suitable for release, while the three-year result is not. The scorecard is evidence, not the release decision itself; `forecast_release_gate` applies the predeclared minimum observation, baseline-skill, and coverage requirements.

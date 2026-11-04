# `historical_analogue_prediction`

[Back to the data documentation index](README.md)

- **Layer:** Model outputs
- **Databricks table:** `workspace.neighborhood_twin_model.historical_analogue_prediction`
- **Sample:** [historical_analogue_prediction.jsonl](../../data/samples/historical_analogue_prediction.jsonl)
- **Grain and key:** one validation query tract, query origin, horizon, and prediction method.
- **Purpose:** places historical-analogue estimates and selected forecasting comparators on the
  same deterministic query sample.

The four analogue methods combine median or inverse-distance outcomes with weighted-standardized
or PCA retrieval. Zero change, current state trend, and regularized linear predictions are copied
from the existing forecast baseline output for the identical queries. The table carries observed
and predicted cumulative log change, a readable annualized percentage, residual and absolute
error, descriptive analogue outcome bounds, and run lineage.

The analogue 10th and 90th percentiles describe what happened across the matched examples. They
are not calibrated uncertainty intervals. The table is a development comparison rather than an
approved application-serving forecast.

The November 3 development run contains 224 rows: 32 query-and-horizon cases evaluated under four
analogue methods and three forecast comparators.

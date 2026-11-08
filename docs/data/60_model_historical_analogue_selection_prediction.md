# `historical_analogue_selection_prediction`

[Back to the data documentation index](README.md)

- **Layer:** Model output
- **Databricks table:** `workspace.neighborhood_twin_model.historical_analogue_selection_prediction`
- **Grain and key:** one expanded validation query, horizon, and prediction method.
- **Purpose:** compares analogue outcome summaries and the fixed forecast comparators on exactly
  the same expanded query rows.

The analogue methods are the median and inverse-distance outcome under weighted-standardized and
PCA retrieval. Forecast comparators are zero change, current state trend, and regularized linear.
The table also retains the descriptive 10th-to-90th percentile analogue outcome range plus the
query housing-composition, community-size, and ACS-uncertainty bands used for subgroup review.

The analogue range is historical variation, not a calibrated forecast interval. Live row counts
and a real sample will be added after the first validated job-602 publication.

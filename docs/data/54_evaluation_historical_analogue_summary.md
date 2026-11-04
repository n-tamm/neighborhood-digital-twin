# `historical_analogue_summary`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.historical_analogue_summary`
- **Sample:** [historical_analogue_summary.jsonl](../../data/samples/historical_analogue_summary.jsonl)
- **Grain and key:** one horizon, representation, and historical analogue run.
- **Purpose:** describes how the two historical retrieval representations behave before outcome
  accuracy is considered.

The table reports query and match counts, distance percentiles, candidate age, cross-state and
same-county shares, PCA explained variance, and the mean top-k overlap between weighted
standardized and PCA matches. High overlap means the two methods often return the same examples;
low overlap means the representation choice materially changes the evidence shown to a user.

These are unsupervised retrieval diagnostics, not measures of future-outcome accuracy. Read them
with `historical_analogue_scorecard` and reviewed match examples rather than selecting a method
from explained variance alone.

The November 3 development run contains four rows, one for each combination of the one- and
three-year horizons with the weighted-standardized and PCA representations.

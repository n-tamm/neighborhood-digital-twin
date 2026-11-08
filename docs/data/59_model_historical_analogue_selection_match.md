# `historical_analogue_selection_match`

[Back to the data documentation index](README.md)

- **Layer:** Model output
- **Databricks table:** `workspace.neighborhood_twin_model.historical_analogue_selection_match`
- **Sample:** [historical_analogue_selection_match.jsonl](../../data/samples/historical_analogue_selection_match.jsonl)
- **Grain and key:** one expanded validation query, representation, and match rank.
- **Purpose:** retains the exact historical evidence used to compare the provisional weighted
  representation with PCA on a larger validation sample.

Each query receives ten weighted-standardized and ten PCA matches. The workflow first keeps the
closest historical state for each candidate GEOID, so every top-ten list contains ten distinct
physical communities. Candidate outcomes end no later than the query origin, and self-matches are
prohibited.

The validated table contains 3,560 rows: 88 one-year queries and 90 three-year queries, with ten
matches from both representations for each query. It contains locations and years,
representation and distance, rank, candidate age, later
candidate outcome, the distinct-tract policy, and both historical-analogue and selection-run
lineage. It is evaluation evidence, not an application serving table.

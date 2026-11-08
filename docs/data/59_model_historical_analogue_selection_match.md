# `historical_analogue_selection_match`

[Back to the data documentation index](README.md)

- **Layer:** Model output
- **Databricks table:** `workspace.neighborhood_twin_model.historical_analogue_selection_match`
- **Grain and key:** one expanded validation query, representation, and match rank.
- **Purpose:** retains the exact historical evidence used to compare the provisional weighted
  representation with PCA on a larger validation sample.

Each query receives ten weighted-standardized and ten PCA matches. The workflow first keeps the
closest historical state for each candidate GEOID, so every top-ten list contains ten distinct
physical communities. Candidate outcomes end no later than the query origin, and self-matches are
prohibited.

The table contains locations and years, representation and distance, rank, candidate age, later
candidate outcome, the distinct-tract policy, and both historical-analogue and selection-run
lineage. It is evaluation evidence, not an application serving table.

Live row counts and a real sample will be added after the first validated job-602 publication.

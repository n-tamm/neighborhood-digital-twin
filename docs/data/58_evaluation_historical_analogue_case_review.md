# `historical_analogue_case_review`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:**
  `workspace.neighborhood_twin_evaluation.historical_analogue_case_review`
- **Sample:** [historical_analogue_case_review.jsonl](../../data/samples/historical_analogue_case_review.jsonl)
- **Grain and key:** one selected validation query, baseline representation, and match rank.
- **Purpose:** provides the feature-level evidence needed to decide whether retrieved historical
  matches make substantive sense.

Cases are selected by deterministic rules rather than attractive outcomes. The set includes
regional and geographic-role coverage, the lowest weighted-versus-PCA overlap, the largest mean
match distance, and any query with repeated historical states from the same physical tract. The
query's later outcome is not used to select cases.

Each row includes the governed query and candidate feature arrays, absolute standardized gaps,
average gaps for the five feature families, the closest feature, and the largest feature
difference. These fields explain the data used by retrieval; they should not be interpreted as
evidence about amenities or lived experience that the model does not contain. Human review notes
remain a later analytical step and are not generated automatically by this table.

The validated November 7 table contains 600 match rows for 30 selected queries and both baseline
representations. Representative review found that weighted-standardized matches usually keep the
five family-level gaps visible and balanced. Several PCA examples looked close in compressed
space while retaining a large market-trajectory or housing-structure gap, which is one reason PCA
was not selected as the application representation after expanded evaluation.

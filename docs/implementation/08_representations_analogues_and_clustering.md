# 08 — Representations, Historical Analogues, and Clustering

## Purpose

The analogue system answers a different question from the forecast model: which earlier neighborhood states looked most like this tract now, and what happened afterward? It should be useful even to someone who does not care about a two-dimensional embedding plot.

## Representation baseline

Start with a small, interpretable set of standardized state dimensions. Fit scaling on the training period and compare two representations:

1. distance in the standardized original feature space;
2. principal component analysis followed by distance in the retained components.

Choose component count through explained variance, stability, and downstream analogue results—not only a visual elbow. UMAP can support a map-like visualization, but it should not become the retrieval metric without evidence because it can distort global distances.

## Time-safe retrieval

For a query tract at forecast origin `t`:

- search only tract-years earlier than `t`;
- optionally exclude the same tract and immediate neighbors;
- apply any metro, region, or period filters explicitly;
- return rank, distance, shared strengths, and important differences;
- attach the analogue's later one- and three-year outcomes when available;
- retain the representation and feature versions.

This prevents a current state from retrieving its own future or near-duplicate row.

## Distance and weighting

Begin with Euclidean distance after documented standardization. Consider cosine or a weighted distance only if the project can explain the tradeoff and evaluate it. Do not let high-cardinality feature families dominate merely because they have more columns.

Feature-family weighting can reflect project priorities, but weights must be configured, versioned, and sensitivity-tested. A housing-only analogue and a broader community-state analogue may both be useful if the app labels them honestly.

## Evaluation

Analogue quality is not established by visually appealing matches. Compare the average later outcome of the nearest analogues with:

- random historical tract-years from the same period;
- random matches within the same metro or region;
- persistence and regional forecasts;
- the supervised forecast model.

Measure outcome MAE or rank usefulness, neighbor stability under bootstrap or feature changes, distance separation, geographic diversity, and coverage. Review case studies for obvious mismatches that a metric misses.

## Optional trajectory clustering

After the analogue system works, cluster sequences of state change rather than only single-year states. A good first baseline is multivariate functional PCA followed by k-means, which aligns with prior neighborhood-trajectory research. Compare with simpler sequence summaries before considering deep or graph embeddings.

Evaluate cluster stability across seeds, time windows, feature subsets, and geography. Assign plain-language descriptions only after examining profiles. Avoid labels such as improving, declining, desirable, or risky unless they refer to a precisely defined measure and are essential to the research.

## Required outputs

- fitted scaler and representation object;
- versioned representation table;
- time-safe `gold_analogues` table;
- analogue evaluation against random and forecast baselines;
- stability analysis and reviewed case studies;
- app-ready similarity explanations;
- optional trajectory clusters and stability evidence.

## Acceptance checks

- no retrieved analogue occurs at or after the query forecast origin;
- training-period scaling is reused for later queries;
- distance calculations are deterministic and versioned;
- the same tract and immediate neighbors follow the configured exclusion rule;
- analogue usefulness is compared with honest baselines;
- app text states that similarity does not guarantee the same future;
- optional embeddings or clusters add evidence beyond a visualization.

## Handoff

The app receives a compact analogue table and display definitions. The scenario engine may use analogues for historical plausibility checks, but the two components should not become circular: a forecast should not be evaluated against analogues selected using its future outcome.

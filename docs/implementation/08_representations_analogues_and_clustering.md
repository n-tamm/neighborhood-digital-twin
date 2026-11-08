# 08 — Representations, Historical Analogues, and Clustering

## Purpose

The analogue system answers a different question from the forecast model: which earlier neighborhood states looked most like this tract now, and what happened afterward? It should be useful even to someone who does not care about a two-dimensional embedding plot.

## Representation baseline

`gold_model_feature_historical` now supplies the point-in-time raw state needed for retrospective
retrieval. It includes broad community descriptors, FHFA history, county/state context, source
timing, and uncertainty fields, but it deliberately does not contain a fitted scaler, feature
weights, PCA, or imputation. Those objects must be learned from the approved development period
and reused unchanged for validation, test, and current-state queries.

Start with a small, interpretable set of standardized state dimensions. The first representation should include housing-stock composition, affordability, tenure or vacancy, single-family HPI history, selected socioeconomic context, and regional conditions. This prevents a tract from being labeled similar only because its covered single-family market moved the same way. Fit scaling on the training period and compare two representations:

1. distance in the standardized original feature space;
2. principal component analysis followed by distance in the retained components.

Choose component count through explained variance, stability, and downstream analogue results—not only a visual elbow. UMAP can support a map-like visualization, but it should not become the retrieval metric without evidence because it can distort global distances.

### Implemented current-state scaffold

Job `501 Modeling | Similarity Baselines` now creates a deliberately small review set from the
current national candidate table. Population, housing-unit, income, value, and rent fields use a
`log1p` transform; all fields are median-imputed and standardized. The job compares exact
Euclidean neighbors in the standardized feature space with exact neighbors in a six-component
PCA space. It records explained variance, distance distributions, cross-state match share, and
raw-versus-PCA top-k overlap in MLflow and dedicated model and evaluation tables.

This remains a representation sanity check rather than the historical-analogue system. It fits the
current candidate population and uses a small deterministic query set.

The first shared run completed on October 30, 2026. Six PCA components retain 95.5% of the
standardized variance. Both representations return geographically broad matches: 91.7% of raw
matches and 95.0% of PCA matches cross a state boundary. However, their top-10 lists overlap by
only 5.5 communities on average. Compression is not simply reproducing the raw ranking, so the
team needs to inspect shared strengths and important differences for the six queries before
choosing either representation. Explained variance alone is not enough to select PCA.

## Time-safe retrieval

### Implemented historical development workflow

Job `502 Modeling | Historical Analogue Baseline` now performs the first retrospective test for
one- and three-year horizons. It fits median imputation, standardization, equal feature-family
weights, and six-component PCA on training rows only. It then samples validation queries across
origin year, Census region, and geographic role and returns ten exact matches from both weighted
standardized and PCA space.

Candidates come only from the geographic-development states. They must have the same horizon, a
different tract identifier, and an observed target ending no later than the query origin. This
last condition is stricter and clearer than requiring only an earlier candidate state:

```text
candidate origin + horizon <= query origin
```

The resulting match, prediction, retrieval-summary, and scorecard tables live in the model and
evaluation schemas. The [similarity documentation](../similarity/README.md) records the exact
feature registry, runtime behavior, current results, and interpretation limits.

Job `601 Evaluation | Historical Analogue Audit` now reproduces the published job-502 baselines,
selects deterministic review cases, and evaluates 21 feature-weight, family-ablation, PCA, and
candidate-policy variants on every development query. Its validated output contains 6,720 match
rows, 672 complete query-variant summaries, and 600 case-review rows. Small family-weight changes
retain 93.4% of weighted neighbors on average, while alternate PCA dimensions retain 50.9% of the
six-component list. Reviewed PCA matches can be close in compressed space while retaining a large
gap in an original feature family.

Weighted standardized distance is consequently the provisional application representation, and
the application should return one historical state per physical candidate tract. The latter rule
retains 93.1% of baseline neighbors while removing repeated-community results. PCA and the
tract-year rule remain available for model audit. These are development decisions rather than
final performance claims until the 16-query-per-horizon sample is expanded or justified.

For a query tract at forecast origin `t`:

- search only tract-years whose later outcome is already known at `t`;
- optionally exclude the same tract and immediate neighbors;
- apply any metro, region, or period filters explicitly;
- return rank, distance, shared strengths, and important differences;
- attach the analogue's later one- and three-year outcomes when available;
- retain the representation and feature versions.

This prevents a current state from retrieving its own future or near-duplicate row.

The cohort change also needs to be part of retrieval policy. Historical queries through 2020 are
limited to tracts with stable 2010-to-2020 geography, while the broader candidate population begins
in 2021. A cross-period search should either restrict both query and candidates to the stable
cohort or label that later candidates come from a wider tract universe. It should not treat the
extra later tracts as if they had comparable earlier history.

## Distance and weighting

Begin with Euclidean distance after documented standardization. Consider cosine or a weighted distance only if the project can explain the tradeoff and evaluate it. Do not let high-cardinality feature families dominate merely because they have more columns.

Feature-family weighting can reflect project priorities, but weights must be configured, versioned, and sensitivity-tested. A housing-only analogue and a broader community-state analogue may both be useful if the app labels them honestly.

## Evaluation

Analogue quality is not established by visually appealing matches. Evaluate it as a retrospective retrieval task:

1. choose a historical query tract-year and hide what happened next;
2. search only candidate tract-years that were already observable at that date;
3. retrieve a small set of analogues from the approved state dimensions;
4. summarize the analogues' later outcomes;
5. compare that summary with the query tract's observed later outcome.

The implemented scorecard compares analogue-based estimates with zero change, current state
trend, and the regularized linear forecast on identical query rows. Random and same-region
retrieval baselines are not yet implemented and should be considered only if the first result
cannot be interpreted cleanly against the current comparators.

Use outcome MAE when the analogue set is presented as evidence about what may follow. Also measure neighbor stability under small feature and scaling changes, balance across the displayed feature families, distance separation, geographic diversity, and coverage. The application should explain both the strongest similarities and important differences. Review case studies for obvious mismatches that a metric misses.

FHFA outcome availability should not define whether two communities are descriptively similar.
Heavily multifamily tracts may have useful ACS-based matches even when the single-family target is
missing or less representative. Keep retrieval coverage, outcome-based analogue evaluation, and
target representativeness as separate reported quantities. This avoids optimizing the entire
similarity experience around the subset of places that FHFA measures best.

## Optional trajectory clustering

After the analogue system works, cluster sequences of state change rather than only single-year states. A good first baseline is multivariate functional PCA followed by k-means, which aligns with prior neighborhood-trajectory research. Compare with simpler sequence summaries before considering deep or graph embeddings.

Evaluate cluster stability across seeds, time windows, feature subsets, and geography. Assign plain-language descriptions only after examining profiles. Avoid labels such as improving, declining, desirable, or risky unless they refer to a precisely defined measure and are essential to the research.

## Required outputs

- versioned time-safe match and prediction tables in the model schema;
- retrieval and later-outcome evaluation tables in the evaluation schema;
- MLflow parameters and metrics for the fitted development representation;
- reviewed cases and a documented representation decision;
- an app-ready current-query match table after the development rule is frozen;
- app-ready shared-strength and important-difference explanations;
- optional trajectory clusters and stability evidence.

## Acceptance checks

- no retrieved analogue has an outcome ending after the query forecast origin;
- training-period scaling is reused for later queries;
- distance calculations are deterministic and versioned;
- the same tract is excluded; immediate-neighbor exclusion is not implemented because analytical
  adjacency is not yet available;
- analogue usefulness is compared with honest baselines;
- retrieved matches remain understandable across housing mix and the other displayed dimensions;
- app text states that similarity does not guarantee the same future;
- optional embeddings or clusters add evidence beyond a visualization.

## Handoff

The app receives a compact analogue table and display definitions. The scenario engine may use analogues for historical plausibility checks, but the two components should not become circular: a forecast should not be evaluated against analogues selected using its future outcome.

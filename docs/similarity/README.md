# Similarity System

The similarity system is designed to answer:

> Which communities in the past looked most like this neighborhood, and what happened to them
> afterward?

It is related to the forecasting model, but it serves a different purpose. The forecast produces
the primary numerical prediction. Similarity provides historical examples that help a user
understand what kinds of trajectories have followed comparable neighborhood conditions.

## How the system works

### 1. Represent a neighborhood at a particular year

Each neighborhood is a census tract observed at a specific forecast-origin year. Its
representation currently includes five groups of features:

- **Community scale:** population and housing units
- **Occupancy and tenure:** occupancy and owner-occupancy rates
- **Housing structure:** single-family, multifamily, and mobile-home shares
- **Affordability:** home-value-to-income and annual-rent-to-income ratios
- **Housing-market trajectory:** recent HPI movement, volatility, and performance relative to the
  state

This is currently a housing-focused neighborhood representation, not a complete measure of lived
experience or neighborhood quality.

### 2. Make the features comparable

Population and housing-unit counts are log-transformed so very large communities do not dominate.
Missing values are median-imputed, and features are standardized.

These transformations are learned only from training-period data. Later validation communities do
not influence the scaling or imputation rules.

### 3. Balance the feature groups

Each of the five feature families receives equal overall weight. This prevents housing structure,
which has several columns, from automatically mattering more than affordability or community scale
simply because it has more variables.

### 4. Create two competing representations

The system currently tests:

- **Weighted standardized features:** distance is calculated directly from the interpretable
  features.
- **PCA representation:** the same features are compressed into six principal components before
  calculating distance.

PCA may remove redundancy, but it can also change which communities appear similar. We therefore
evaluate it rather than assuming it is better.

### 5. Select a historical query

For development evaluation, the system chooses a neighborhood at an earlier validation year and
acts as though that year were the present.

For example, it might ask: “Given what was known about this tract in 2021, which earlier
communities would have looked similar?”

### 6. Construct a time-safe candidate pool

A historical community can be used only if:

- it uses the same outcome horizon as the query;
- it is not the same census tract;
- it comes from the geographic-development states; and
- its later outcome was already observable by the query year.

The crucial rule is:

```text
candidate origin year + outcome horizon <= query origin year
```

For a three-year query in 2021, a candidate from 2018 is allowed because its three-year outcome
ends in 2021. A candidate from 2019 is rejected because its outcome would not be known until 2022.

### 7. Find the closest historical matches

The system calculates exact Euclidean distance in both representations and returns the ten closest
historical tract-years for each one.

Each result retains:

- match rank and distance;
- query and candidate locations and years;
- representation used;
- candidate age;
- the candidate's later observed HPI outcome; and
- model and MLflow lineage.

### 8. Summarize what happened afterward

The matched communities' later outcomes are combined in two ways:

- median outcome; and
- inverse-distance weighted mean, where closer matches contribute more.

The 10th and 90th percentiles are also retained to show the range of historical outcomes. That
range is descriptive; it is not a calibrated prediction interval.

### 9. Compare analogues with the forecasting system

On the same query neighborhoods, the analogue estimates are compared with:

- zero change;
- current state trend; and
- the regularized linear forecast.

The scorecard includes MAE, RMSE, tail error, bias, R-squared, directional behavior, and
improvement over zero change.

### 10. Present the evidence in the application

The planned application view will show:

- the selected neighborhood today;
- its closest historical community matches;
- why they were considered similar;
- important differences;
- what happened to those communities afterward;
- the historical outcome range; and
- the primary forecasting-model result beside the analogue-based result.

The application should describe these as comparable historical examples, not communities that are
guaranteed to follow the same path.

## Current implementation status

All six implemented similarity stages have completed validated live runs.

### Job 501: Current-state similarity baseline

- Uses six review query tracts.
- Compares standardized-feature and PCA neighbors.
- Confirmed that both methods can retrieve national rather than merely local matches.

### Job 502: Historical analogue baseline

- Evaluates time-safe historical retrieval.
- Supports one- and three-year outcomes.
- Published 640 individual matches and 224 prediction and comparator rows.
- Passed self-match, timing, validation-role, and top-ten reconciliation checks.

### Job 601: Historical analogue audit

- Reproduces the job-502 baselines before another result can be published.
- Selects representative and diagnostic cases without using their later outcomes.
- Tests small feature-family weight changes, family removal, PCA dimensions, and distinct-tract
  candidate ranking on the same queries.
- Separates exact or mathematically certified retrieval from shortlist-based stress tests.
- Publishes match-level evidence, query-level stability metrics, and feature-level case-review
  evidence.

The validated run published 6,720 variant matches, 672 complete query-variant stability rows, and
600 case-review rows. Small feature-family weight changes retained 93.4% of the weighted top ten
on average and were exactness-certified. Alternate PCA dimensions retained 50.9% of the baseline
PCA list, while family removal retained 37.6% of weighted matches and confirmed that market
trajectory has the strongest influence on the current match definition.

Weighted standardized distance was the provisional application default after job 601. It was more
stable under reasonable local changes, easier to explain, and did not sacrifice a clear accuracy
advantage to PCA. The audit also supported distinct physical communities: that policy retained
93.1% of baseline matches while removing repeat years from the same tract.

### Job 602: Expanded historical analogue selection

- Expands the sample to 88 one-year and 90 three-year validation query tract-years.
- Requires ten distinct physical candidate tracts for both representations.
- Covers every eligible housing-composition, community-size, and ACS-uncertainty category, while
  labeling rare categories that have too few examples for subgroup claims.
- Finds lower overall analogue MAE for weighted matching than PCA at both horizons.
- Confirms that the regularized-linear forecast remains the stronger primary numerical estimate.

Weighted standardized distance and distinct physical candidates are now the selected application
policy. PCA remains an internal audit lens. Job 503 implements current-neighborhood retrieval for
a small configurable set of latest-year model-ready tracts while keeping locked temporal-test
outcomes unavailable.

### Job 503: Current analogue retrieval

- Applies the selected weighted representation to neighborhoods at the latest model-ready year.
- Published ten distinct one-year and three-year historical matches for one Arizona, Michigan,
  and Pennsylvania tract in the first validated run.
- Excludes same-tract results, future candidate outcomes, and every locked temporal-test row.
- Publishes the median, inverse-distance summary, and 10th-to-90th percentile historical outcome
  range as context rather than a calibrated interval.
- Took about 14 minutes for three query tracts, so exact retrieval is the audit reference rather
  than the intended interactive serving method.

The current historical representation can serve 46,719 tracts with 2025 model-ready features.
The broader ACS similarity cohort contains 83,359 tracts. Unsupported tracts therefore need an
explained unavailable state or a separately evaluated ACS-only method; they must not be passed
through an invisible change to the selected representation.

### Job 603: Scalable retrieval benchmark

- Compares three deterministic random-projection LSH shortlists with exhaustive exact retrieval
  for 29 stratified current queries at one- and three-year horizons.
- Adds separate physical-community and tract-year-state recall so a different historical year
  cannot be hidden behind the same tract identifier.
- Covers every required region, cohort, housing-composition, community-size, and ACS-uncertainty
  category without using later outcomes to select queries.
- Finds perfect community recall, but the tested shortlists retain 88.7% to 99.9% of all possible
  pairs and are roughly three to five times slower than exact retrieval within the cached run.

The tested LSH design is rejected for application serving. This is useful engineering evidence:
high recall came from doing nearly all of the original work. The next retrieval design should use
bounded exact precomputation or a materially more selective index and must retain the same fidelity
and timing checks.

The initial historical evaluation used 16 queries per horizon. It found that:

- approximately 95% to 97.5% of matches crossed state lines, supporting the national comparison
  idea;
- PCA retained about 83% to 84% of weighted feature variance;
- PCA and direct weighted matching shared only 20.8% to 27.1% of their top-ten matches;
- every analogue method beat zero change; and
- no analogue method beat the state-trend or regularized-linear forecast.

The analogues therefore appear to contain useful historical information, but the current evidence
does not support replacing the forecasting model with an analogue forecast. Their strongest role
is historical context and a secondary comparison.

The five-year analogue evaluation is intentionally unavailable. There is not enough earlier
model-ready history to produce leakage-safe five-year candidates for the existing validation
period.

## Visual evidence status and plan

The project currently has one generated similarity figure:
`06_similarity_representation_diagnostics.png`. It was useful for the initial current-state
baseline because it showed distance spread, geographic reach, and raw-versus-PCA overlap. It is
not enough for the final report or application story. It predates the historical analogue audit,
expanded evaluation, selected weighted representation, and current-neighborhood retrieval.

The final similarity visual package should cover three different needs:

1. **Explain the method:** a compact workflow diagram should show the five feature families,
   training-only preprocessing, equal family weighting, time-safe candidate filtering, distinct
   top-ten retrieval, and later-outcome summary.
2. **Evaluate the method:** figures should show stability under reasonable weight changes,
   weighted-versus-PCA selection evidence, analogue error beside forecast comparators, and current
   eligibility coverage. These visuals must use the governed evaluation tables rather than a few
   hand-picked examples.
3. **Present the result:** a polished case study should combine the selected tract, a map of its
   historical matches, the strongest shared characteristics and largest differences, and aligned
   later trajectories. It should make the analogue year and descriptive—not causal or
   calibrated—interpretation impossible to miss.

The first raw-versus-PCA figure can remain as development evidence, but it should not be the only
similarity figure or the main final-report visual. New figures must be versioned in Databricks,
linked to their source run IDs, documented one per file, and visually reviewed for legibility and
interpretation before report use.

The historical method, current-year lookup contract, and exact indexed retrieval are implemented
and evaluated. Job 700 now applies the KD-tree nationally and publishes versioned matches,
descriptive summaries, availability reasons, target-scope warnings, and release lineage for the
application. Deterministic match explanations, aligned trajectories, the final visual package,
and the application integration remain.

## Detailed documentation

1. [Representation design](representation_design.md) explains the feature set, transformations,
   current-state standardized space, PCA space, distance rule, and design boundaries.
2. [Current-state similarity module](similarity_module.md) documents
   [`src/neighborhood_twin/similarity.py`](../../src/neighborhood_twin/similarity.py) function by
   function.
3. [Current-state baseline workflow](baseline_workflow.md) documents the first Databricks
   notebook, deterministic query selection, MLflow tracking, and output tables.
4. [Current-state evaluation and results](evaluation_and_results.md) explains the unsupervised
   diagnostics and initial standardized-versus-PCA findings.
5. [Historical analogue design](historical_analogue_design.md) defines the time-safety rule,
   historical feature representation, candidate policy, outcome estimates, and evaluation design.
6. [Historical analogue implementation](historical_analogue_implementation.md) explains the code,
   query sample, retrieval sequence, Databricks job, published tables, and operational checks.
7. [Historical analogue results](historical_analogue_results.md) records the completed development
   run, the diagnostic and outcome findings, and the resulting interpretation.
8. [Case review protocol](case_review_protocol.md) defines deterministic representative and
   diagnostic cases, the evidence reviewers inspect, and the repeated-community decision.
9. [Stability evaluation](stability_evaluation.md) defines the bounded weight, ablation, PCA, and
   candidate-uniqueness tests and the metrics used to interpret them.
10. [Expanded historical analogue evaluation](expanded_evaluation.md) explains the larger
    validation sample, distinct-community policy, sample-coverage evidence, publication gates,
    and representation-selection boundary.
11. [Current-neighborhood historical analogue retrieval](current_neighborhood_retrieval.md)
    explains the latest-year lookup, test-set safeguard, published outputs, coverage boundary,
    and path toward application serving.
12. [Scalable retrieval benchmark](scalable_retrieval.md) explains the exact reference, LSH
    shortlist configurations, fidelity measures, coverage design, and serving-selection boundary.
13. [Exact indexed retrieval](exact_tree_retrieval.md) explains the KD-tree design, exact
    distinct-community stopping rule, scale populations, decision measures, and publication
    boundary.
14. [Current analogue serving products](analogue_serving_products.md) explains the national batch
    release, table grains, activation manifest, validation gates, and application reading rule.

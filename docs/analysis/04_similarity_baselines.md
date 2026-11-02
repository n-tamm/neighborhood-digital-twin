# Similarity Baselines

The current similarity workflow asks whether a small, interpretable set of public neighborhood
features can retrieve plausible communities from across the country. It compares two ways of
representing the same current tract state. Its purpose is to expose representation choices and
produce cases the team can inspect before building historical analogues.

It does not yet answer what happened next in similar communities. The matches should not be
presented as recommendations, predictions, or an app-ready “places like this” result.

## Current input population

The workflow reads
[`gold_similarity_candidate_current`](../data/18_gold_similarity_candidate_current.md), which
contains current national tracts with positive population and housing-unit counts and the
implemented similarity features. Unlike the forecast population, this candidate definition does
not require FHFA history. That choice preserves descriptive matching for multifamily-heavy
communities and other tracts where FHFA is unavailable or less representative.

The twelve implemented features are:

| Community dimension | Features |
|---|---|
| Scale | Population and total housing units |
| Occupancy and tenure | Occupancy, vacancy, owner-occupancy, and renter-occupancy rates |
| Housing structure | Single-family, multifamily, and mobile-home shares |
| Affordability and value | Median household income, median owner-occupied value, and median gross rent |

This is a housing-focused representation. It does not currently include education, employment,
commuting, health, amenities, environment, development activity, or a measure of subjective
livability.

## Preprocessing and representations

The pipeline is fit on the current candidate population in this order:

1. Apply `log1p` to population, housing units, income, owner-occupied value, and gross rent. This
   reduces the influence of very large scale differences while retaining zero values.
2. Median-impute missing feature values.
3. Center and standardize every feature so a dollar-valued field does not dominate a rate solely
   because of its units.
4. Keep the twelve-dimensional standardized vector as the `standardized_raw` representation.
5. Fit principal component analysis and retain six components as the `pca` representation.
6. Compute exact Euclidean distance from each query to every other candidate in each space.
7. Exclude the query tract itself and return the ten smallest distances, with the tract GEOID as
   a deterministic tie-breaker.

PCA creates six weighted combinations of the standardized features that preserve as much overall
variation as possible. It can reduce redundancy, but its components are less directly
interpretable than the original features. High explained variance does not prove that PCA keeps
the distinctions users care about.

Distance is only comparable within one representation. A PCA distance of 2 and a raw-space
distance of 3 do not establish that the PCA match is “closer,” because the vector spaces have
different dimensions and scales.

## Review-query design

The implemented run uses two deterministic query tracts from each of Arizona, Michigan, and
Pennsylvania. They are selected by a stable hash of the tract GEOID rather than hand-picked for a
favorable story. Each query receives ten raw-space and ten PCA-space neighbors, producing 120
match rows in total.

The three states are a review sample, not a search boundary. Every query searches the national
candidate population. The code also accepts an explicit list of eleven-digit tract GEOIDs for a
future review run.

Exact all-candidate search is appropriate for six queries and makes the baseline easy to verify.
It is not intended as the final low-latency retrieval method for an interactive national app.

## Implemented diagnostics

| Diagnostic | What it tells us | What it does not tell us |
|---|---|---|
| PCA explained variance | How much standardized feature variation the six components retain | Whether the retained variation produces useful neighborhood matches |
| Distance percentiles and IQR | Whether retrieved distances are tightly concentrated or separated within a representation | Whether a close-looking match has a similar later outcome |
| Cross-state match share | Whether the search reaches beyond the query's state | Whether cross-state matches are substantively better |
| Same-county match share | Whether results collapse to very local near-duplicates | Whether local matches should always be excluded |
| Raw/PCA top-10 overlap | How sensitive the retrieved list is to representation choice | Which representation is correct |

These diagnostics are unsupervised evaluation measures: they examine the structure and stability
of the retrieval output when no single correct match list exists. They are necessary, but they
are not enough to establish usefulness.

## Current results

- Six PCA components retain 95.5% of standardized feature variance.
- Raw and PCA top-10 lists overlap by 5.5 tracts, or 55%, on average.
- About 91.7% of raw matches and 95.0% of PCA matches cross a state boundary.
- Both representations therefore search nationally, but they often disagree about the exact
  communities that are closest.

The moderate overlap is the most important result. PCA is not simply a compressed copy of the raw
ranking, so explained variance alone cannot choose the representation. Concrete match cases need
to be inspected for shared strengths and important differences, followed by stability and
historical-outcome evaluation.

## Outputs and reproducibility

- Workflow: `501 Modeling | Similarity Baselines`
- Implementation: [`similarity.py`](../../src/neighborhood_twin/similarity.py)
- Databricks notebook:
  [`02_run_similarity_baselines.py`](../../notebooks/05_modeling/02_run_similarity_baselines.py)
- Match table:
  [`workspace.neighborhood_twin_model.similarity_baseline_match`](../data/49_model_similarity_baseline_match.md)
- Summary table:
  [`workspace.neighborhood_twin_evaluation.similarity_baseline_summary`](../data/50_evaluation_similarity_baseline_summary.md)
- MLflow experiment: `/Shared/neighborhood-digital-twin/similarity-baselines`

The match table records query and matched tract identifiers, rank, distance, representation,
schema version, build time, and run ID. The summary table carries representation-level distance,
geography, variance, and overlap diagnostics for the same run.

## Current boundaries

- The transforms are fit to the current candidate population, not a historical development
  period.
- The workflow does not retrieve earlier tract states or attach later outcomes.
- Perturbation tests, feature-family balance checks, and structured human case review have not
  been run.
- The match table does not yet explain the strongest shared features or important differences.
- No clustering or trajectory model has been implemented.
- The output is a small review scaffold, not an application serving table.

A future historical-analogue workflow will need point-in-time queries, candidates observable only
before the query date, training-period transforms reused without refitting, later-outcome tests,
and comparisons with random, regional, and forecast baselines. Those items are intentionally not
described here as current results.

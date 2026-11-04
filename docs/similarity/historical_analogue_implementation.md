# Historical Analogue Implementation

## What is implemented

Job `502 Modeling | Historical Analogue Baseline` turns the historical modeling panel into a
small, reproducible analogue experiment. For a tract observed in a validation year, it finds
earlier tract-year states that looked similar and whose later FHFA outcome was already known at
the query date. It then asks a practical question: would the outcomes of those earlier
communities have provided useful context for what happened to the query tract?

This is a development workflow, not the application lookup service. It deliberately samples a
manageable set of queries, evaluates two representations, and compares the analogue estimates
with forecasting baselines on exactly the same query rows.

## Code and workflow map

| Component | Responsibility |
|---|---|
| `src/neighborhood_twin/historical_analogues.py` | Feature preparation, training-only preprocessing, query selection, time-safe retrieval, analogue estimates, forecast comparators, and evaluation summaries |
| `notebooks/05_modeling/04_run_historical_analogue_baseline.py` | Databricks inputs, MLflow tracking, Delta publication, and post-publication contract checks |
| `historical_analogue_baseline` in `databricks.yml` | Job `502`, parameters, shared experiment path, and model/evaluation schema destinations |
| `src/neighborhood_twin/metadata.py` | Unity Catalog table descriptions, grains, layers, and column comments |

The Python module owns the analytical logic so it can be tested outside the notebook. The
notebook stays focused on orchestration and publication.

## Processing sequence

The workflow runs separately for the one- and three-year horizons:

1. Read `gold_modeling_panel` and require the declared source columns.
2. Derive twelve historical analogue features from values available at each forecast origin.
3. Fit median imputation, standardization, feature-family weights, and PCA using point-model
   training rows only.
4. Select validation queries deterministically within origin year, Census region, and geographic
   development or holdout role. A query is included only if every forecast comparator is also
   available.
5. Search development-state candidate rows with observed outcomes. Exclude the same tract and any
   candidate whose target would not have been known by the query year.
6. Rank exact neighbors in weighted standardized space and six-component PCA space, keeping ten
   per query and representation.
7. Summarize later match outcomes with a median and an inverse-distance weighted mean.
8. Evaluate those four analogue estimates alongside zero change, state trend, and regularized
   linear predictions on the same queries.
9. Publish model outputs and evaluation tables, then reread them and enforce the leakage, row
   count, method coverage, and validation-role checks.

No locked temporal test row is selected anywhere in this sequence.

## Why the query sample is small

Exact historical retrieval compares every selected query with a large candidate population. The
first run chooses one tract for each available combination of horizon, validation origin, Census
region, and geographic role. The choice is deterministic, so rerunning the same contract selects
the same tracts. This gives broad review coverage without pretending that the first experiment is
an application-scale all-tract search.

This sample is appropriate for comparing representation behavior and detecting major weaknesses.
It is not enough by itself for a final product claim. A later frozen version should expand the
query population or justify a stratified evaluation sample after the retrieval contract is
reviewed.

## Representation and distance

The twelve features belong to five families: community scale, occupancy and tenure, housing
structure, affordability, and recent market trajectory. Each family contributes the same total
weight to squared Euclidean distance. A family with three columns therefore does not overpower a
family with two simply because it has more fields.

The weighted standardized representation preserves the declared features directly. PCA provides
a compressed comparison using six components learned from the same training rows. Both use exact
Euclidean retrieval. Distances are meaningful only within a representation and version; a PCA
distance should not be compared numerically with a weighted-standardized distance.

## Time-safety and geography rules

The key rule is:

```text
candidate_target_end_year <= query_origin_year
```

For a three-year query in 2021, the latest eligible candidate origin is 2018. Its 2021 outcome
would have been observable when the query was made. A 2019 candidate would require a 2022 outcome
and is rejected. The candidate must also use the same horizon, come from the geographic
development states, and have a different tract identifier.

These rules are stricter than merely requiring the candidate origin to precede the query. They
prevent future outcomes from entering the analogue estimate and preserve the held-out states as a
geographic transfer check.

## Published tables

| Schema | Table | Use |
|---|---|---|
| `neighborhood_twin_model` | `historical_analogue_match` | Ranked query-to-candidate evidence, distances, later candidate outcomes, geography, and run lineage |
| `neighborhood_twin_model` | `historical_analogue_prediction` | Four analogue estimates and three forecast comparators on identical query rows |
| `neighborhood_twin_evaluation` | `historical_analogue_summary` | Retrieval distance, geography, age, PCA, and representation-overlap diagnostics |
| `neighborhood_twin_evaluation` | `historical_analogue_scorecard` | Error, bias, baseline skill, direction, coverage, and evaluation slices |

The match table is evidence-level output; the prediction table is query-level output. The two
evaluation tables should be used together because a low prediction error does not prove that
individual matches are understandable or stable.

## Runtime and validation lessons

The first implementation attempts exposed two engineering issues that are now part of the tested
workflow:

- Query and candidate frames originally carried the same horizon column name after a cross join,
  making the filter ambiguous. The candidate horizon now has a temporary explicit name and is
  dropped only after equality is enforced.
- Spark's lazy evaluation initially recomputed the exact query-to-candidate ranking for every
  metric and table write. Match frames are now cached and materialized once per horizon. Under
  Spark Connect, uncaching the parent representation before downstream scorecards were
  materialized invalidated their plans, so cache cleanup now happens only after all tables are
  written and validated.

These corrections change execution reliability and runtime, not the modeling contract.

## Reproduction

After jobs `300 Gold | Model Readiness` and `500 Modeling | Forecast Baselines` have succeeded:

```powershell
databricks bundle validate --profile neighborhood-twin -t team
databricks bundle deploy --profile neighborhood-twin -t team
databricks bundle run historical_analogue_baseline --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

Rerunning job `502` overwrites the four current development tables and creates a new MLflow run
under `/Shared/neighborhood-digital-twin/historical-analogues`. It does not rerun ingestion,
silver, gold, or the forecast baselines.

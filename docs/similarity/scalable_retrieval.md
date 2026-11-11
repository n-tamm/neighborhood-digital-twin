# Scalable Historical Analogue Retrieval Benchmark

## Decision this benchmark supports

Job 503 established a trustworthy exact implementation, but its first three-query run took about
14 minutes. Job `603 Evaluation | Scalable Analogue Retrieval` tests whether a smaller candidate
shortlist can preserve the exact top-ten result closely enough to support later precomputation or
interactive serving.

This stage does not replace the selected neighborhood representation. Every method uses the same
training-fitted preprocessing, equal feature-family weights, time-safety rules, distinct-tract
policy, and exact weighted Euclidean distance. The only approximation is which historical
candidates are sent to final exact reranking.

## Benchmark queries

The query sample uses the latest model-ready year. It selects up to three tracts for each Census
region and stable-versus-post-2020 modeling cohort combination. Deterministic supplements ensure
that every eligible housing-composition, community-size, and ACS-uncertainty category appears at
least once.

This is a development benchmark rather than a population-weighted national sample. The coverage
table shows how its composition differs from all eligible current queries, and very small groups
must not be used for broad subgroup claims.

## Exact reference

For every selected tract and horizon, the benchmark reruns exhaustive job-503 retrieval and keeps
ten distinct physical candidate tracts. This reference excludes the query tract, candidates from
geographic holdout states, candidate outcomes ending after the query year, and all locked temporal
test rows.

Approximate fidelity is measured against these exact candidate identities and ranks. An
approximate result is not judged only by whether its returned distances look small.

## LSH candidate generation

The first benchmark tests deterministic bucketed random-projection locality-sensitive hashing
(LSH). Each hash table projects the weighted feature vector onto a seeded random direction and
assigns projected values to fixed-width buckets. Query and candidate states sharing a bucket in
at least one table enter the shortlist. Duplicate collisions are removed, exact weighted distance
is calculated, the closest state of each physical tract is retained, and the final ten are ranked.

Three configurations intentionally trade shortlist size for expected recall:

| Configuration | Bucket length | Hash tables | Intended role |
|---|---:|---:|---|
| `lsh_narrow` | 0.75 | 6 | Small shortlist and lower compute |
| `lsh_balanced` | 1.50 | 10 | Middle fidelity and workload candidate |
| `lsh_high_recall` | 3.00 | 14 | Broader shortlist intended to favor exact-match recovery |

The parameter names describe the intended tradeoff, not a result. Live evidence determines
whether any configuration actually behaves that way.

## Evaluation measures

| Measure | Question answered |
|---|---|
| Complete top-ten share | Does the method return ten distinct communities for every query? |
| Exact top-ten recall | How many exact-reference communities are recovered? |
| Exact tract-year state recall | Are the same historical years retained for those communities? |
| Top-ten Jaccard similarity | How similar are the complete approximate and exact candidate sets? |
| Exact top-three retention | Are the strongest exact matches preserved? |
| Shared-rank displacement | How far do recovered communities move in the list? |
| Outcome-summary drift | Does approximation materially change the historical median or inverse-distance outcome? |
| Shortlist pair count | How much candidate work remains after hashing? |
| Measured runtime | Does candidate generation and reranking reduce end-to-end benchmark time? |

Zero-result query/configuration pairs remain in the query-level evaluation with zero recall. They
are not dropped from averages. Historical outcome drift remains unavailable when no approximate
matches exist rather than being invented as zero.

## Outputs

| Schema | Table | Use |
|---|---|---|
| `neighborhood_twin_model` | `scalable_analogue_match` | Exact and approximate ranked-match evidence |
| `neighborhood_twin_evaluation` | `scalable_analogue_query_evaluation` | Query-level completeness, overlap, ranks, and outcome drift |
| `neighborhood_twin_evaluation` | `scalable_analogue_summary` | Horizon and configuration fidelity, runtime, and shortlist comparison |
| `neighborhood_twin_evaluation` | `scalable_analogue_coverage` | Selected-versus-eligible current-query composition |

## Selection boundary

The benchmark will not declare a configuration production-ready merely because it is faster.
Selection should require complete results, strong and reasonably consistent exact-match recall,
small historical-outcome drift, a meaningful runtime or storage advantage, and no timing or
coverage failure. The chosen method must then be tested at the intended precomputation scale in a
later production-retrieval branch.

## Reproduction

After the current model-ready panel and exact retrieval contract are current:

```powershell
databricks bundle validate --profile neighborhood-twin -t team
databricks bundle deploy --profile neighborhood-twin -t team
databricks bundle run scalable_analogue_retrieval --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

The job writes a new MLflow run under
`/Shared/neighborhood-digital-twin/scalable-analogue-retrieval`. It does not overwrite jobs 503,
601, or 602.

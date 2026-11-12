# Exact Indexed Analogue Retrieval

## Why this stage exists

Job 603 showed that broad random-projection LSH buckets preserved match quality only by retaining
88.7% to 99.9% of the full query-candidate cross-product. This stage tests a different idea: use
an exact tree index to prune candidate states without changing the frozen weighted Euclidean
distance or accepting approximate matches.

The implemented index is scikit-learn's `KDTree`. The representation has twelve numeric
dimensions, which is within the range where a tree can plausibly reduce work, but the decision is
based on the live benchmark rather than that rule of thumb. Scikit-learn notes that KD-tree
performance depends on dimensionality and data structure, and exposes the number of distance
calls for direct measurement. [Scikit-learn nearest-neighbor guide](https://scikit-learn.org/stable/modules/neighbors.html)

The job uses the standard Databricks serverless environment. This preserves the Spark
Connect-compatible preprocessing already used by the project's modeling workflows while using
the included NumPy and scikit-learn libraries. An early test with environment version 2 was
rejected because its older PySpark client could not construct the existing Spark ML imputer on
serverless compute.

## Preserved analytical contract

The tree changes only how candidates are found. It preserves:

- training-fitted imputation and standardization;
- equal total weight for each feature family;
- Euclidean distance in the weighted standardized space;
- one- and three-year candidate pools;
- geographic-development candidates only;
- outcomes known by the 2025 query year;
- exclusion of locked temporal-test candidates and the query tract; and
- ten distinct physical candidate tracts.

This is an exact index. The final ranked list must reproduce job 603's exhaustive candidate tract,
historical origin year, rank, distance, and outcome summaries. Approximate recall is not an
acceptable tradeoff in this branch.

## Distinct-community retrieval

The candidate index contains tract-year states, so one physical tract can appear more than once.
The workflow initially requests 64 nearest states, keeps each tract's closest state, and ranks the
remaining distinct tracts by distance, newer candidate year, and GEOID.

If fewer than ten distinct tracts appear, or if the tenth distinct tract is tied with the farthest
retrieved state, the request doubles. Retrieval stops only when the next unseen state must be
farther than the selected top ten. This makes the distinct-community result exact while retaining
measured expansion counts for operational review.

## Evaluation populations

The job measures three populations per horizon:

1. **Job-603 benchmark:** the same 29 stratified current queries used by the exhaustive reference.
   This population supports exact identity, rank, and outcome reconciliation.
2. **Deterministic intermediate sample:** 1,000 current tracts selected without outcomes. This
   checks whether pruning and throughput remain stable beyond the development sample.
3. **All current eligible queries:** every tract with the selected 2025 representation. This is a
   direct batch timing and work measurement, but the job does not yet publish all national matches.

The locked temporal test is never opened. Candidate outcomes are historical observations already
known by the current query year.

## Measures and selection rule

| Measure | Interpretation |
|---|---|
| Community and tract-year recall | Must both equal 100% against job 603 |
| Rank displacement and outcome drift | Must both remain zero |
| Distance-computation ratio | Tree distance calls divided by one exhaustive pair pass |
| Query elapsed time and throughput | Measured indexed retrieval plus distinct-tract processing |
| Expansion behavior | How often 64 states are insufficient and how large requests become |
| Tree build time and array bytes | Batch refresh cost and in-memory index footprint |

The KD-tree will be selected only if it is exact and provides a meaningful current-scale work or
runtime advantage with manageable index size. If it fails, the project will retain job 503 as the
audit reference and test a different serving design rather than weakening fidelity checks.

## Outputs

| Schema | Table | Role |
|---|---|---|
| `neighborhood_twin_model` | `analogue_tree_benchmark_match` | Reviewable indexed matches for the 29 reference queries |
| `neighborhood_twin_evaluation` | `analogue_tree_query_evaluation` | Query-level exact-reference reconciliation |
| `neighborhood_twin_evaluation` | `analogue_tree_summary` | Horizon-level fidelity, work, runtime, and storage decision evidence |
| `neighborhood_twin_evaluation` | `analogue_tree_scale_benchmark` | Direct 29-query, intermediate, and full-current scale measurements |

## Reproduction

```powershell
databricks bundle validate --profile neighborhood-twin -t team
databricks bundle deploy --profile neighborhood-twin -t team
databricks bundle run analogue_tree_retrieval --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

Job 604 requires current jobs 302 and 603. It fails if job 603's reference uses a different
model-readiness build.

# Similarity Module

**Code file:** [`src/neighborhood_twin/similarity.py`](../../src/neighborhood_twin/similarity.py)

**Current schema version:** `1.1.0`

## Responsibility

The module validates the similarity feature contract, applies scale transforms, fits the current
imputation/standardization/PCA pipeline, selects review queries, retrieves exact neighbors, and
summarizes representation behavior. It returns Spark DataFrames and leaves table publication to
the Databricks notebook.

## Constants and contracts

- `SIMILARITY_FEATURE_COLUMNS` is imported from `products.py` so current candidate construction
  and retrieval use one feature registry.
- `LOG_TRANSFORM_FEATURES` lists the five scale variables receiving `log1p`.
- `DEFAULT_PCA_COMPONENTS` is six.
- Output tables are `similarity_baseline_match` and `similarity_baseline_summary`.

## Main functions

| Function | Responsibility |
|---|---|
| `parse_geoid_list` | Validates optional comma-separated eleven-digit tract GEOIDs |
| `validate_similarity_features` | Fails when an input feature is missing |
| `transformed_feature_name` | Gives every transformed column a stable, explicit name |
| `_prepare_features` | Applies `log1p` or identity transformations without replacing source fields |
| `_select_queries` | Uses explicit GEOIDs or deterministic hash-ranked state samples |
| `_rank_matches` | Cross-joins the small query set to candidates, calculates Euclidean distance, excludes self, and ranks top-k |
| `_representation_summary` | Calculates distance, geography, PCA-variance, and neighbor-overlap diagnostics |
| `build_similarity_baseline_run` | Fits the pipeline and returns versioned match and summary DataFrames |

External code should call `build_similarity_baseline_run()` rather than private preparation or
ranking functions independently.

## Spark ML pipeline

```text
Documented log/identity transforms
    -> Median Imputer
    -> Vector Assembler
    -> Standard Scaler
    -> PCA with 6 components
```

The pipeline produces both `standardized_vector` and `pca_vector`, allowing identical queries to
be ranked in both spaces.

## Ranking implementation

Because the baseline uses only six queries, `_rank_matches()` performs an exact query-candidate
cross join. It converts Spark vectors to arrays, sums squared element differences, takes the square
root, and assigns rank within query and representation. Rank is ordered by distance and then
matched GEOID for deterministic ties.

## Summary implementation

Each representation receives query and match counts, mean and percentile distances, interquartile
range, cross-state share, and same-county share. Raw/PCA overlap is calculated by joining the two
top-k lists on query and matched GEOID, then averaging the overlap count across queries. PCA
explained variance is read from the fitted PCA stage.

## Safety checks

- Duplicate or malformed query GEOIDs are rejected.
- Explicit queries must exist in the candidate table.
- Fallback states must each supply the requested number of queries.
- `top_k` and query counts must be positive.
- PCA components must be between one and the feature count.
- The query tract is excluded from its own result.

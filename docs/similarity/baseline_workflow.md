# Similarity Baseline Workflow

**Databricks job:** `501 Modeling | Similarity Baselines`

**Notebook:** [`02_run_similarity_baselines.py`](../../notebooks/05_modeling/02_run_similarity_baselines.py)

## Default configuration

| Setting | Default |
|---|---|
| Input | `workspace.neighborhood_twin_gold.gold_similarity_candidate_current` |
| Query GEOIDs | Empty; use deterministic state sample |
| Query states | Arizona (`04`), Michigan (`26`), Pennsylvania (`42`) |
| Queries per state | 2 |
| Neighbors per representation | 10 |
| PCA components | 6 |
| MLflow experiment | `/Shared/neighborhood-digital-twin/similarity-baselines` |

The fallback queries are selected by a stable hash of tract GEOID within each state. They are not
hand-picked for a favorable story. An explicit query list can replace the fallback sample.

## Execution sequence

1. Locate and import the deployed package.
2. Parse widgets and read the current similarity candidate table.
3. Create the parent Workspace folder for the shared MLflow experiment if required.
4. Log feature, transform, query, top-k, and PCA settings.
5. Fit the representation pipeline and calculate exact raw and PCA neighbors.
6. Log PCA explained variance and raw/PCA overlap metrics.
7. Overwrite the match and representation-summary Delta tables.
8. Verify that published row count equals queries times top-k times two representations.
9. Fail if any query appears as its own match.

## Outputs

| Output | Schema | Role |
|---|---|---|
| [`similarity_baseline_match`](../data/49_model_similarity_baseline_match.md) | `neighborhood_twin_model` | Ranked tract matches by query and representation |
| [`similarity_baseline_summary`](../data/50_evaluation_similarity_baseline_summary.md) | `neighborhood_twin_evaluation` | Distance, geography, variance, and overlap diagnostics |
| MLflow run | Shared experiment | Reproducible configuration, metrics, and run ID |

The initial run contains 120 match rows: six queries, ten neighbors, and two representations.

## Reproduction

After the current gold candidate table exists and the bundle is deployed:

```powershell
databricks bundle run similarity_baselines --profile neighborhood-twin -t team
databricks bundle run model_evaluation_figures --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

The evaluation job should follow so its manifest points to the new similarity MLflow run. The
metadata job should follow because the baseline overwrites current Delta schemas.

## Operational boundaries

- The job does not require the forecast baseline once its own gold input exists.
- It fits a current-state representation rather than a historical, time-safe representation.
- It does not publish a low-latency application index or serving table.

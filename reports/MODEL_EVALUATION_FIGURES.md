# Model Evaluation Figures

The first model-evaluation workflow is live in Databricks. It combines the current forecast
scorecard and similarity diagnostics into seven versioned PNGs. These are development results,
not final test results: the locked temporal tests remain unopened, and prediction intervals have
not yet been calibrated.

## Shared location

- **Volume:** `workspace.neighborhood_twin_evaluation.model_evaluation_figures`
- **Current build:** `20261030T203807838205Z`
- **Current build directory:**
  `/Volumes/workspace/neighborhood_twin_evaluation/model_evaluation_figures/build_id=20261030T203807838205Z/`
- **Manifest table:**
  `workspace.neighborhood_twin_evaluation.model_evaluation_figure_manifest`
- **Forecast MLflow run:** `6112e891d7244f7eb0a966d79c9466d1`
- **Similarity MLflow run:** `1a4f60f9ddeb42abb2cb36d7974ec312`

The manifest is the authoritative current inventory. It links each file to its evaluation build
and both source MLflow runs. The seven files were checked after rendering; all opened correctly,
labels and legends were readable, and the smallest file was 97,768 bytes.

## Figure set

1. `01_forecast_mae_by_horizon.png` compares all point-forecast methods on the same validation
   rows for each horizon.
2. `02_forecast_skill_vs_zero.png` shows how much each method improves on a zero-change forecast,
   using both MAE and RMSE skill.
3. `03_forecast_bias_and_tail_error.png` separates average signed bias from 90th-percentile
   absolute error so a reasonable mean error cannot hide systematic or extreme misses.
4. `04_forecast_geographic_transfer.png` compares development states with the governed held-out
   states. This is a development transfer check, not the final temporal test.
5. `05_forecast_housing_composition.png` compares errors across single-family housing shares,
   which is important because FHFA HPI is a single-family market measure.
6. `06_similarity_representation_diagnostics.png` compares raw standardized and PCA-based
   retrieval on distance distribution, geographic diversity, and top-10 neighbor overlap.
7. `07_forecast_temporal_stability.png` shows one-year error by independent forecast-origin year
   instead of treating millions of tract rows as independent evidence.

## What the first evaluation shows

In the November 7, 2026 decade-safe validation run, gradient-boosted trees has the lowest one-year
MAE (0.0707) and improves MAE by 40.4% over zero change. It underpredicts by about 3.77 annualized
percentage points on average, showing why no single metric should select the model.

Directional accuracy needs especially careful interpretation. About 90.2% of one-year validation targets are positive, rising to roughly 94.6% and 97.3% at three
and five years. The apparent
90%-plus directional accuracy therefore provides essentially no lift over always predicting the
majority direction. It should not be presented as evidence of useful directional prediction.

At three years, the gradient-boosted-tree candidate has the lowest MAE and RMSE. The five-year
regularized linear result is stronger than the tree, but it is based on only two training origins
and one validation origin, so it remains exploratory. One-year errors are also higher for tracts where
single-family detached homes make up less than 25% of the housing stock, reinforcing the need to
show housing-composition limitations in the application.

For similarity, the six-component PCA representation retains 95.5% of standardized variance, but
the raw and PCA top-10 lists overlap by only 55% on average. Both methods retrieve mostly
cross-state matches, yet the moderate overlap shows that representation choice materially changes
which communities are called similar. The separate job-502 retrospective test now evaluates later
outcomes; human review and perturbation stability are still required before selecting the
application representation.

## Reproduce the figures

The job is defined in [`databricks.yml`](../databricks.yml) and rendered by
[`03_render_model_evaluation.py`](../notebooks/05_modeling/03_render_model_evaluation.py). Run it
only after jobs 500 and 501 have current successful outputs:

```powershell
databricks bundle validate --profile neighborhood-twin -t team
databricks bundle deploy --profile neighborhood-twin -t team
databricks bundle run model_evaluation_figures --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

In Catalog Explorer, open the `workspace` catalog, then `neighborhood_twin_evaluation`, then the
`model_evaluation_figures` volume. Query the manifest table when a reproducible matched set is
needed. Local report copies belong under ignored `reports/generated/`, not `personal_scratch/`.

## Evaluation work still required

- compare one focused nonlinear forecast candidate and feature-family ablations;
- estimate uncertainty across forecast origins or geographic blocks rather than treating tract
  rows as independent replicates;
- calibrate prediction intervals and report empirical coverage, width, and subgroup coverage;
- expand or justify the first time-safe analogue query sample, then run retrieval perturbation
  tests and human case review;
- freeze the champion and calibration method before opening the locked temporal tests; and
- evaluate application comprehension, usability, latency, and unavailable-result behavior after
  serving tables and the interactive application exist.

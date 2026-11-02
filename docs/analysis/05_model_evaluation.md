# Model Evaluation

The current evaluation layer turns forecast scorecards and similarity diagnostics into a small,
versioned set of review figures. It is designed to answer development questions: which baseline
is strongest, where does it fail, does it transfer, and how sensitive are the similarity matches
to representation choice?

It does not report final model performance. The locked temporal tests remain unopened, forecast
intervals have not been calibrated, and the current similarity run has not been evaluated as a
historical analogue system.

## Evaluation sequence

A useful review follows this order:

1. Confirm the analytical population and split limits in the
   [data and cohort guide](01_analytical_data_and_cohorts.md).
2. Compare overall forecast error on identical validation rows.
3. Check whether a model improves on simple baselines rather than only reporting its raw error.
4. Inspect bias, large misses, origin-to-origin stability, geographic transfer, and housing-stock
   composition.
5. Review similarity distance, geographic reach, and raw/PCA agreement as representation
   diagnostics—not as proof of useful matches.
6. Freeze a point-model choice only after the evidence is consistent enough across these views.
7. Reserve calibration and locked-test evaluation for the later approved release workflow.

The implemented job does not retrain a model or recalculate matches. It reads the current
run-linked evaluation tables, renders the figures, validates the output set, and publishes a
manifest. This keeps model computation separate from presentation.

## Forecast evaluation figures

### 1. MAE by model and horizon

`01_forecast_mae_by_horizon.png` compares all six methods on the same validation rows within each
horizon. Lower MAE means a smaller average absolute miss in cumulative HPI log change.

This is the primary ranking view, but it is not sufficient by itself. A low overall MAE can hide
systematic underprediction, large tail errors, instability across time, or poor results in a
specific housing population. Values should be compared within a horizon; a one-year and
five-year cumulative target do not have the same interpretation.

### 2. Skill relative to zero change

`02_forecast_skill_vs_zero.png` reports MAE and RMSE skill:

```text
skill = 1 - candidate error / zero-change error
```

A value above zero improves on zero change, zero ties it, and a negative value is worse. This
figure answers whether added machinery earns its complexity relative to a transparent baseline.
It does not show whether the remaining error is small enough for a user-facing forecast.

### 3. Bias and tail error

`03_forecast_bias_and_tail_error.png` focuses on the state-trend and regularized-linear methods.
Mean signed error is actual minus predicted change: a positive value indicates underprediction
and a negative value indicates overprediction. The 90th-percentile absolute error shows the level
below which 90% of absolute misses fall.

Reading the two together prevents a reasonable average from hiding bad extremes, or a modest
absolute error from hiding a consistent direction of bias. The current one-year linear model
underpredicts by about 2.74 annualized percentage points on average.

### 4. Geographic transfer

`04_forecast_geographic_transfer.png` compares development states with Maine, North Dakota, West
Virginia, and New Mexico, which are the governed geographic holdout states.

This is a transfer diagnostic during development. It asks whether performance changes when the
model is evaluated in complete states that were excluded from fitting. It is not the final
temporal test, and four relatively small states cannot represent every kind of national transfer.
Observation and tract counts should be considered alongside error before interpreting a gap.

### 5. One-year accuracy by housing composition

`05_forecast_housing_composition.png` compares one-year error across ACS single-family housing
share bands. This slice is necessary because FHFA HPI represents a filtered single-family market
and both target coverage and model error are weaker in heavily multifamily tracts.

A larger error in a low-single-family band may reflect different market behavior, weaker target
representation, less FHFA history, or a combination. The figure identifies a limitation to
communicate; it does not identify the cause.

### 7. Temporal stability

`07_forecast_temporal_stability.png` reports one-year MAE separately for each validation
forecast-origin year. Each point represents one independent origin rather than treating the many
tract rows from that year as independent time evidence.

This view checks whether an overall advantage appears in both validation periods or is driven by
one market year. With only two one-year validation origins, it is a necessary diagnostic but not
a precise estimate of performance variability.

## Similarity evaluation figure

### 6. Representation diagnostics

`06_similarity_representation_diagnostics.png` compares standardized raw and PCA retrieval using
distance distributions, cross-state reach, and mean top-10 overlap.

- Distance quantiles and the interquartile range show whether the nearest matches are tightly
  packed or more separated within a representation.
- Cross-state and same-county shares show whether the output collapses to local geography or
  retrieves nationally.
- Top-10 overlap shows how much the selected neighbors change when the same features are compressed
  from twelve standardized dimensions to six PCA components.

These are unsupervised diagnostics because no authoritative list of correct matches exists. The
current 55% mean overlap says representation choice materially affects the answer. It does not say
that either representation is useful for anticipating a later outcome. Distances must not be
compared numerically across raw and PCA spaces.

## Current evidence in one view

| Finding | What it supports | What it does not support |
|---|---|---|
| Linear one-year MAE is 0.0724 versus 0.0757 for state trend | The linear model is the strongest current one-year MAE baseline | Declaring it final when bias and R-squared remain weak |
| State trend three-year MAE is 0.0666 versus 0.0679 for linear | Simple regional context remains competitive | Assuming more model complexity will improve every horizon |
| Five-year linear MAE is 0.0952 with three training origins | Keeping a simple exploratory five-year comparison | A strong or stable five-year product claim |
| One-year linear R-squared is negative | Cross-tract variation remains poorly captured on squared error | Concluding that every prediction is useless; MAE skill answers a different question |
| Directional accuracy adds almost no lift over the majority direction | De-emphasizing direction accuracy in model selection | Claiming useful rise/fall classification from a 90% raw accuracy |
| PCA retains 95.5% of variance but overlaps raw matches by 55% | Reviewing concrete matches before choosing a representation | Choosing PCA from explained variance alone |

## Why the measures are kept together

Model evaluation can appear contradictory because each measure asks a different question. MAE
describes the average magnitude of a miss, RMSE reacts more strongly to large misses, signed error
shows systematic under- or overprediction, and R-squared asks whether squared error improves on a
mean prediction. Skill compares with a chosen operational baseline. A model can improve MAE over
zero change while having negative R-squared and meaningful bias; that is exactly why the project
does not select a model from one number.

The same principle applies to similarity. Explained variance, distances, geographic diversity,
and neighbor overlap describe representation behavior. None creates a labeled ground truth. The
later historical-analogue stage will need to test whether earlier matches provide useful context
about later outcomes and whether reasonable preprocessing changes leave the results mostly
stable.

## Reproducibility and lineage

- Workflow: `600 Evaluation | Model Diagnostics`
- Rendering notebook:
  [`03_render_model_evaluation.py`](../../notebooks/05_modeling/03_render_model_evaluation.py)
- Figure manifest:
  [`workspace.neighborhood_twin_evaluation.model_evaluation_figure_manifest`](../data/51_evaluation_model_evaluation_figure_manifest.md)
- Managed volume: `workspace.neighborhood_twin_evaluation.model_evaluation_figures`
- Build inventory and export instructions:
  [Model Evaluation Figures](../../reports/MODEL_EVALUATION_FIGURES.md)

The manifest records each figure's build ID and the exact forecast and similarity MLflow run IDs
used to create it. A matched figure set can therefore be reproduced without guessing which model
run was current at rendering time.

## Current evaluation boundary

The current evidence is sufficient to diagnose the baselines and decide what to test next. It is
not sufficient to release a forecast or similarity feature in the application. The following are
not implemented evaluation results:

- uncertainty interval coverage, width, and subgroup calibration;
- nonlinear-model or feature-family ablation results;
- retrospective analogue outcome accuracy and comparison with random or regional matches;
- systematic perturbation stability and structured human review of matches;
- locked temporal test scores; or
- evaluation of application content, availability states, and usefulness.

Those results should be added to this guide only after the corresponding workflow is implemented
and its outputs are versioned.

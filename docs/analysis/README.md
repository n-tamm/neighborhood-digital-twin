# Implemented Analysis Guide

This section explains the analysis that is running now. It is meant for a reader who can inspect
the repository but cannot open the team's Databricks workspace. The documents connect the
governed tables, EDA figures, model code, and evaluation results without presenting planned work
as though it already exists.

## Recommended reading order

1. [Analytical data and cohorts](01_analytical_data_and_cohorts.md) explains the data population,
   tract-vintage rule, point-in-time feature logic, forecast target, and model splits shared by the
   current analyses.
2. [Exploratory data analysis](02_exploratory_data_analysis.md) explains the twelve implemented
   EDA figures, the order in which they should be read, and the claims each can and cannot support.
3. [Forecasting baselines](03_forecasting_baselines.md) explains the prediction target, six
   implemented methods, training pipeline, validation design, and current results.
4. [Similarity baselines](04_similarity_baselines.md) explains how the current neighborhood
   matches are built, what their diagnostics mean, and why they are not yet historical analogues
   or recommendations.
5. [Model evaluation](05_model_evaluation.md) explains the seven implemented evaluation figures
   and how the current evidence should guide the next model iteration.

The analysis currently follows this sequence:

```text
Validated silver tables
        |
        v
Current and historical gold products
        |
        +------------------+
        |                  |
        v                  v
EDA summaries        Model-ready panel
and 12 figures       and current similarity candidates
                           |
                           +--------------------+
                           |                    |
                           v                    v
                    Forecast baselines   Similarity baselines
                           |                    |
                           +----------+---------+
                                      v
                         Evaluation tables and 7 figures
```

## What is implemented

| Area | Current implementation | Evidence available in the repository |
|---|---|---|
| Data preparation | National ACS, FHFA tract HPI, tract relationships, display geometry, geography hierarchy, current profiles, historical features, targets, and fixed model splits | Per-table contracts in [`docs/data`](../data/README.md), small samples in [`data/samples`](../../data/samples/README.md), and the [run-order guide](../PIPELINE_RUN_ORDER.md) |
| EDA | Governed summary tables and twelve versioned figures covering coverage, uncertainty, time, geography, feature readiness, and split design | [EDA guide](02_exploratory_data_analysis.md), rendering code, and the [figure inventory](../../reports/EDA_FIGURES.md) |
| Forecasting | Five fixed baselines and one L2-regularized linear model, fit separately for one-, three-, and five-year horizons | [Forecast guide](03_forecasting_baselines.md), source code, prediction contract, scorecard contract, and evaluation figures |
| Similarity | Exact nearest neighbors for six review queries in standardized raw and six-component PCA spaces | [Similarity guide](04_similarity_baselines.md), source code, match contract, summary contract, and evaluation figures |
| Evaluation | Validation-only forecast scorecards, similarity diagnostics, MLflow tracking, and seven versioned figures | [Evaluation guide](05_model_evaluation.md) and the [evaluation figure inventory](../../reports/MODEL_EVALUATION_FIGURES.md) |

## Evidence labels used here

- **Descriptive** means the result summarizes observed data. It does not show that one factor
  caused another.
- **Development result** means the result uses validation data to compare or diagnose methods.
  It can guide model development but is not a final performance claim.
- **Locked test result** would mean a result produced only after the model and uncertainty method
  are frozen. No locked temporal test result has been produced yet.

The current forecast and similarity results are development results. Prediction intervals,
historical analogue evaluation, app-serving model tables, and the interactive application are not
part of the implemented analysis described here.

## Where the live outputs are stored

The versioned PNGs, Delta tables, and MLflow runs live in the shared Databricks workspace. Git
contains the transformation and rendering code, table contracts, small representative samples,
and these interpretation guides. The manifest tables identify the current matched figure sets:

- `workspace.neighborhood_twin_gold.gold_eda_figure_manifest`
- `workspace.neighborhood_twin_evaluation.model_evaluation_figure_manifest`

This separation avoids committing changing binary outputs while keeping the work reproducible and
reviewable without direct workspace access.

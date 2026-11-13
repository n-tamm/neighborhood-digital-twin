# Similarity Communication Figures

## Current reviewed build

- **Build ID:** `20261113T193948450115Z`
- **Databricks job:** `800 Presentation | Similarity Communication Figures`
- **Job run:** `626327765918889` (successful in 58 seconds)
- **Managed volume:**
  `/Volumes/workspace/neighborhood_twin_evaluation/similarity_evaluation_figures/build_id=20261113T193948450115Z/`
- **Manifest:**
  `workspace.neighborhood_twin_evaluation.similarity_evaluation_figure_manifest`
- **Case study:** Oakland County, Michigan, tract `26125144200`, three-year horizon

The five PNGs are a matched evidence set. Use the manifest rather than choosing files by
modification time because it records the exact audit, selection, retrieval, and serving lineage
used by the build.

## Figure inventory and interpretation

1. **`01_similarity_workflow.png`** explains the sequence from the current tract state through
   training-only preprocessing, time-safe candidates, exact retrieval, observed later outcomes,
   and application evidence. It is the clearest opening figure for explaining the method.
2. **`02_similarity_stability_and_selection.png`** shows that small family-weight changes retain
   most of the original top ten, while removing a whole feature family or changing PCA dimensions
   is a materially different model. Weighted matching also has lower validation error than PCA at
   both supported horizons, which supports its use as the application default.
3. **`03_analogue_outcome_utility.png`** shows that historical analogues improve on a zero-change
   comparison but do not beat the state-trend or regularized-linear forecast. This is why the app
   presents analogues as supporting evidence rather than its primary forecast.
4. **`04_current_analogue_coverage.png`** shows that 46,719 of 85,528 canonical current tracts
   (54.6%) support the complete selected method at each horizon. Unsupported results keep an
   explicit reason and must not be silently replaced with another representation.
5. **`05_oakland_county_case_study.png`** connects one current tract to ten matches in ten states,
   identifies the top match's feature-family gaps, and plots the ten observed later FHFA paths.
   The paths are historical observations, not forecasts or causal counterfactuals.

## Why this case was selected

The Michigan example met a predeclared communication rule: ten complete distinct-community
matches, ten represented states, complete three-year paths, and no query-side imputation. It was
not selected because its later outcomes looked favorable. One example cannot establish national
performance; figures 2 through 4 provide the broader evaluation and coverage evidence.

## Visual review

All five images were inspected at full resolution after the live job. The first render exposed an
unclear final workflow transition and a coverage annotation that overlapped a stacked bar. Those
layouts were corrected and the complete governed job was rerun. The accepted build has readable
titles, legends, scales, notes, and color contrast. Labels were also checked against the manifest
and source-table results. Job 900 then applied the table description and comments to all 14
manifest columns.

## Standup walkthrough

Open
[`01_similarity_model_walkthrough.py`](../notebooks/08_final_analysis/01_similarity_model_walkthrough.py)
in Databricks. It reads the current manifest and published evidence, displays the figures in
method order, and includes short speaking callouts. It does not retrain the model or implement a
second retrieval path.

The recommended sequence is: research question and boundary, five-table serving contract,
feature representation, time-safety, representation selection, outcome utility, current
coverage, exact batch scale, Michigan example, and interpretation limits.

## Reproduce or refresh

After deploying the reviewed branch and confirming that jobs 601, 602, 604, and 700 represent the
approved evidence:

```powershell
databricks bundle run similarity_communication_figures --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

A style-only change requires job 800 and then job 900. A model, evaluation, or serving change must
refresh the relevant upstream job first. Do not edit or replace PNG files manually.

## Report-use boundary

These figures support claims about method design, validation behavior, current coverage, and one
transparent example. They do not show locked-test performance, prove causal similarity, create a
calibrated uncertainty interval, or establish that every tract has usable historical analogues.

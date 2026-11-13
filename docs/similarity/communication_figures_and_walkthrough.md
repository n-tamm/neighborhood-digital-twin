# Similarity Communication Figures and Walkthrough

## Purpose

The similarity system now has enough separate evaluation and serving products that no single
table or early diagnostic can explain it. Job 800 creates a matched five-figure set for the final
report, standups, and application design. The companion walkthrough notebook presents those
figures in the same order as the method itself.

The workflow reads published evidence only. It does not retrain preprocessing, adjust feature
weights, retrieve new neighbors, select a different representation, or open locked temporal-test
rows.

## Governed inputs

The build combines four stages of evidence:

- job 601 stability results, including small weight changes, family ablations, PCA variations,
  and the distinct-community rule;
- job 602 expanded-validation scorecards used to choose weighted standardized matching over PCA
  and compare analogue outcomes with forecast methods;
- job 604 national exact-tree scale measurements; and
- the latest complete job-700 schema-1.1 serving release, including availability, explanations,
  and annual historical paths.

The manifest records one run or release identifier from each stage. Publication stops if a source
contains multiple current run IDs or if no serving release has all five validated manifest rows.

## Figure set

1. **Similarity workflow:** explains the five feature families, training-only preprocessing,
   time-safe candidate rule, exact distinct-community retrieval, explanations, and application
   interpretation.
2. **Stability and representation selection:** shows the distribution of top-ten retention under
   declared model changes and the weighted-versus-PCA later-outcome comparison.
3. **Outcome utility:** compares both weighted analogue summaries with zero change, state trend,
   and regularized linear forecasting on identical expanded-validation queries.
4. **Current availability:** shows the available population and every governed unavailable-result
   reason at one and three years.
5. **Michigan case study:** locates ten historical matches, shows the top match's five family
   gaps, and aligns the ten observed post-match FHFA paths by elapsed year.

Every figure answers one question and carries an interpretation note. A file is rejected when it
does not match the fixed name and sequence, is smaller than 20,000 bytes, or lacks consistent
audit, selection, tree, and serving lineage.

## Case-study selection

The default example is Oakland County, Michigan, tract `26125144200`, at the three-year horizon.
It was selected using a declared communication rule rather than because it had an unusually good
later outcome: it has ten matches, ten represented candidate states, complete annual paths, and no
query-side imputation. The example is intended to make the system easy to explain. It is not a
claim that every current tract has equally complete or geographically diverse evidence.

The map uses the project's display-only Census tract geometry to locate the query and candidates.
Geometry is not used to calculate similarity, proximity, or model features. Plotly's standard
[`scattergeo` geographic projection](https://plotly.com/python/reference/scattergeo/) supplies the
presentation basemap; no map code was copied from another project.

## Walkthrough sequence

[`01_similarity_model_walkthrough.py`](../../notebooks/08_final_analysis/01_similarity_model_walkthrough.py)
is designed to be opened during a standup. It proceeds through:

1. the five-table release contract;
2. feature families and training-only preprocessing;
3. time-safety and distinct-community rules;
4. stability and representation choice;
5. analogue-versus-forecast utility;
6. national current availability;
7. exact indexed scale;
8. one application-style case; and
9. interpretation limits.

Short speaking callouts are included at the points where the distinction between similarity,
historical outcome evidence, and forecasting is most likely to be lost. The notebook reads the
current figure manifest and governed tables. It does not contain a second implementation of the
model.

## Operational boundary

Run job 800 after jobs 601, 602, 604, and 700 contain the approved evidence. A style-only revision
requires job 800 but not model or serving refreshes. If any upstream representation, evaluation,
or serving release changes, refresh the relevant upstream jobs first so the new figure manifest
records one coherent set of lineage IDs. Run job 900 afterward to apply metadata to the manifest.

Live build identifiers, visual-review findings, and figure-level results will be added after the
first successful Databricks publication.

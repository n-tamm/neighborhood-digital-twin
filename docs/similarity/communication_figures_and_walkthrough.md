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
2. the twelve features, training-only imputation and scaling, family balancing, and weighted
   Euclidean distance;
3. the time-safe candidate pool, exact nearest-neighbor retrieval, and distinct-community rule;
4. the combined evaluation framework and stability and representation evidence;
5. MAE, RMSE, and bias evidence for analogue-versus-forecast utility;
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

## Validated live result

Job 800 run `887982270644008` completed successfully in 61 seconds and published build
`20261121T204510966976Z`. The manifest contains the expected five rows and one coherent set of
source identifiers:

- audit run `d4957281b60a407a9dc0b1a84d7c9e57`;
- selection run `9da77fab59bd41d8b8b602493131a890`;
- exact-tree run `344fbe71819f4a779b36701a5fdaf7b8`; and
- serving release `analogue-20261121T163609734965Z`.

The files range from 154,297 to 354,645 bytes, so each passed the publication-size guard. The final
review also corrected the utility title and distinguished current tracts per horizon from total
tract-horizon availability rows. All five PNGs were inspected after rendering. Job 900 run
`477954237899280` completed successfully and reapplied metadata across the governed tables.

The final set makes four project decisions visible: weighted matching is the default; bounded
weight changes are stable but family ablations are not minor changes; analogue outcomes are useful
context but not the strongest forecast; and the complete method is available for 46,719 of 85,528
current canonical tracts at each supported horizon. The Michigan example then shows what one
available result looks like without turning it into a national performance claim.

See the report-facing [similarity figure guide](../../reports/SIMILARITY_FIGURES.md) for the file
inventory, speaking sequence, and reproduction commands.

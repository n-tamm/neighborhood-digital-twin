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

## Validated live result

Job 800 run `626327765918889` completed successfully in 58 seconds and published build
`20261113T193948450115Z`. The manifest contains the expected five rows and one coherent set of
source identifiers:

- audit run `a7f7d2c018214708a955a4ac9b9ec0c4`;
- selection run `f161ff3938b34032afe3634ef3de38df`;
- exact-tree run `fae78721154347039d41864bad2e871a`; and
- serving release `analogue-20261113T132155097077Z`.

The files range from 148,449 to 364,326 bytes, so each passed the publication-size guard. Full-
resolution review found two layout issues in the first render: the final workflow transitions
were ambiguous, and the coverage explanation overlapped the bar. Both were corrected and the
governed job was rerun. The accepted five-figure set was then inspected for titles, labels,
legends, scales, color contrast, and consistency with the underlying evidence. Job 900 completed
successfully and confirmed comments on all 14 manifest columns.

The final set makes four project decisions visible: weighted matching is the default; bounded
weight changes are stable but family ablations are not minor changes; analogue outcomes are useful
context but not the strongest forecast; and the complete method is available for 46,719 of 85,528
current canonical tracts at each supported horizon. The Michigan example then shows what one
available result looks like without turning it into a national performance claim.

See the report-facing [similarity figure guide](../../reports/SIMILARITY_FIGURES.md) for the file
inventory, speaking sequence, and reproduction commands.

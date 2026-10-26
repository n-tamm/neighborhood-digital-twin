# Next Work: Historical Modeling and Parallel Development

This is the short operational handoff for the next development session. It does not replace the
[project roadmap](ROADMAP.md) or the detailed
[implementation guides](docs/implementation/README.md).

## Current position

The source-to-EDA portion of the Databricks pipeline is complete for the current project scope.
The repository and shared workspace now contain:

- governed source snapshots, manifests, bronze tables, and bronze validation;
- typed and validated FHFA, ACS, relationship, geometry, and Connecticut bridge products in
  silver;
- a complete 85,528-row canonical 2020 tract dimension;
- a complete current tract profile plus 83,359 similarity candidates, 51,263 forecast candidates,
  and 8,182 application-demo tracts in gold;
- complete annual 2010-2024 ACS coverage for the 50 states and Washington, D.C.: 765 required
  state-release pairs, 1,152,605 selected silver tract-release rows, and zero hard failures in the
  latest bronze, silver, and gold validation runs;
- a supported Census hierarchy containing one country, four regions, nine divisions, 51 states or
  state equivalents, 3,143 counties or equivalents, and 84,414 canonical tracts;
- national FHFA tract history through 2025;
- governed readiness summaries and seven reviewed, versioned EDA figures;
- table descriptions, column comments, individual table documents, and small real samples.
- a measured 2010-to-2020 tract-change audit: 59,607 of 73,057 project-scope 2010 tracts meet the
  conservative stable same-GEOID rule, while 13,450 require harmonization or exclusion.
- a published 1,018,099-row historical neighborhood-state panel covering ACS releases from 2010
  through 2024, with alignment and conservative availability lineage on every row;
- a published 6,207,795-row forecast-target table with direct one-, three-, and five-year FHFA
  outcomes, retained censored rows, and zero unresolved hard validation failures;
- a 40-row historical coverage table that makes the smaller pre-2020 cohort and later broad
  coverage visible by release and alignment outcome.

Source acquisition, source-specific cleaning, geography alignment, historical state, and target
construction are complete for the approved ACS, FHFA, and geography scope. The pipeline is not
yet model-ready from end to end. It still needs point-in-time feature rows, fixed evaluation split
assignments, and a model-ready joined panel. Model outputs, uncertainty intervals, historical
analogues, scenarios, and application-serving tables follow those products.

## Scope decisions already supported by the data

- Keep current-state similarity and descriptive application coverage national.
- Treat FHFA forecasting as a narrower product for the covered, predominantly single-family tract
  population. Do not generalize its results to all communities or housing types.
- Keep one-year forecasting as the primary target. Three- and five-year horizons remain secondary
  until their final eligible samples and evaluation windows are confirmed.
- Use the existing simplified geometry only for display. Adjacency, distance, or other analytical
  spatial features require a separate approved geography product.
- Do not add another source merely because it is available. Add one only when a baseline or
  required evaluation exposes a weakness it can address.

## Immediate shared decision gate

The historical geography, state, and target decisions are now implemented. Before model-ready
features and split tables are published, the team must approve the remaining point-in-time
modeling contract covering:

1. the forecast origin and source-availability cutoff;
2. training, validation, calibration, locked temporal-test, and geographic-holdout assignments;
3. the initial feature registry, missingness rules, and training-fitted preprocessing policy;
4. whether the first geographic evaluation uses county, state, or another currently supported
   geographic unit.

One teammate should draft the contract and proposed schemas. The other should review timing,
geography, leakage, target meaning, and feasibility before it is merged. Merge this small contract
first so the parallel branches share the same definitions.

The published state table enforces the 59,607-tract stable cohort for every pre-2020 release. Do
not use Census land overlap as a population or housing weight. Downstream contracts still need to
state whether a given evaluation uses the balanced stable cohort across all years or a later-only
window with broader 2020-geography coverage.

## Parallel workstream A: historical data and forecasting readiness

Suggested branch: `data/historical-modeling-tables`

Responsibilities:

- use the published historical neighborhood-state and horizon-specific target tables as governed
  inputs;
- build leakage-safe feature rows with source vintage, availability, age, and quality fields;
- publish chronological and geographic split assignments rather than creating them inside model
  notebooks;
- add leakage, uniqueness, range, reconciliation, and attrition checks;
- document each new table and add a small real sample;
- fit zero-change, historical-average, persistence, regional, and regularized-linear forecasting
  baselines after the tables pass.

This workstream should own shared Databricks job wiring and table-metadata changes during this
sprint so both people do not edit `databricks.yml` and `metadata.py` at the same time.

## Parallel workstream B: similarity and application foundation

Suggested first branch: `model/similarity-baseline`

This work can begin immediately with `gold_similarity_candidate_current` and
`gold_application_demo_tract`; it does not need to wait for the historical panel.

Responsibilities:

- build a standardized-feature Euclidean nearest-neighbor baseline;
- compare original feature-space retrieval with a PCA representation;
- retain distances, rank, feature versions, and understandable similarities and differences;
- test neighbor stability across scaling, feature families, geography, and housing composition;
- review representative matches for obvious failures that a distance metric misses;
- define the future `gold_analogues` and application-serving contracts;
- if capacity allows, build a thin Streamlit prototype for tract selection, maps, housing mix,
  current state, source dates, coverage warnings, and methods.

The final time-safe analogue evaluation still waits for workstream A because it needs historical
query and candidate years plus later outcomes. The current-state retrieval implementation and app
shell do not.

## Coordination rules that avoid blockers

- Create both branches from the same reviewed contract commit.
- Give one person temporary ownership of shared configuration and metadata files.
- Do not let both people publish the same canonical Databricks table or run competing refreshes.
- Keep experimental outputs separate from existing gold contracts until validation passes.
- Put reusable logic in `src/neighborhood_twin/`, tests in `tests/`, and keep notebooks as thin
  orchestration or investigation layers.
- Commit small, coherent units and exchange contract changes early rather than after a large
  branch has diverged.
- Merge the historical-table branch first because its outputs become shared dependencies. Rebase
  the similarity branch onto that result before adding retrospective analogue evaluation.

## Integration sequence

1. Approve the remaining feature and evaluation-split contract.
2. Build point-in-time features and the current-state similarity baseline in parallel.
3. Validate and merge feature, split-assignment, and model-ready panel tables.
4. Fit forecasting baselines and add retrospective, time-safe analogue evaluation.
5. Decide whether CBSA membership, analytical adjacency, macroeconomic context, or another source
   earns its place through a measured baseline comparison.
6. Select one nonlinear forecasting model and one uncertainty method.
7. Publish predictions, intervals, analogues, explanations, and scenario outputs.
8. Build compact serving tables and complete the interactive application.

## Definition of the next completed checkpoint

The next checkpoint is complete when the team has:

- a reviewed point-in-time feature and split contract built on the implemented state and target
  products;
- reproducible feature, split-assignment, and model-ready panel tables with zero unresolved hard
  validation failures;
- a leakage review and clear row attrition report;
- forecast baselines evaluated on identical chronological and geographic splits;
- an interpretable current-state similarity baseline with stability and case review;
- a written decision about any additional source or analytical spatial product;
- enough stable outputs for the application prototype to consume explicit contracts rather than
  research notebooks.

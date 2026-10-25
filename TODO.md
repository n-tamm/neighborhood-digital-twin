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

Source acquisition and source-specific cleaning are complete for the approved ACS, FHFA, and
geography scope. The pipeline is not yet complete from an end-product perspective. It does not
have the cross-vintage historical modeling panel, targets, evaluation splits, model outputs,
uncertainty intervals, historical analogues, scenarios, or application-serving tables.

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

Before either workstream creates final historical products, the team must approve one
point-in-time modeling contract covering:

1. the forecast origin and source-availability cutoff;
2. the historical ACS geography policy, especially for pre-2020 releases on 2010-vintage tracts;
3. one-, three-, and five-year target definitions, eligibility, and right-censoring rules;
4. training, validation, calibration, locked temporal-test, and geographic-holdout assignments;
5. the initial feature registry, missingness rules, and training-fitted preprocessing policy;
6. whether the first geographic evaluation uses county, CBSA, state, or another explicit unit.

One teammate should draft the contract and proposed schemas. The other should review timing,
geography, leakage, target meaning, and feasibility before it is merged. Merge this small contract
first so the parallel branches share the same definitions.

## Parallel workstream A: historical data and forecasting readiness

Suggested branch: `data/historical-modeling-tables`

Responsibilities:

- build the historical neighborhood-state table at one tract and forecast origin per row;
- build leakage-safe feature rows with source vintage, availability, age, and quality fields;
- build horizon-specific FHFA targets, eligibility flags, and censoring reasons;
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

1. Approve and merge the historical modeling contract.
2. Build historical tables and the current-state similarity baseline in parallel.
3. Validate and merge historical state, feature, target, and split tables.
4. Fit forecasting baselines and add retrospective, time-safe analogue evaluation.
5. Decide whether CBSA membership, analytical adjacency, macroeconomic context, or another source
   earns its place through a measured baseline comparison.
6. Select one nonlinear forecasting model and one uncertainty method.
7. Publish predictions, intervals, analogues, explanations, and scenario outputs.
8. Build compact serving tables and complete the interactive application.

## Definition of the next completed checkpoint

The next checkpoint is complete when the team has:

- a reviewed point-in-time state, feature, target, and split contract;
- reproducible historical gold tables with zero unresolved hard validation failures;
- a leakage review and clear row attrition report;
- forecast baselines evaluated on identical chronological and geographic splits;
- an interpretable current-state similarity baseline with stability and case review;
- a written decision about any additional source or analytical spatial product;
- enough stable outputs for the application prototype to consume explicit contracts rather than
  research notebooks.

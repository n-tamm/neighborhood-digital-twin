# Next Work: Data Readiness and Exploration

This is the short operational handoff for the next development session. It does not replace the
[project roadmap](ROADMAP.md) or the detailed [implementation guides](docs/implementation/README.md).

## Where the project sits

The core Databricks data pipeline is working through bronze, silver, canonical geography, current
gold products, governed EDA summaries, and a reviewed visual-EDA figure build. Tables are separated
into bronze, silver, gold, and quality schemas. Structural validation and current-state exploration
are strong; model-specific historical preparation is now the next major stage.

Current analytical outputs include:

- 85,528 rows in the complete current tract profile;
- 83,359 current similarity candidates;
- 51,263 current forecast candidates, which are only an availability screen and not training rows;
- 8,182 Arizona, Michigan, and Pennsylvania application-demo tracts;
- nationwide 2024 ACS coverage for the 50 states and Washington, D.C.;
- annual 2010-2024 ACS coverage for Arizona, Michigan, and Pennsylvania;
- national FHFA tract history through 2025;
- a validated canonical 2020 tract backbone, display geometry, and Connecticut geography bridge.
- seven versioned report-ready EDA figures with a governed manifest in the gold schema.

Every implemented Databricks table has an individual document in the
[data guide](docs/data/README.md) and a small example in [`data/samples`](data/samples/).

## Important limitations to resolve

- Visual EDA confirms that FHFA forecasting coverage is strongly tilted toward single-family,
  owner-occupied tracts. Forecasting claims must stay within that target population, while the
  broader current-state similarity experience can remain national.
- The current gold profile is useful for descriptive analysis, similarity prototyping, and early
  application work, but it is not a historical modeling panel.
- ACS releases before 2020 use 2010-vintage tract geography and have not yet been transformed into
  the canonical 2020 geography. Nonadditive measures must not be redistributed casually.
- Forecast origins, horizon-specific targets, censoring rules, and data splits do not exist yet.
- Preprocessing such as imputation, scaling, and dimensionality reduction must eventually be fit
  inside training folds rather than calculated on the full dataset.
- Connecticut is resolved: all 728 FHFA tract identifiers use the planning-region geography and
  map through the reviewed bridge, producing 662 current forecast candidates. Keep the explicit
  bridge-coverage checks in every gold rebuild.
- County/CBSA context, detailed analysis geometry, adjacency, and additional economic or supply
  sources are not implemented. Add them only when exploration or a baseline comparison gives them
  a clear role.

## Next milestone

Create the **historical modeling contract and tables** before fitting models or adding sources.

1. Finalize the point-in-time data contract:
   - forecast origin and source-availability rules;
   - primary one-year target and feasibility rules for three- and five-year targets;
   - historical geography policy by field family;
   - train, validation, calibration, temporal-test, and geographic-holdout assignments;
   - missingness, scaling, and feature-registry policies.
2. Build the historical neighborhood-state, feature, and target tables and run their
   leakage, uniqueness, reconciliation, and attrition checks.
3. Fit simple persistence and regional forecasting baselines before more complex models.
4. Build a transparent current-state similarity baseline and test whether its neighbors make
   sense across geography and housing composition.
5. Add another source only if these baselines expose a specific weakness it can address.

## Expected checkpoint outputs

- A reviewed historical state/feature/target contract.
- Leakage-safe historical gold tables and chronological split assignments.
- Forecast and similarity baselines with interpretable evaluation outputs.
- A documented decision about whether any new source or spatial feature is necessary before the
  next modeling iteration.

Do not expand the source catalog merely because another public dataset is available. The next
source should address a weakness found in exploration or produce measurable value over a simpler
baseline.

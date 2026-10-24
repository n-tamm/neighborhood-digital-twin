# Next Work: Data Readiness and Exploration

This is the short operational handoff for the next development session. It does not replace the
[project roadmap](ROADMAP.md) or the detailed [implementation guides](docs/implementation/README.md).

## Where the project sits

The core Databricks data pipeline is working through bronze, silver, canonical geography, and
current gold products. Structural validation is strong, but formal exploration and model-specific
historical preparation are the next major stages.

Current analytical outputs include:

- 85,528 rows in the complete current tract profile;
- 83,359 current similarity candidates;
- 50,601 current forecast candidates, which are only an availability screen and not training rows;
- 8,182 Arizona, Michigan, and Pennsylvania application-demo tracts;
- nationwide 2024 ACS coverage for the 50 states and Washington, D.C.;
- annual 2010-2024 ACS coverage for Arizona, Michigan, and Pennsylvania;
- national FHFA tract history through 2025;
- a validated canonical 2020 tract backbone, display geometry, and Connecticut geography bridge.

Every implemented Databricks table has an individual document in the
[data guide](docs/data/README.md) and a small example in [`data/samples`](data/samples/).

## Important limitations to resolve

- Formal EDA notebooks, reusable figure code, and final exploration outputs have not been built.
- The current gold profile is useful for descriptive analysis, similarity prototyping, and early
  application work, but it is not a historical modeling panel.
- ACS releases before 2020 use 2010-vintage tract geography and have not yet been transformed into
  the canonical 2020 geography. Nonadditive measures must not be redistributed casually.
- Forecast origins, horizon-specific targets, censoring rules, and data splits do not exist yet.
- Preprocessing such as imputation, scaling, and dimensionality reduction must eventually be fit
  inside training folds rather than calculated on the full dataset.
- Connecticut now has 879 current ACS land-tract profiles but zero forecast candidates. Confirm
  whether FHFA adopted the planning-region GEOIDs or whether Connecticut is genuinely absent from
  usable FHFA history before describing forecast coverage as national.
- County/CBSA context, detailed analysis geometry, adjacency, and additional economic or supply
  sources are not implemented. Add them only when exploration or a baseline comparison gives them
  a clear role.

## Next milestone

Create a **data-readiness and EDA checkpoint** before adding more sources or fitting models.

1. Investigate Connecticut FHFA identifiers and coverage. Record whether another safe geography
   bridge is needed and rerun the relevant coverage checks if it is.
2. Build organized exploration from the existing governed tables:
   - pipeline attrition and source coverage;
   - ACS missingness and relative margins of error;
   - FHFA history length, recency, and target availability;
   - FHFA coverage by geography and housing composition;
   - retained-versus-excluded community comparisons;
   - HPI level, annual-change, volatility, and temporal behavior;
   - one-, three-, and five-year target feasibility;
   - initial maps and other presentation-quality figures.
3. Use those findings to confirm two explicit initial scopes:
   - a national current-state similarity and application scope;
   - a three-state historical forecasting scope using Arizona, Michigan, and Pennsylvania.
4. Finalize the point-in-time data contract before building historical gold tables:
   - forecast origin and source-availability rules;
   - primary one-year target and feasibility rules for three- and five-year targets;
   - historical geography policy by field family;
   - train, validation, calibration, temporal-test, and geographic-holdout assignments;
   - missingness, scaling, and feature-registry policies.
5. After review, build the historical neighborhood-state, feature, and target tables and run their
   leakage, uniqueness, reconciliation, and attrition checks.

## Expected checkpoint outputs

- A small, clearly sequenced set of EDA notebooks backed by reusable package functions.
- Coverage, uncertainty, missingness, housing-composition, and temporal figures.
- A concise written data-readiness finding with any resulting scope changes.
- A reviewed historical state/feature/target contract.
- A documented decision about whether any new source or spatial feature is necessary before the
  first forecasting and similarity baselines.

Do not expand the source catalog merely because another public dataset is available. The next
source should address a weakness found in exploration or produce measurable value over a simpler
baseline.

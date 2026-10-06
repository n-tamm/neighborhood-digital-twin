# Contributing

The project is designed so contributors can own meaningful work without creating separate, incompatible pipelines. The shared contracts are the tract-year neighborhood state, forecasts, intervals, historical analogues, scenarios, and serving bundle.

## Before starting work

1. Read the [project charter](PROJECT_CHARTER.md) and the relevant numbered implementation guide.
2. Check the current branch. Do not work directly on `main`.
3. Create a descriptive branch such as `data/fhfa-feasibility`, `model/persistence-baseline`, or `app/tract-profile`.
4. Open or claim an issue with a clear output and acceptance criteria.
5. Confirm any new data source against [DATA_SOURCES.md](DATA_SOURCES.md).

## Where work belongs

- Use notebooks for investigation, diagnostic plots, and narrative demonstrations.
- Move reusable logic into `src/neighborhood_twin/`.
- Put user-interface code in `app/` and keep it dependent on stable serving contracts rather than research tables.
- Put repeatable command wrappers in `scripts/`; keep the actual logic in the package.
- Put source metadata and build provenance in `manifests/`.
- Record scope or architecture decisions in `docs/decisions/`.
- Do not commit raw data, secrets, local experiment stores, or machine-specific paths.

## Pull request expectations

A focused change should include:

- the issue or question being addressed;
- the data and model versions affected;
- tests or a clear reason tests do not apply;
- documentation for changed behavior or contracts;
- before/after evidence for analytical changes;
- checks for leakage, missingness, geography, or scenario support when relevant;
- no generated data or model artifact unless it is intentionally part of a small public demonstration bundle.

Reviewers should ask whether the change is reproducible, point-in-time valid, geographically honest, and understandable. More complexity is not automatically an improvement.

## Data and model contracts

Schema changes should be explicit. Do not silently rename columns, change units, alter target timing, or replace a model artifact in place. Update the relevant contract, increment its version, and document downstream effects.

The final temporal test must not influence feature selection, hyperparameters, calibration choices, or scenario ranges. If a result causes the team to revise the approach, return to the development and validation periods and document why the test is no longer considered locked.

## Commit and merge practice

- Keep commits focused and written in plain language.
- Main branch is protected and changes must be feature branches with a MR to main on GitHub.
- Do not add co-author metadata for automated tools. Use the disclaimer process where needed.
- Do not rewrite shared history without team agreement.
- Merge to `main` only after the branch checks pass and the change is ready for the rest of the team.
- Tag releases only from a clean, reviewed `main` branch.

## Definition of ready for integration

A component is ready when another contributor can consume it without reading the implementation notebook. It has a documented input, output, version, failure behavior, and small test fixture; its metrics or validation checks are available; and its limitations are clear.

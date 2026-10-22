# Data Source Policy and Initial Catalog

This is the project's data access statement and source-review record. The planned core data is published by U.S. federal agencies and is available to every team member through the public pages or APIs linked below. The project does not currently use private partner data, paid data, or data governed by a nondisclosure agreement.

A source appearing here is not automatically approved for modeling or redistribution. Before use, the team must confirm its current terms, record the publisher and access method in a versioned manifest, and document whether derived or source records may be included in a public demonstration bundle. Raw national data is downloaded from its publisher rather than redistributed through this repository.

## Core candidates

| Source | Intended use | Main limitations |
|---|---|---|
| [FHFA House Price Index](https://www.fhfa.gov/data/hpi/datasets) | Annual single-family tract target, lagged market history, and coverage analysis | Developmental and non-seasonally adjusted; excludes condominiums, cooperatives, multi-unit properties, and planned-unit developments; missing values are meaningful |
| [ACS five-year data](https://www.census.gov/data/developers/data-sets/acs-5year.html) | Housing composition, income, population, tenure, vacancy, housing burden, education, and commuting context | Released annually but pools 60 months of responses; adjacent releases overlap; margins of error, publication lag, and variable or geography changes must be retained |
| [2020 Census cartographic boundaries](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.2020.html) | Tract geometry for maps, joins, and adjacency | Simplified display geometry; does not contain demographic attributes |
| [Census relationship files](https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.2020.html) | Mapping earlier tract vintages to the canonical geography | Splits and merges require explicit weighting assumptions and validation |
| [FRED API](https://fred.stlouisfed.org/docs/api/fred/) and ALFRED vintages | Mortgage rates, inflation, labor-market, and broader economic context | API key; revisions; geographic grain varies; point-in-time use may require ALFRED or pinned snapshots |

## Current interpretation of the core housing data

The FHFA tract HPI is the initial forecast target, but it represents annual appreciation in a filtered single-family market rather than every housing unit in a tract. The project must use the precise label `FHFA single-family HPI` in target definitions, evaluation tables, and application text. A tract with many multifamily units may still receive a forecast for its covered single-family segment, but the application must not imply that the forecast describes the tract's full housing market.

ACS table B25024 or its release-specific equivalent provides counts of units in detached and attached single-family structures, buildings with two or more units, mobile homes, and other housing. The state table should derive mutually exclusive single-family, multifamily, and mobile/other shares with estimates and quality information retained. These fields support neighborhood description, similarity matching, representativeness warnings, and evaluation slices; they do not create a multifamily price index.

The tract-year table may contain one row for each annual forecast origin even though the sources have different time meanings. FHFA is annual. ACS tract estimates are annual releases of rolling five-year measurements: adjacent releases share four years of responses. The pipeline must retain both the ACS release year and survey window, use the latest release actually available at each forecast origin, and avoid interpreting small adjacent-release changes as precise one-year movement.

## Staged extensions

| Source | Possible value | Add only if |
|---|---|---|
| Census Building Permits Survey | Construction and supply context at county or metro level | The contextual geography is labeled honestly and the feature adds out-of-time value |
| LEHD Origin-Destination Employment Statistics | Employment density and accessibility from block-level records | The team can support the volume, vintage alignment, and documented aggregation |
| County Business Patterns | Establishment, payroll, employment, and industry context | County context is sufficient or any ZIP/ZCTA mapping is defensible |
| FEMA National Risk Index | Slow-moving hazard exposure and expected-loss context | Vintage and interpretation are documented and it is not treated as an annual causal driver |
| NOAA climate data | Weather and climate context | Station-to-tract linkage and engineering cost are justified by the research question |

## Source admission checklist

A source must answer all of these before it enters the main pipeline:

1. Can every teammate access it without a paid account, NDA, or data-use agreement?
2. Do its license and terms allow the planned analysis and public outputs?
3. Does it have enough historical depth for the intended evaluation?
4. Can we determine when each value became available?
5. Can it be joined to the analytical geography without invented precision?
6. Are missingness, revisions, schema changes, and coverage measurable?
7. Can its role in the model or application be explained plainly?
8. Does it avoid unnecessary individual, sensitive, or biomedical data?
9. Does it improve an ablation, scenario capability, or user interpretation enough to justify its cost?

## Required manifest fields

Every acquired source version should record:

- source name and owner;
- canonical landing page and exact download or API endpoint;
- request parameters;
- reference period, publication date, and retrieval timestamp;
- geographic grain and vintage;
- file size, row count, checksum, and schema fingerprint;
- license, terms, and citation link;
- known missing-value codes and coverage rules;
- local storage location and bronze table name;
- code version responsible for acquisition.

Raw national data is not committed to Git. The repository may include a small fixture or compact demonstration output only after its source terms permit redistribution and its attribution is recorded.

## Privacy and IRB position

The planned core uses aggregate public geographic statistics and does not recruit or interact with people. It does not require individual-level, personally identifying, biomedical, or protected research data. A new IRB review is therefore not expected, subject to course and university guidance. Any future source that changes that assessment must be reviewed before acquisition.

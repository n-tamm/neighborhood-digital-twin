# Application Data Access and Contracts

## Two explicit modes

The application never silently falls back between data modes.

- `sample` is the local default. It reads `app/sample_data/autauga_demo.json`, a reduced fixture
  made from real public project data for tract `01001020300`. It contains one tract and one
  historical match so developers can test layout and logic without credentials.
- `live` requires `DATABRICKS_WAREHOUSE_ID`. It uses the Databricks App service principal and
  parameterized SQL against the approved Unity Catalog tables. Missing configuration fails at
  startup rather than falling back to sample values.

Schema and catalog environment values are restricted to safe SQL identifiers. Tract input must be
exactly 11 digits, search text is length-limited, and user values are passed as query parameters.

## Live read boundary

| Table | App use |
|---|---|
| `gold_tract_profile_current` | Current labels, ACS profile, housing composition, coverage flags, and latest HPI context |
| `silver_fhfa_tract_year` | Observed annual single-family HPI history |
| `silver_tract_display_geometry_2020` | Selected and matched tract display centers |
| `serving_release_manifest` | Select one complete validated analogue release |
| `serving_analogue_availability_current` | Search universe, horizon availability, and unavailable reason |
| `serving_analogue_summary_current` | Match count and descriptive outcome distribution |
| `serving_analogue_match_current` | Approved top-ten ranked historical matches |
| `serving_analogue_explanation_current` | Stored feature-family and feature-level comparisons |
| `serving_analogue_trajectory_current` | Observed post-match annual HPI paths |

The interface does not read the modeling panel, evaluation tables, raw snapshots, or bronze data.
Every Databricks App table resource is `SELECT` only, and the warehouse permission is `CAN_USE`.

## Release-selection rule

At startup, live mode reads the manifest newest first and accepts only a release with validated
rows for all five historical-analogue components: availability, summary, matches, explanations,
and trajectories. Every neighborhood query then uses that same release ID. This prevents an app
session from combining a new match table with an older explanation or trajectory table.

The current analogue schema is version `1.1`. The application displays the release ID and source
lineage in the Methods tab. A future schema change should add an explicit compatibility check
before new fields are used.

## Current compromises and next contract

The analogue products are fully serving-oriented. The current profile and FHFA history are compact
enough for this foundation but still come from gold and silver. They should move behind a versioned
profile/history serving release when the forecasting contract is published.

The next forecast contract must contain, at minimum, tract and horizon keys, target definition,
point estimate, lower and upper interval, as-of year, model and feature versions, baseline result,
availability reason, release status, and enough driver information for a stable explanation. The
app should continue showing its current unavailable state until that contract passes validation.

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
exactly 11 digits, county GEOIDs must contain five digits, state abbreviations must contain two
letters, search text is length-limited, and user values are passed as query parameters.

## Live read boundary

| Table | App use |
|---|---|
| `gold_tract_profile_current` | Current labels, ACS profile, housing composition, coverage flags, and latest HPI context |
| `silver_fhfa_tract_year` | Observed annual single-family HPI history |
| `silver_connecticut_tract_bridge_2020_2024` | Current Connecticut FHFA identifiers mapped to canonical 2020 tracts |
| `silver_tract_display_geometry_2020` | Simplified selected, nearby-context, and matched tract outlines plus display bounds |
| `serving_release_manifest` | Select one complete validated analogue release |
| `serving_analogue_availability_current` | Search universe, state/county/tract navigation, horizon availability, and unavailable reason |
| `serving_analogue_summary_current` | Match count and descriptive outcome distribution |
| `serving_analogue_match_current` | Approved top-ten ranked historical matches |
| `serving_analogue_explanation_current` | Stored feature-family and feature-level comparisons |
| `serving_analogue_trajectory_current` | Observed post-match annual HPI paths |

The interface does not read the modeling panel, evaluation tables, raw snapshots, or bronze data.
Every Databricks App table resource is `SELECT` only, and the warehouse permission is `CAN_USE`.

Connecticut requires one additional identity step. Current FHFA rows use planning-region tract
identifiers, while the application and display geometry use canonical 2020 tract GEOIDs. The
history query applies the audited one-to-one Connecticut bridge before filtering on the selected
tract. Other states retain their source GEOID directly. Without this step, a Connecticut profile
can correctly report available FHFA history while the chart query returns no rows.

## Geometry query and performance boundary

Live mode converts stored WKB into GeoJSON in Databricks SQL with
[`st_geomfromwkb`](https://docs.databricks.com/aws/en/sql/language-manual/functions/st_geomfromwkb)
and
[`st_asgeojson`](https://docs.databricks.com/aws/en/sql/language-manual/functions/st_asgeojson).
This avoids a second geometry library in the application runtime. The selected-neighborhood query
returns the chosen tract and an expanded local display window, ordered by center proximity and
capped at 80 rows. The match query returns only the 20 approved candidate outlines across the two
horizons.

The seven result sets needed for one neighborhood are executed over one SQL connection instead of
opening one connection per table. Streamlit then caches the assembled neighborhood for 15 minutes,
so switching tabs, horizons, or inspected matches does not rerun warehouse queries.

The geographic browser issues small aggregate or identity queries in sequence: state coverage,
counties for one state, and tracts for one county. Each result is cached for one hour. These
queries run only after the user switches from the default neighborhood map to `Browse U.S.`, so
the additional navigation does not slow the normal tract page load.

The state map requires one canonical named state identity. Its aggregation excludes availability
rows with missing state labels and limits the mapped view to the 50 states and District of
Columbia. Text search remains the access path for territories and for records that cannot be
placed on Plotly's state geometry.

All maps use canonical 2020 tract outlines, including Connecticut. Current profile data,
historical matches, and display geometry therefore share one map identity even when a newer source
uses planning-region codes. The bridge maps identifiers only; it does not reshape or area-weight
tract geometry.

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

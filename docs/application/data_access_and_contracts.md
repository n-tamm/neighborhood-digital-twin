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

The optional live address lookup is separate from Databricks SQL. It sends one user-submitted
address to the public
[U.S. Census Geocoder](https://www.census.gov/data/developers/data-sets/Geocoding-services.html)
with the `Public_AR_Current` benchmark and `Census2020_Current` geography vintage. The response
must contain an 11-digit 2020 tract GEOID before the app uses it. The address is not persisted in
Unity Catalog, logs created by this project, or model features. The app explains the external
request before submission and fails visibly when Census cannot match an address.

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
| `serving_forecast_availability_current` | Per-tract and per-horizon availability, locked release decision, and unavailable reason |
| `serving_forecast_current` | Approved current point forecasts, intervals, state baseline, scope notes, and evaluation context |

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
counties for one state, and tracts for one county. The queries join the independently activated
forecast-availability release at both one- and three-year horizons so analogue and forecast
readiness remain distinct. Tract choices also join compact profile counts for readable population
context and four bounding-box fields from the display-only geometry table. The browser uses those
fields to draw clickable center points without transferring every tract polygon. Each result is
cached for one hour. These queries run only after the user switches from the default neighborhood
map to `Browse U.S.`, so the additional navigation does not slow the normal tract page load.

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

Forecast releases are selected independently. A forecast release is active only when the manifest
contains validated rows for both `serving_forecast_current` and
`serving_forecast_availability_current`. This lets the app use the newest complete forecast
without pretending it shares a build ID with the analogue release. Every forecast query uses the
selected forecast release ID.

The version-2 forecast release contains both supervised models at both horizons for model-ready
tracts. Availability remains one row per tract and horizon and is true only when both model rows
exist. Evaluation warnings are fields on the model results rather than reasons to suppress a
horizon.

## Current compromises

The analogue and forecast model products are serving-oriented. Current profile and FHFA history
remain compact reads from gold and silver rather than a shared versioned profile/history release.
That is acceptable for the current capstone build but means their lineage is displayed separately
from the two model releases.

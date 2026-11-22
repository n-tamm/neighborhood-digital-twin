# Application

This folder contains the first working Neighborhood Housing Intelligence application. It is a
map-first Streamlit interface that lets a user select a 2020 Census tract, review its current
community and housing profile, inspect observed FHFA single-family HPI history, and explore
approved historical analogues. Live mode also shows the approved one-year FHFA HPI forecast,
calibrated interval, state-trend baseline, and explicit locked-gate state for the withheld
three-year horizon. The reduced local fixture intentionally keeps forecasting unavailable.

The interface uses a deep navy theme with high-contrast teal, blue, and gold semantics across the
application and its maps. The primary map combines a visible selected-tract point with its
simplified boundary and nearby tract outlines; selecting a nearby tract opens it. A separate
`Browse U.S.` map lets a user select a state, then narrow through county and tract controls without
loading model outputs for every place in advance. State and county summaries report both analogue
and approved one-year forecast coverage with comma-formatted counts. Tract choices include
population and both model statuses so an 11-digit GEOID is not the only distinguishing context.

The live app also offers address-to-tract lookup through the public U.S. Census Geocoder. The
submitted address is sent to Census only for that lookup and is not written to project tables. A
successful match adds a recognizable incorporated place, census-designated place, or county
subdivision label when Census returns one.

The analogue experience layers numbered points over actual matched-tract polygons: points remain
visible at the national extent, while boundaries become useful after zooming. Its selectable
county table is the single detailed-match control, so persistent table selection cannot conflict
with a second dropdown.

The Data Science tab is a self-contained walkthrough of the implemented pipeline, forecast, and
similarity evidence. It uses reviewed figures produced by the repository's Databricks workflows,
with the release decision and limitations explained next to each figure.

The interface is intentionally thin. It does not train models, rebuild features, download source
data, or query `gold_modeling_panel`. Live mode uses a Databricks App service principal and reads
only the compact tables declared in `databricks.yml`.

## Folder contents

| Path | Responsibility |
|---|---|
| `streamlit_app.py` | Page structure, tract search, tabs, and user-facing states |
| `neighborhood_app/data.py` | Configuration, release validation, parameterized SQL, and local fixture repository |
| `neighborhood_app/geocoding.py` | Bounded Census address-to-2020-tract lookup |
| `neighborhood_app/charts.py` | Map and chart construction with consistent visual semantics |
| `neighborhood_app/ui.py` | Formatting, status badges, metric cards, and responsive styles |
| `assets/data_science/` | Reviewed, workflow-generated figures shown in the Data Science tab |
| `sample_data/autauga_demo.json` | Reduced real-data fixture for credential-free local development |
| `.streamlit/config.toml` | Shared theme and Streamlit runtime preferences |
| `app.yaml` | Databricks App command and resource-backed environment configuration |
| `requirements.txt` | Minimal Databricks App runtime dependencies |

## Run locally

From the repository root, install the application and development dependencies:

```powershell
python -m pip install -e ".[dev,app]"
python -m streamlit run app/streamlit_app.py
```

The default is `sample` mode. It loads one real public-data tract and one real historical match so
the interface can be developed without credentials. The banner and explanatory text identify the
fixture as reduced; it must not be used to make national coverage or performance claims.

Run the focused app checks with:

```powershell
python -m pytest tests/unit/test_app_data.py tests/unit/test_app_geocoding.py tests/unit/test_app_presentation.py
```

## Live Databricks mode

The bundle resource is named `neighborhood_housing_intelligence`, while the Databricks App is
named `neighborhood-intelligence`. Validate and deploy from the repository root:

```powershell
databricks bundle validate --profile neighborhood-twin -t team
databricks bundle deploy --profile neighborhood-twin -t team
databricks bundle run neighborhood_housing_intelligence --profile neighborhood-twin -t team
```

Databricks injects the SQL warehouse identifier through the `sql-warehouse` app resource. No
token, host, or password belongs in source control. The initial workspace app remains private
until access is explicitly granted after live validation.

## Current product boundaries

- ACS fields describe the broader current community and housing stock and are rolling five-year
  estimates.
- FHFA history and analogue outcomes describe the single-family housing market, not every home or
  the multifamily market.
- Historical analogue outcomes are observed evidence from earlier communities, not forecasts or
  causal comparisons.
- The forecast tab shows only the approved one-year release. It never substitutes an analogue
  statistic, validation prediction, or fabricated demonstration value for an unavailable horizon.
- The three-year method failed its locked accuracy and uncertainty gates and is shown as withheld,
  not silently replaced.
- Simplified geometry locates places on the map but is not used for similarity, adjacency, or
  distance claims.
- Connecticut history uses the audited current-to-2020 identifier bridge so the profile, trend
  chart, and canonical 2020 display outline refer to the same tract.
- Live neighborhood result sets share one warehouse connection and are cached by tract so richer
  boundary maps do not require repeated SQL startup on tab or horizon changes.
- State, county, and tract navigation lists are compact, parameterized, and cached separately. The
  state browser is loaded only when the user switches away from the default neighborhood map.
- Address lookup is optional, live-mode only, and calls the public Census Geocoder on submission.
  It does not create a project record or make the entered address a modeling feature.
- The Data Science tab is explanatory. Its bundled figures are immutable copies of governed
  builds; the app does not recalculate evaluation metrics or select models at runtime.

The implementation and interpretation details are in
[the application documentation](../docs/application/README.md).

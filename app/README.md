# Application

This folder contains the first working Neighborhood Housing Intelligence application. It is a
map-first Streamlit interface that lets a user select a 2020 Census tract, review its current
community and housing profile, inspect observed FHFA single-family HPI history, and explore
approved historical analogues. Forecasting has a deliberate unavailable state until the
forecasting workstream publishes a selected model, calibrated interval, and versioned serving
contract.

The primary map uses the selected tract's simplified boundary and nearby tract outlines. The
analogue experience uses actual matched-tract polygons and side-by-side footprint comparisons
rather than point markers.

The interface is intentionally thin. It does not train models, rebuild features, download source
data, or query `gold_modeling_panel`. Live mode uses a Databricks App service principal and reads
only the compact tables declared in `databricks.yml`.

## Folder contents

| Path | Responsibility |
|---|---|
| `streamlit_app.py` | Page structure, tract search, tabs, and user-facing states |
| `neighborhood_app/data.py` | Configuration, release validation, parameterized SQL, and local fixture repository |
| `neighborhood_app/charts.py` | Map and chart construction with consistent visual semantics |
| `neighborhood_app/ui.py` | Formatting, status badges, metric cards, and responsive styles |
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
python -m pytest tests/unit/test_app_data.py tests/unit/test_app_presentation.py
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
- The forecast tab never substitutes an analogue statistic, validation prediction, or fabricated
  demonstration value for an approved forecast.
- Simplified geometry locates places on the map but is not used for similarity, adjacency, or
  distance claims.
- Live neighborhood result sets share one warehouse connection and are cached by tract so richer
  boundary maps do not require repeated SQL startup on tab or horizon changes.

The implementation and interpretation details are in
[the application documentation](../docs/application/README.md).

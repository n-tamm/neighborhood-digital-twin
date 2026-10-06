# Application

This folder will contain the public, map-driven Neighborhood Digital Twin. The planned implementation is Streamlit because it keeps the application close to the Python analysis stack and can be deployed directly from GitHub.

The app should read only a compact, versioned serving bundle. It should not download national source data, run the ETL pipeline, train models, or require a live Databricks connection during a user session.

Planned organization:

```text
app/
├── streamlit_app.py       # public entry point
├── pages/                 # optional multipage views
├── components/            # reusable charts, map controls, and notices
└── assets/                # small static images and style resources
```

Required views are map/search, current state, history, forecast, drivers, historical analogues, comparison, scenario lab, and methods/limitations. Application code should consume contracts produced by `src/neighborhood_twin/app_data/`, not reach into modeling internals.

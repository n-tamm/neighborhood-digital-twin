# `neighborhood_twin` package

Current and planned module boundaries:

- `data`: implemented source catalog, acquisition, manifests, ACS requests, and Databricks bronze helpers;
- `validate`: implemented persisted bronze profiling for schema, grain, ranges, uniqueness, parseability, source lineage, and FHFA-to-ACS tract coverage;
- `geography`: GEOIDs, crosswalks, geometry, adjacency, and regional membership;
- `transform`: implemented latest-snapshot selection, bronze-to-silver normalization,
  source-specific validation, and publication for FHFA and ACS;
- `features`: point-in-time feature and target construction;
- `models`: baselines, candidate forecasters, calibration, and model persistence;
- `representations`: PCA or other representations, analogue search, and optional clustering;
- `simulation`: scenario definitions, support checks, and distribution generation;
- `evaluation`: backtesting, metrics, slices, ablations, and visual diagnostics;
- `app_data`: serving-bundle construction and contract validation;
- `common`: shared configuration, logging, hashing, and identifiers.

Dependencies should move in one direction: source and geography modules feed features; features feed models and representations; those outputs feed simulation and application exports. The Streamlit app should not import acquisition or training code. The first implemented `data` package keeps engine-neutral source logic separate from the small Spark-specific adapter so most behavior can be tested without Databricks.

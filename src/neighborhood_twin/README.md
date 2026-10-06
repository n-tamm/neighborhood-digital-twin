# `neighborhood_twin` package

Planned module boundaries:

- `acquire`: source-specific downloads and raw snapshot metadata;
- `validate`: schema, grain, ranges, uniqueness, and quality checks;
- `geography`: GEOIDs, crosswalks, geometry, adjacency, and regional membership;
- `transform`: bronze-to-silver normalization and shared table operations;
- `features`: point-in-time feature and target construction;
- `models`: baselines, candidate forecasters, calibration, and model persistence;
- `representations`: PCA or other representations, analogue search, and optional clustering;
- `simulation`: scenario definitions, support checks, and distribution generation;
- `evaluation`: backtesting, metrics, slices, ablations, and visual diagnostics;
- `app_data`: serving-bundle construction and contract validation;
- `common`: shared configuration, logging, hashing, and identifiers.

Dependencies should move in one direction: source and geography modules feed features; features feed models and representations; those outputs feed simulation and application exports. The Streamlit app should not import acquisition or training code.

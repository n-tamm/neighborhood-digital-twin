# Artifacts

This folder is the boundary between reproducible code and generated output. Model files, diagnostics, local experiment output, and serving bundles are written here during development and are ignored by default.

Planned local areas:

- `local/`: temporary run output and diagnostics;
- `models/`: serialized estimators, preprocessors, and calibration objects;
- `bundles/`: versioned application-serving bundles.

A serving bundle may be published only when it is small, permitted by source terms, and has a manifest containing its version, build time, source vintages, model version, supported geographies and horizons, row counts, hashes, and known limitations. Large artifacts should use release storage or another documented artifact location rather than ordinary Git history.

# Data

This folder is for local data used by the pipeline. With the exception of tiny, redistributable test fixtures or approved demonstration records, its contents are intentionally excluded from Git.

Planned zones:

```text
data/
├── external/     # manually supplied third-party source files
├── raw/          # immutable downloaded snapshots
├── interim/      # parsed or partially standardized data
├── processed/    # local gold tables and analysis-ready subsets
└── demo/         # compact, permitted data prepared for the public app
```

Every raw snapshot must retain its source URL, retrieval date, parameters, checksum, and applicable terms. Do not edit a raw file in place. A corrected or updated source becomes a new version with a new checksum. Create a dedicated manifest location only when the acquisition pipeline produces real manifests that need to be shared.

Databricks Delta tables may live outside this local folder, but they should use the same bronze/silver/gold definitions and retain equivalent lineage fields.

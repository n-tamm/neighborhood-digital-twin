# Data

This folder is for local data used by the pipeline. With the exception of tiny, redistributable
test fixtures, approved demonstration records, and the documented table samples in `samples/`, its
contents are intentionally excluded from Git.

```text
data/
|-- external/     # manually supplied third-party source files
|-- raw/          # immutable downloaded snapshots
|-- interim/      # parsed or partially standardized data
|-- processed/    # local gold tables and analysis-ready subsets
|-- demo/         # compact, permitted data prepared for the public app
`-- samples/      # tracked, tiny examples from each implemented Databricks table
```

Every raw snapshot must retain its source URL, retrieval date, parameters, checksum, and applicable
terms. Do not edit a raw file in place. A corrected or updated source becomes a new version with a
new checksum. Create a dedicated manifest location only when the acquisition pipeline produces real
manifests that need to be shared.

Databricks Delta tables may live outside this local folder, but they should use the same
bronze/silver/gold definitions and retain equivalent lineage fields.

The files in [`samples/`](samples/) contain a small representative extract of no more than ten
rows per table. They are intended
only for inspecting names, types, nulls, and general shape. Databricks remains authoritative for
analysis, row counts, lineage, and quality history. See the corresponding
[table documentation](../docs/data/README.md) for grain, structure, intended use, and limitations.

# Table Samples

[Data folder overview](../README.md) | [Table documentation](../../docs/data/README.md)

This folder contains small JSON Lines extracts from every implemented Databricks table. Each line
is one real development-table row serialized as JSON, and each file contains at most ten rows.
JSON Lines keeps data types and nulls clearer than a very wide CSV while remaining easy to inspect
in GitHub, Python, or a text editor.

The samples are intentionally small and should only be used to understand structure and naming.
They are not test fixtures, modeling inputs, or a replacement for the shared Delta tables. Binary
geometry is omitted because even a few encoded polygons would make the repository unnecessarily
large; those samples include the geometry's byte length instead.

The extracts were refreshed from the `workspace.neighborhood_twin_bronze`,
`neighborhood_twin_silver`, `neighborhood_twin_gold`, and `neighborhood_twin_quality` schemas
through the October 30, 2026 baseline-modeling and expanded visual-EDA runs and the preceding
model-readiness build. Table counts, quality
histories, and source snapshots will continue to change as the pipeline is rerun, so Databricks
remains the authoritative source.

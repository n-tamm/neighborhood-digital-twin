# `source_snapshot_manifest`

[Back to the data documentation index](README.md)

- **Layer:** Governance and bronze
- **Databricks table:** `workspace.neighborhood_twin_bronze.source_snapshot_manifest`
- **Sample:** [source_snapshot_manifest.jsonl](../../data/samples/source_snapshot_manifest.jsonl)

- **Grain and key:** one row per immutable source snapshot; keyed by `source_snapshot_id`.
- **Purpose:** records where a source came from, when it was retrieved, how it is licensed, where
  its raw object is stored, and whether it passed acquisition checks.
- **Main structure:** source identity, retrieval metadata, content hash, governed volume path,
  licensing fields, validation status, and validation messages.
- **Use:** begin here when reproducing or auditing an ingestion. Analytical code should not join
  this table directly unless it needs source-level lineage.

The managed Databricks table is authoritative. Its table description and column comments are
applied from source-controlled metadata after schema-overwriting pipeline runs.

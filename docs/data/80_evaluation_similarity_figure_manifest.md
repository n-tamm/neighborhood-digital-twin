# `similarity_evaluation_figure_manifest`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:**
  `workspace.neighborhood_twin_evaluation.similarity_evaluation_figure_manifest`
- **Sample:**
  [`data/samples/similarity_evaluation_figure_manifest.jsonl`](../../data/samples/similarity_evaluation_figure_manifest.jsonl)
- **Grain and key:** one rendered figure in the current similarity communication build.
- **Purpose:** connects each similarity figure to its managed-volume file, build time, case-study
  configuration, and source audit, selection, exact-tree, and serving lineage.

The manifest is overwritten only after all five expected files pass identity, lineage, and minimum
file-size checks. Figure directories are versioned by build ID, so replacing the current manifest
does not remove earlier builds. The manifest identifies the current matched set; selecting files
individually by modification time is not supported.

The case GEOID and horizon are repeated on every row because the fifth figure is a declared
communication example. They do not imply that the other four figures were calculated from that
one tract.

The current reviewed build is `20261121T204510966976Z`. It contains five files ranging from
154,297 to 354,645 bytes and points to analogue audit run
`d4957281b60a407a9dc0b1a84d7c9e57`, selection run
`9da77fab59bd41d8b8b602493131a890`, exact-tree run
`344fbe71819f4a779b36701a5fdaf7b8`, and serving release
`analogue-20261121T163609734965Z`. Job 900 run `477954237899280` reapplied table and column
metadata after publication. The tracked JSONL is a point-in-time example from the preceding
figure build; the managed manifest is authoritative for the current build.

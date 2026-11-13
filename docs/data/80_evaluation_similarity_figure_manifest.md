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

The current reviewed build is `20261113T193948450115Z`. It contains five files totaling about
1.17 MB and points to analogue audit run `a7f7d2c018214708a955a4ac9b9ec0c4`, selection run
`f161ff3938b34032afe3634ef3de38df`, exact-tree run
`fae78721154347039d41864bad2e871a`, and serving release
`analogue-20261113T132155097077Z`. Job 900 confirmed a table description and comments on all 14
columns.

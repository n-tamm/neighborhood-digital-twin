# `similarity_evaluation_figure_manifest`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:**
  `workspace.neighborhood_twin_evaluation.similarity_evaluation_figure_manifest`
- **Sample:** a small real manifest sample will be added after the first validated build.
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

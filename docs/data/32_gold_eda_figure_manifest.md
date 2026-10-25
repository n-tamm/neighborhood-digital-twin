# `gold_eda_figure_manifest`

[Back to the data documentation index](README.md)

- **Layer:** Gold exploration summaries
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_eda_figure_manifest`
- **Sample:** [gold_eda_figure_manifest.jsonl](../../data/samples/gold_eda_figure_manifest.jsonl)

- **Grain and key:** one row per figure in the current visual-EDA build.
- **Purpose:** makes every report-ready PNG discoverable and ties its title and intended use to a
  versioned file in the managed `eda_figures` volume.
- **Main structure:** figure order, stable name, title, purpose, Unity Catalog volume path, file
  format, byte size, and build lineage.
- **Caution:** the manifest describes the latest successful build, while older versioned figure
  directories remain in the volume. Use the build ID in this table when selecting a matched set.

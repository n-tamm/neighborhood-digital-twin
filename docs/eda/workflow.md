# EDA Workflow

## Implemented sequence

The EDA workflow is split into governed computation and rendering:

1. `400 Exploration | EDA Readiness` builds data-readiness summaries and quality metrics.
2. `401 Exploration | Visual EDA` runs
   [`02_build_visual_eda.py`](../../notebooks/04_exploration/02_build_visual_eda.py) to refresh the
   small visual-summary tables.
3. The same job runs
   [`03_render_eda_figures.py`](../../notebooks/04_exploration/03_render_eda_figures.py) to render
   the twelve PNGs.
4. Rendering checks that all twelve files exist and exceed 10,000 bytes before publishing
   `gold_eda_figure_manifest` as the current matched set.
5. Job `900 Operations | Table Metadata` reapplies table descriptions and column comments after
   overwritten Delta tables are published.

Separating summary construction from plotting keeps population definitions in tested Spark code
and keeps the rendering notebook focused on presentation. A chart should not silently implement a
second version of an eligibility or cohort rule.

## Storage and lineage

- Summary and manifest schema: `workspace.neighborhood_twin_gold`
- Figure volume: `workspace.neighborhood_twin_gold.eda_figures`
- Manifest table: `workspace.neighborhood_twin_gold.gold_eda_figure_manifest`
- Quality schema: `workspace.neighborhood_twin_quality`

Each manifest row records the sequence, stable filename, title, purpose, build ID, volume path,
file type, and byte size. Previous build directories remain versioned even when the manifest is
replaced by a newer successful build.

## Shared analytical rules

- ACS annual releases are overlapping five-year estimates, not independent one-year samples.
- FHFA tract HPI describes a filtered single-family market rather than every housing type.
- Analyses crossing the 2020 tract redesign use the governed stable cohort. Broader post-2020
  analysis uses the current-vintage cohort and is reported separately.
- Arizona, Michigan, and Pennsylvania are the map-review states. They do not limit the national
  source or modeling scope.
- Map geometry is display-only. It is not approved for distance, adjacency, or spatial weights.
- Missing map observations use a dedicated gray so they cannot be mistaken for low values.
- Fixed observed endpoints are used for change maps; a tract's individual latest date is not
  substituted into a common-period comparison.

## How to reproduce the current workflow

Follow the canonical [pipeline run-order guide](../PIPELINE_RUN_ORDER.md). When the approved gold
and model-readiness tables already exist, the relevant commands are:

```powershell
databricks bundle run data_readiness_eda --profile neighborhood-twin -t team
databricks bundle run visual_eda --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

Documentation-only changes do not require these jobs. The exact current build and export command
are maintained in the [EDA figure inventory](../../reports/EDA_FIGURES.md).

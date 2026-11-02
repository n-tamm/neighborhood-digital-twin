# Documentation

The project keeps several focused technical documentation areas:

- [System architecture](ARCHITECTURE.md) explains the analytical and application boundaries.
- [Databricks pipeline run order](PIPELINE_RUN_ORDER.md) is the canonical operational sequence for
  setup, source refreshes, downstream rebuilds, recovery, and metadata publication.
- [EDA documentation](eda/README.md) documents the implemented workflow and provides one
  interpretation guide per published EDA visual.
- [Forecasting documentation](forecasting/README.md) separates target and split design, baseline
  choices, module behavior, Databricks execution, metrics, and current results.
- [Similarity documentation](similarity/README.md) explains the representation design, retrieval
  implementation, workflow, diagnostics, and current results.
- [Model-evaluation documentation](model_evaluation/README.md) documents the evaluation workflow
  and each of the seven current model-diagnostic visuals.
- [Implementation guide](implementation/README.md) provides the ordered build plan from data feasibility through final delivery.
- [Data guide](data/README.md) documents implemented table grains, intended use, limitations, and small development-table samples.
- [Tract vintage coverage](TRACT_VINTAGE_COVERAGE.md) explains why pre-2020 history uses a
  smaller stable-tract subset and how that affects modeling and interpretation.

The [project charter](../PROJECT_CHARTER.md), [roadmap](../ROADMAP.md), and [data access statement](../DATA_SOURCES.md) remain at the repository root because they are primary project entry points.

Keep documentation close to the code or decision it explains. Add a separate contract, configuration, operations, or reference folder only when real implementation produces several files with that distinct purpose.

The application does not yet have implementation documentation because no interactive application
code or serving contract has been implemented. Its current plan remains in the implementation
guide; a dedicated application documentation area should be added with the first working app
component rather than describing planned behavior as a completed product.

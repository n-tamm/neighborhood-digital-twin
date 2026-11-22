# `forecast_final_evaluation_figure_manifest`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.forecast_final_evaluation_figure_manifest`
- **Sample:** [forecast_final_evaluation_figure_manifest.jsonl](../../data/samples/forecast_final_evaluation_figure_manifest.jsonl)
- **Grain and key:** one figure in a versioned final forecast build.
- **Purpose:** links report-ready figures to their source finalization run and managed-volume files.

The three-row version-2 manifest identifies side-by-side validation and later-period MAE, model-specific interval coverage, and mean observed-versus-predicted figures. Each row records its build, ordering, file path, source run, and generation time.

The manifest prevents a figure from being presented without knowing which model run produced it. A later rebuild should use a new immutable build directory rather than overwriting these files.

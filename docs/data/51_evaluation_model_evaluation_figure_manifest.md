# `model_evaluation_figure_manifest`

[Back to the data documentation index](README.md)

- **Layer:** Model evaluation
- **Databricks table:** `workspace.neighborhood_twin_evaluation.model_evaluation_figure_manifest`
- **Sample:** [model_evaluation_figure_manifest.jsonl](../../data/samples/model_evaluation_figure_manifest.jsonl)
- **Grain and key:** one rendered figure in the current evaluation build.
- **Purpose:** connects every published evaluation visual to its file, build timestamp, and source
  forecast and similarity run IDs.

The manifest is replaced only after all expected figures render and pass a minimum file-size
check. Figure files remain versioned in the evaluation schema's `model_evaluation_figures` managed
volume, so replacing the current manifest does not erase prior builds.

The current build is `20261030T203807838205Z`. It contains seven visually reviewed PNGs; the
smallest is 97,768 bytes. See the [model evaluation figure guide](../../reports/MODEL_EVALUATION_FIGURES.md)
for the figure inventory, initial findings, and reproduction instructions.

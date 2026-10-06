# Repository Structure

## Why this layout exists

The repository separates intent, implementation, data, generated output, and deployment. That prevents three common problems: notebooks becoming the only pipeline, application code depending on private research state, and generated files being mistaken for source.

```text
neighborhood-digital-twin/
├── README.md
├── PROJECT_CHARTER.md
├── ROADMAP.md
├── DATA_SOURCES.md
├── CONTRIBUTING.md
├── pyproject.toml
├── app/
├── artifacts/
├── configs/
├── data/
├── docs/
│   ├── architecture/
│   ├── contracts/
│   ├── decisions/
│   ├── implementation/
│   ├── reference/
│   └── runbooks/
├── infrastructure/
├── manifests/
├── notebooks/
├── reports/
├── scripts/
├── src/neighborhood_twin/
└── tests/
```

## Placement rules

### Root documents

The root answers the first questions a new contributor has: what the project is, what is in scope, what data is allowed, how work is organized, and what happens next. Do not place detailed method notes or one-off analyses at the root.

### `docs/`

Documentation is organized by lifecycle. Numbered implementation guides describe how to build the system. Architecture documents explain stable cross-cutting structure. Contracts define interfaces. Decision records preserve the reasoning behind choices. Reference documents describe the finished system, and runbooks explain how to operate it.

### `notebooks/` versus `src/`

A notebook may answer a question once. A package module must answer it repeatedly. When an exploratory transformation becomes part of the pipeline, move it into `src/` and leave the notebook as a thin consumer. This makes tests, Databricks jobs, scripts, and the application share the same logic.

### `configs/` versus code constants

Configuration contains choices that vary by source, experiment, horizon, or deployment. Code contains behavior and invariants. A scenario range belongs in configuration; the rule that rejects values outside that range belongs in code.

### `manifests/` versus `data/`

Data files are large and usually local. Manifests are small evidence about those files and are normally committed. A teammate should be able to identify the exact source version without receiving the raw file through Git.

### `artifacts/` versus `reports/`

Artifacts are machine-consumable outputs such as model objects, calibrated intervals, and serving bundles. Reports are human-facing figures, tables, narrative drafts, and presentation material. Both are generated, but they have different consumers and release rules.

### `app/` versus `src/neighborhood_twin/app_data/`

The app owns interaction and presentation. `app_data` owns reproducible export and validation of the serving contract. This prevents Streamlit callbacks from becoming an undocumented data pipeline.

### `scripts/` versus package modules

Scripts orchestrate. Package modules implement. A script may parse command-line arguments and call `build_features(config)`, but the feature logic should remain importable and testable.

### `infrastructure/`

Only tested deployment definitions belong here. A future Databricks asset bundle, documentation build configuration, or deployment helper can live here. Secrets and cloud state do not.

## Growth rules

- Add a new top-level folder only if it represents a new kind of artifact or lifecycle responsibility.
- Prefer a clear contract to a new service.
- Avoid `utils.py` dumping grounds; shared code should have a named responsibility.
- Keep raw-source details behind acquisition and silver interfaces.
- Do not add a second framework for the same job without a recorded reason.
- Archive or delete superseded generated artifacts rather than labeling several files `final`.

## Naming

- Use `snake_case` for Python modules, data fields, and configuration keys.
- Use stable table names with a layer and subject, such as `silver_acs_tract_year`.
- Put versions in manifests and metadata rather than adding dates to every source filename by hand.
- Use numbered notebook and implementation-guide prefixes only where order matters.
- Give branches a workstream prefix: `data/`, `geo/`, `model/`, `scenario/`, `app/`, `docs/`, or `infra/`.

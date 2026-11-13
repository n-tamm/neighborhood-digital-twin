# Notebooks

Notebooks are for exploration, diagnostics, explanation, and thin Databricks orchestration. Reusable acquisition and transformation logic belongs in the tested package rather than notebook cells.

Use numbered groups that mirror the implementation guide:

```text
notebooks/
├── 01_feasibility/
├── 02_data_quality/
├── 03_transformation/
├── 04_exploration/
├── 05_modeling/
├── 06_representations/
├── 07_scenarios/
└── 08_final_analysis/
```

Each notebook should state its question, inputs, expected grain, data and code versions, and whether its output is exploratory or part of a final result. Reusable functions move to `src/neighborhood_twin/`; final figures are generated through repeatable code and written to `reports/generated/`.

The first entry point is `01_feasibility/01_ingest_core_sources.py`. It calls tested package functions to create governed raw snapshots and bronze tables. `01_feasibility/02_ingest_historical_acs.py` adds a bounded, reviewed state-by-release batch without reacquiring FHFA or geography files. `02_data_quality/01_profile_bronze_sources.py` records coverage, integrity, parseability, missingness, internal consistency, and cross-source tract-match metrics. The separate silver job starts at `03_transformation/01_build_silver_source_tables.py`; it reads accepted bronze data without rerunning acquisition. These notebooks remain small orchestration layers, while reusable behavior stays in the package.

`03_transformation/02_build_tract_relationship.py` validates the registered official Census relationship snapshot, upgrades its manifest status, and publishes the typed relationship and geography-quality tables. It deliberately stops short of transforming ACS measures: the source contains land overlap, not population or housing weights.

`03_transformation/03_build_display_geometry.py` parses the registered 1:500,000 cartographic archive in a pinned GIS environment. It publishes valid WKB geometry for application maps and labels it as display-only so later spatial modeling cannot silently reuse it for adjacency or precise measurements.

`04_exploration/01_build_data_readiness.py` is the first formal EDA checkpoint. It publishes
reusable state coverage, ACS uncertainty, FHFA history-depth, and forecast-horizon summaries
instead of recomputing national joins in presentation cells. Its publication checks are stored in
the quality schema, including failed attempts that explain why a run was corrected.

`04_exploration/02_build_visual_eda.py` adds governed housing-composition, cohort-comparison, and
temporal summaries. `04_exploration/03_render_eda_figures.py` consumes those contracts plus the
approved display geometry and writes a versioned twelve-figure set to the Unity Catalog
`eda_figures` volume. The gold figure manifest is the authoritative pointer to the current set.

`05_modeling/01_run_forecast_baselines.py` fits the fixed baseline ladder and one regularized
linear model from the published modeling panel. It writes validation-only predictions and sliced
scorecards and records the run in MLflow; it does not score the locked temporal tests.
[`05_modeling/06_local_forecast_demo.ipynb`](05_modeling/06_local_forecast_demo.ipynb) is the
meeting-ready local forecast demo. It downloads and caches a deterministic 500-tract subset of
`gold_modeling_panel` (one-year horizon, eligible training and validation rows), then demonstrates
the production feature registry, temporal split, local model fitting, score interpretation, and
subset-based diagnostics. It also reproduces published EDA figures 2, 3, 4, 5, 7, and 8 from
small aggregated Databricks EDA tables. Calibration and locked-test outcome rows are excluded.
Local scikit-learn results are illustrative and are not an exact reproduction of Spark ML or the
national validation scorecard. Outputs and downloaded subsets are ignored under
`reports/generated/`.
[`scripts/forecast_demo.py`](../scripts/forecast_demo.py) remains a separate synthetic-data CLI
demo.
`05_modeling/02_run_similarity_baselines.py` compares standardized raw and PCA current-state
matches for a small deterministic review set. That output is an inspection baseline, not yet the
time-safe historical analogue product used for final evaluation or serving.
`05_modeling/04_run_historical_analogue_baseline.py` retrieves earlier tract-year states for a
deterministic validation sample, requires each candidate's later outcome to be known by the query
year, and compares analogue-based estimates with forecast baselines on identical queries. The
first contract covers one- and three-year outcomes and does not open locked temporal tests.
`05_modeling/05_run_analogue_audit_stability.py` refuses to publish unless it reproduces those
baseline matches. It then creates deterministic review cases and measures top-ten stability under
small family-weight changes, family ablations, alternate PCA dimensions, and a distinct-tract
candidate policy. Exact and boundary-certified results remain visibly separate from bounded
shortlist stress tests.

Clear outputs before committing unless visible output is needed to review a result. Do not embed secrets, raw national data, or machine-specific absolute paths.

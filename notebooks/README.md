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

Clear outputs before committing unless visible output is needed to review a result. Do not embed secrets, raw national data, or machine-specific absolute paths.

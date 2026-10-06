# Notebooks

Notebooks are for exploration, diagnostics, and explanation. They are not the production pipeline.

Use numbered groups that mirror the implementation guide:

```text
notebooks/
├── 01_feasibility/
├── 02_data_quality/
├── 03_geography/
├── 04_exploration/
├── 05_modeling/
├── 06_representations/
├── 07_scenarios/
└── 08_final_analysis/
```

Each notebook should state its question, inputs, expected grain, data and code versions, and whether its output is exploratory or part of a final result. Reusable functions move to `src/neighborhood_twin/`; final figures are generated through repeatable code and written to `reports/generated/`.

Clear outputs before committing unless visible output is needed to review a result. Do not embed secrets, raw national data, or machine-specific absolute paths.

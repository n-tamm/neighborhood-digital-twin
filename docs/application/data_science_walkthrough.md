# Data Science Results

## Purpose

The application includes a dedicated Data Science Results tab so someone can understand the implemented
analysis without direct Databricks access. It is a project-level explanation rather than a
tract-specific dashboard. The page keeps three ideas separate:

1. which records are valid for longitudinal analysis;
2. how the two supervised forecast models compare with simple baselines; and
3. how historical communities are retrieved and evaluated.

The page does not train models, query evaluation tables, or recalculate metrics at runtime. It
renders reviewed copies of figures produced by the existing Databricks jobs. This makes the page
fast and prevents an application session from silently creating a different evaluation result.

## Page sequence

### Data foundation

The first section uses `01_tract_vintage_coverage.png` to explain why national source coverage is
not the same as model eligibility. The text distinguishes the 59,607-tract stable cohort used when
features cross the 2020 tract redesign from the broader current 2020-geography profile universe.
This section establishes the geographic limitation before any performance result is shown.

Source lineage:

- figure source: `06_tract_vintage_coverage.png`;
- accepted EDA build: `20261101T144931442020Z`;
- generating workflow: `400 Exploration | Visual EDA and Figures`.

### Forecasting

The forecasting section explains the cumulative FHFA single-family HPI target and compares the
project's regularized-linear and gradient-boosted-tree models at one and three years. A grouped
validation chart includes five simple baselines so readers can see whether model flexibility adds
value. State trend remains visible as a baseline; it is not treated as the three-year model.

The current bundled validation values come from governed job-500 scorecards. After the corrected
two-model jobs 504, 605, and 606 run, the page will also receive reviewed side-by-side figures for
later-period MAE, model-specific interval coverage, and error direction. The app does not
recalculate those metrics at runtime.

### Historical analogues

The similarity section first explains the method, then representation selection and stability,
then later-outcome utility and current coverage. Its four figures are:

- `05_similarity_workflow.png`;
- `06_similarity_stability_and_selection.png`;
- `07_analogue_outcome_utility.png`; and
- `08_current_analogue_coverage.png`.

The text states that weighted standardized distance retrieves ten distinct earlier tracts from a
time-safe candidate pool. Weighted matching is the application default because it was more
interpretable and had lower validation error than PCA. Bounded weight changes retained most
matches, while removal of a feature family is treated as a different model question. Analogue
outcomes beat zero change but not the strongest forecast comparator, so the product uses them as
historical evidence rather than its primary forecast. The approved serving release covers 46,719
of 85,528 current tracts at each supported horizon.

Source lineage:

- accepted figure build: `20261121T204510966976Z`;
- generating workflow: `800 Presentation | Similarity Communication Figures`;
- audit run: `d4957281b60a407a9dc0b1a84d7c9e57`;
- selection run: `9da77fab59bd41d8b8b602493131a890`;
- exact-tree run: `344fbe71819f4a779b36701a5fdaf7b8`;
- serving release: `analogue-20261121T163609734965Z`.

## Asset and refresh rule

The deployed copies and reviewed validation extract live in `app/assets/data_science/`. Figures
are not manually redrawn or edited.
When an accepted upstream figure build changes:

1. rerun and validate the appropriate Databricks figure workflow;
2. visually inspect the governed output;
3. replace only the corresponding application asset with the accepted file;
4. update the build and run IDs in this document and the on-page commentary if conclusions
   changed; and
5. rerun application tests and perform a live visual review.

Keeping explicit build IDs prevents the app from mixing a new written claim with an older image.

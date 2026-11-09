# Current-Neighborhood Historical Analogue Retrieval

## Purpose

The retrospective workflows asked whether historical matching was stable, interpretable, and
useful on earlier validation years. Job `503 Modeling | Current Analogue Retrieval` applies the
resulting policy to a neighborhood selected at the latest model-ready year. This is the first
workflow that answers the application's actual similarity question:

> Which communities in the past looked most like this neighborhood today, and what happened to
> them afterward?

The workflow does not replace the forecasting model. It produces historical evidence that can be
shown beside the primary forecast.

## Frozen retrieval contract

The branch carries forward the decisions supported by jobs 601 and 602:

- weighted standardized distance is the only application-facing representation;
- the five feature families retain equal total squared-distance weight;
- imputation and standardization are fitted only on point-model training rows;
- each result contains ten distinct physical candidate tracts;
- the selected tract cannot match itself; and
- candidate outcomes must have ended by the current query's as-of year.

PCA remains available in the historical evaluation tables for audit, but job 503 does not expose
it as a second user-facing list.

## Processing sequence

1. Read `gold_modeling_panel` and use its latest `forecast_origin_year` unless an earlier as-of
   year is explicitly requested.
2. Select explicit query GEOIDs or a deterministic small set from the configured demo states.
3. For each one- and three-year horizon, fit median imputation and standardization on eligible
   training rows only.
4. Transform the selected latest-year queries and the historical candidate states with that same
   fitted preprocessing.
5. Search the historical development-state candidates using exact weighted-standardized distance.
6. Exclude the query tract, any candidate whose outcome ended after the query year, and every row
   assigned to the locked temporal test.
7. Keep the closest state of each physical candidate tract, then retain the ten closest distinct
   tracts.
8. Summarize their later FHFA outcomes with a median, inverse-distance mean, and 10th-to-90th
   percentile range.

## Why locked temporal-test candidates are excluded

The current query year is later than the locked forecast tests. Without an explicit filter, a
current-neighborhood search could use those test outcomes as historical candidate evidence even
though the forecast model has not yet completed final evaluation. Job 503 excludes the
`locked_temporal_test` role entirely. This keeps application development from quietly opening the
test set through a different workflow.

Validation and calibration outcomes may appear as candidates because the analogue representation
has already been selected and those rows are not the untouched final test. The candidate's later
outcome must still have been observable by the query as-of year.

## Published outputs

| Schema | Table | Grain and use |
|---|---|---|
| `neighborhood_twin_model` | `current_analogue_match` | One current query, horizon, and historical match rank; retains location, year, distance, candidate outcome, safeguards, and lineage |
| `neighborhood_twin_model` | `current_analogue_summary` | One current query and horizon; provides outcome summaries, distance, age, and geographic diagnostics for later serving-table design |

The 10th-to-90th percentile range describes what happened among ten selected historical
communities. It is not a calibrated prediction interval and is explicitly labeled false in
`outcome_range_is_calibrated_interval`.

## Current coverage boundary

The first implementation queries `gold_modeling_panel`, so a tract needs a current model-ready
FHFA feature row. The broader current profile and job-501 ACS similarity cohort cover more tracts,
including places with limited FHFA history. Those tracts can still receive descriptive profiles,
but the frozen historical-analogue representation should not silently replace its missing market
trajectory family with a different method.

The application must therefore display an explained unavailable state when a selected tract lacks
a current model-ready analogue row. A later design decision could add a separately evaluated
ACS-only fallback, but it would be a new representation version rather than an invisible change to
this one.

## Scale and latency boundary

Job 503 uses exact search for a small configurable query set. This preserves the evaluated match
definition and provides a trustworthy reference result for application development. It does not
precompute every tract-to-history combination. Before interactive integration, the team should
measure on-demand latency and compare any approximate index with these exact top-ten lists. An
approximate method is acceptable only if its recall and rank behavior are documented and the user
still receives the frozen weighted match definition in practice.

## Validation gates

Publication stops if any query lacks ten distinct matches, a self-match appears, a candidate
outcome ends after the query year, a locked test row appears, or an unapproved representation is
published. The notebook also rereads both Delta tables and requires one MLflow run identifier per
table.

## Reproduction

After jobs 302 and 602 represent the intended data and selected analogue contract:

```powershell
databricks bundle validate --profile neighborhood-twin -t team
databricks bundle deploy --profile neighborhood-twin -t team
databricks bundle run current_analogue_retrieval --profile neighborhood-twin -t team
databricks bundle run table_metadata_pipeline --profile neighborhood-twin -t team
```

The default run selects one tract from each configured application-demo state. To retrieve named
tracts, override `query_geoids` with comma-separated eleven-character 2020 GEOIDs.

# `gold_model_split_assignment`

[Back to the data documentation index](README.md)

- **Layer:** Gold model readiness
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_model_split_assignment`
- **Sample:** [gold_model_split_assignment.jsonl](../../data/samples/gold_model_split_assignment.jsonl)
- **Grain and key:** one canonical 2020 tract GEOID, forecast-origin year, and forecast horizon.
- **Purpose:** freezes temporal roles, target eligibility, and geographic holdouts before model
  comparison so later experiments cannot quietly move the test set.
- **Main structure:** origin and target timing; observed or censored target status; stable versus
  post-2020 cohort; locked test, validation, and calibration years; temporal and geographic roles;
  model-fit and evaluation eligibility flags; holdout seed and method; build lineage.

The locked temporal-test origins are 2024 for the one-year horizon, 2022 for three years, and 2020
for five years. Current calibration origins are 2023, 2019, and 2015; validation origins are
2021-2022, 2017-2018, and 2014. Rows whose targets end after the locked test origin are marked
`purged_pretest`. Cross-2020 rows remain eligible only when their joined feature row belongs to the
stable longitudinal cohort.

One non-District-of-Columbia state per Census region is selected reproducibly with seed 699. The
current holdouts are Maine, North Dakota, West Virginia, and New Mexico, covering 1,106 tracts in
the model-ready panel. These states test transfer beyond the geographic development sample; they
do not replace the separate out-of-time test.

The November 19 table contains 2,090,658 rows across 63,367 tracts and three horizons. Validation
contains 101,703 one-year and 85,363 three-year rows. There are zero observed cross-2020 rows
outside the stable cohort. Five-year split rows remain available for feasibility and historical
reference, but the active forecast model does not train or score that horizon.

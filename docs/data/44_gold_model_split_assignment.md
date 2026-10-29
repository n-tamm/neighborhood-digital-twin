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
for five years. The immediately preceding independent origin is reserved for interval calibration;
validation uses 2021-2022, 2017-2018, and 2014 respectively. Rows whose targets end after the
locked test origin are explicitly marked `purged_pretest` instead of being allowed into model
development.

One non-District-of-Columbia state per Census region is selected reproducibly with seed 699. The
current holdouts are Maine, North Dakota, West Virginia, and New Mexico, covering 1,106 tracts in
the model-ready panel. These states test transfer beyond the geographic development sample; they
do not replace the separate out-of-time test.

The table contains 2,090,658 rows across 63,367 tracts and three horizons. All key, timing, role,
fit-eligibility, and regional-holdout checks passed. The five-year split has only three independent
training origins before validation and calibration, so five-year modeling is exploratory and
should use limited complexity and restrained claims.

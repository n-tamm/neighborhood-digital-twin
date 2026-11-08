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
for five years. Calibration and validation origin assignments must stay inside one calendar decade.
Their current origins are 2023 with validation 2021-2022 for one year, 2016 with validation
2014-2015 for three years, and 2014 with validation 2013 for five years. Any target crossing a
decade is marked `ineligible_target`; rows whose targets end after the locked test origin are
marked `purged_pretest`.

One non-District-of-Columbia state per Census region is selected reproducibly with seed 699. The
current holdouts are Maine, North Dakota, West Virginia, and New Mexico, covering 1,106 tracts in
the model-ready panel. These states test transfer beyond the geographic development sample; they
do not replace the separate out-of-time test.

The table contains 2,090,658 rows across 63,367 tracts and three horizons in the original build.
The decade-boundary rule changes the current split assignments and eligible target counts; rebuild
the product before using it. The five-year split has only two independent training origins before
validation and calibration, so five-year modeling is exploratory and should use limited complexity
and restrained claims.

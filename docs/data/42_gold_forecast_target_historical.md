# `gold_forecast_target_historical`

[Back to the data documentation index](README.md)

- **Layer:** Gold historical products
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_forecast_target_historical`
- **Sample:** [gold_forecast_target_historical.jsonl](../../data/samples/gold_forecast_target_historical.jsonl)
- **Grain and key:** one row per canonical 2020 tract GEOID, forecast-origin year, and configured
  horizon.
- **Purpose:** defines direct one-, three-, and five-year outcomes from the FHFA annual
  single-family HPI without mixing targets into the neighborhood-state table.
- **Main structure:** canonical geography; forecast origin, horizon, and target-end year; origin
  and endpoint HPI; cumulative log change; annualized percentage change; explicit observation or
  censoring status; source snapshots; and build lineage.

The cumulative target is `log(HPI[t+h] / HPI[t])`. The annualized percentage target is
`100 * (exp(cumulative_log_change / h) - 1)`. A target is observed only when both endpoints are
available and positive. Rows without a usable endpoint remain present with
`target_is_observed = false` and a `target_censor_reason`, which makes horizon-specific attrition
reproducible. The origin and endpoint must also fall in the same calendar decade; a window such as
2019-2022 is censored with `crosses_decade_boundary`, even when both HPI values are available.

FHFA describes a filtered single-family market. These targets do not represent multifamily
prices or every home in a tract. Their historical tract identity is aligned to the supported 2020
framework, including the reviewed Connecticut bridge.

The November 7, 2026 build contains 6,207,795 rows across 63,930 tracts and forecast origins from
1975 through 2025. Each horizon has 2,069,265 origin rows. Observed outcomes total 1,771,446
(85.6%) at one year, 1,272,945 (61.5%) at three years, and 819,969 (39.6%) at five years.
Decade-boundary censoring accounts for 200,983, 590,526, and 1,000,412 rows respectively. The
latest observed origins remain 2024, 2022, and 2020 for the one-, three-, and five-year horizons.
Quality checks confirmed zero observed decade-crossing targets.

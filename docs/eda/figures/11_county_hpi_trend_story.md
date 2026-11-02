# Figure 11: County HPI Trend Story

**File:** `11_county_hpi_trend_story.png`

## Question

Do strong cumulative county gains since 2020 imply equally strong current momentum?

## Construction

Display tract shapes are dissolved into county shapes. Each county map uses the median observed
tract HPI change from 2020 through 2025. A supporting scatterplot compares that median with the
county's median 2024-to-2025 tract change, and a side panel reports state summaries.

The county geometry is created only for display. The displayed statistic is a median of observed
tract changes, not an independently estimated county HPI.

## Interpretation

The paired map and scatterplot show why cumulative growth and current momentum must be separated.
A county can sit high on the five-year axis while being near or below zero in the latest year.
The scatterplot carries the analytical comparison; the map supplies geographic context.

## Limits

- Counties with insufficient observed endpoints remain missing.
- Every county receives one marker regardless of population, housing units, or land area.
- Median aggregation hides within-county variation.
- The pattern is descriptive and not an investment signal.

**Source contract:** [`gold_forecast_target_historical`](../../data/42_gold_forecast_target_historical.md)  
**Geometry method:** Shapely `union_all`, documented in the [EDA figure inventory](../../../reports/EDA_FIGURES.md)

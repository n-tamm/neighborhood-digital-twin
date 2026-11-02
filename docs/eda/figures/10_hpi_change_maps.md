# Figure 10: Tract HPI Change Maps

**File:** `10_hpi_change_2020_2025_maps.png`

## Question

How do cumulative tract HPI gains from 2020 through 2025 compare with the latest observed
one-year movement from 2024 through 2025?

## Construction

The figure uses observed targets with fixed endpoints for both periods. Each metric has one shared
scale across Arizona, Michigan, and Pennsylvania. The five-year map uses an ordered sequential
palette; the one-year map uses a zero-centered diverging palette. Color limits are based on the
5th and 95th percentiles, and missing observations are gray.

## Interpretation

The long view shows the accumulated post-2020 pattern. The latest-year view shows whether recent
movement continues, slows, or reverses that pattern. A tract can have a large cumulative gain and
weak recent movement; the two measures answer different questions.

## Limits

- Clipping improves readability but means the most extreme values share endpoint colors.
- The maps are descriptive and do not explain why HPI changed.
- FHFA is a single-family market measure, and missing coverage is not random across housing
  composition.
- Display geometry must not be reused for spatial model features.

**Source contracts:** [`gold_forecast_target_historical`](../../data/42_gold_forecast_target_historical.md),
[`gold_tract_profile_current`](../../data/17_gold_tract_profile_current.md)  
**Color-design reference:** [Matplotlib colormap guidance](https://matplotlib.org/stable/users/explain/colors/colormaps.html)

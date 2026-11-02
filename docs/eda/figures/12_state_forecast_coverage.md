# Figure 12: State Forecast Coverage by Census Region

**File:** `12_state_forecast_coverage.png`

## Question

How does the share of current forecast-candidate tracts vary among states and within each Census
region?

## Construction

For each state, the figure divides current forecast candidates by the relevant current tract
population. States are grouped into Northeast, Midwest, South, and West using the governed Census
geography hierarchy.

## Interpretation

The view confirms that the pipeline and candidate screening are national while showing that model
reach differs in every region. A later application should not imply uniform availability simply
because all states are present in the pipeline.

The regional grouping is organizational; it is not used to rank regions or infer expected market
performance.

## Limits

- The percentage describes availability and history depth, not prediction accuracy.
- States with the same percentage can have very different tract counts and housing composition.
- A current candidate may still be ineligible for a particular historical origin or horizon.

**Source contract:** [`gold_eda_state_coverage`](../../data/24_gold_eda_state_coverage.md)

**Geography contract:** [`silver_geography_state`](../../data/36_silver_geography_state.md)

# Figure 9: Current Forecast-Candidate Maps

**File:** `09_forecast_candidate_maps.png`

## Question

Where is current forecast eligibility available within Arizona, Michigan, and Pennsylvania, and
how should blank areas be interpreted?

## Construction

The figure joins the current tract profile's `forecast_candidate` flag to canonical 2020 display
geometry. It maps eligible and ineligible tracts in the three review states and pairs the maps with
coverage summaries so area is not used as a substitute for a tract count.

## Interpretation

Eligibility has geographic structure and is not uniformly distributed within a state. The figure
is useful for finding coverage gaps that an application will need to explain. It is not a map of
predicted appreciation or model accuracy.

Arizona, Michigan, and Pennsylvania were chosen as contrasting review examples. The underlying
profiles and candidate logic are national.

## Limits

- Eligibility is a current data-readiness flag, not a guarantee of a final released forecast.
- Large rural tracts occupy more map area but do not represent more observations.
- Geometry is simplified and approved for display only. It cannot support analytical distance or
  adjacency.

**Source contracts:** [`gold_tract_profile_current`](../../data/17_gold_tract_profile_current.md),
[`silver_canonical_tract_2020`](../../data/15_silver_canonical_tract_2020.md)  
**Rendering implementation:** [EDA workflow](../workflow.md)

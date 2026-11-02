# Figure 2: Housing Composition and FHFA Coverage

**File:** `02_housing_composition_coverage.png`

## Question

Does FHFA history and current forecast eligibility vary with the proportion of housing that is
single-family?

## Construction

Current-ACS tracts are grouped into ordered bands using the ACS share of attached and detached
single-family units. Within each band, the figure reports the percentage with any FHFA history and
the percentage passing the current forecast-candidate screen.

## Interpretation

Both measures rise as single-family housing becomes a larger share of the tract's housing stock.
This demonstrates why every forecast must be labeled as an FHFA single-family HPI result and why
coverage and error should be reported by housing composition.

The figure does not say that multifamily-heavy tracts lack useful neighborhood information. They
remain eligible for current profiles and ACS-based similarity when the relevant fields exist.

## Limits

- The grouping is descriptive and does not show that housing composition causes missing FHFA
  coverage.
- A covered tract can still have incomplete history for a particular horizon.
- Single-family share is an ACS estimate and carries sampling uncertainty.

**Source contract:** [`gold_eda_housing_coverage`](../../data/29_gold_eda_housing_coverage.md)  
**Related model slice:** [Forecast housing-composition evaluation](../../model_evaluation/figures/05_forecast_housing_composition.md)

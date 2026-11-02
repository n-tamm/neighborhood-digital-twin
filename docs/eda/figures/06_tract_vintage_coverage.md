# Figure 6: Stable Historical and Broader Post-2020 Coverage

**File:** `06_tract_vintage_coverage.png`

## Question

Which tract population can be compared across the 2020 Census boundary redesign, and when can the
broader current-vintage population be used?

## Construction

For each ACS release, the figure compares the source tract count with the tract count admitted by
the governed geography rule. It marks the 2020 redesign and provides two reference populations:
59,607 stable source tracts for cross-vintage work and roughly 84,400 supported tracts for broad
post-2020 work.

## Interpretation

The visible increase around 2020 is a geography and cohort change, not sudden neighborhood
creation or population growth. Work crossing the redesign must use the stable cohort. Work wholly
after the redesign can use broader coverage, but its results should be labeled separately.

## Limits

- Later model eligibility reduces the stable cohort further when usable FHFA origins and
  point-in-time ACS data are required.
- The conservative rule favors comparability over maximum row retention.
- Connecticut's later planning-region change is handled through a separate governed bridge.

**Source contract:** [`gold_historical_tract_coverage`](../../data/40_gold_historical_tract_coverage.md)  
**Detailed methodology:** [Tract Vintage Coverage](../../TRACT_VINTAGE_COVERAGE.md)

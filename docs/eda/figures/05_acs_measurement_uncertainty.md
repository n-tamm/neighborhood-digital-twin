# Figure 5: ACS Measurement Uncertainty

**File:** `05_acs_measurement_uncertainty.png`

## Question

Which ACS measures have the greatest sampling uncertainty relative to their estimated values?

## Construction

The figure selects the twelve measures with the highest 90th-percentile relative margin of error.
For each measure it shows the median and 90th percentile, where:

```text
relative margin of error = published 90% margin of error / absolute estimate
```

## Interpretation

Small housing categories can be noisy at tract scale. A high 90th percentile means a material
subset of tracts has uncertainty large relative to the estimate, even if the median is reasonable.
This supports retaining margins of error, avoiding overinterpretation of small differences, and
slicing forecast results by ACS uncertainty.

## Limits

- A near-zero estimate can create an extremely large relative ratio.
- A margin of error is sampling uncertainty, not a complete measure of data quality.
- The figure does not automatically disqualify a feature; it identifies where aggregation,
  sensitivity checks, or cautious explanation may be needed.

**Source contract:** [`gold_eda_acs_measure_quality`](../../data/25_gold_eda_acs_measure_quality.md)

**Related input contract:** [`silver_acs_tract_measure`](../../data/08_silver_acs_tract_measure.md)

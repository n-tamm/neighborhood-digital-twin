# Figure 3: Forecast Candidates Versus Excluded Tracts

**File:** `03_forecast_included_excluded_comparison.png`

## Question

Are current-ACS tracts that pass the forecast-candidate screen observably different from those
that do not?

## Construction

For each selected ACS feature, the figure calculates a standardized mean difference:

```text
mean among forecast candidates - mean among excluded current-ACS tracts
---------------------------------------------------------------
                     pooled standard deviation
```

Positive values mean the candidate group has a higher average. Negative values mean the excluded
group does. Reference lines at `-0.2` and `0.2` help identify differences worth investigating;
they are not formal significance thresholds.

## Interpretation

The model population is selected by data availability and therefore does not represent all
current tracts equally. This matters when describing model reach and when comparing application
users with and without available forecasts.

## Limits

- Standardization makes feature magnitudes comparable but does not explain why a difference
  exists.
- The comparison is not a causal estimate and is not a model-error result.
- Statistical significance is not the goal; the full national population is being profiled for
  practical selection differences.

**Source contract:** [`gold_eda_cohort_comparison`](../../data/30_gold_eda_cohort_comparison.md)

**Related context:** [Analytical data and cohorts](../../forecasting/target_and_split_design.md)

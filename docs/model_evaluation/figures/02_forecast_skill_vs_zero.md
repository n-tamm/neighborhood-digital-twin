# Figure 2: Forecast Skill Relative to Zero Change

**File:** `02_forecast_skill_vs_zero.png`

## Question

Does each method improve on the transparent assumption that HPI will not change?

## Construction

For each nonzero method and horizon, the figure calculates:

```text
MAE skill = 1 - method MAE / zero-change MAE
```

Positive values improve on zero change, zero ties it, and negative values are worse. The zero
reference is calculated on the same horizon, slice, and rows as the candidate.

## Interpretation

Skill makes baseline value explicit. A favorable raw error is not enough if a no-change rule does
equally well. The current one-year linear model improves MAE by about 39% relative to zero change.

## Limits

- Skill depends on the selected reference and does not define acceptable product error.
- Positive skill can coexist with bias, negative R-squared, or weak subgroup performance.
- The plotted results are validation-only.

**Source:** [`forecast_baseline_scorecard`](../../data/48_evaluation_forecast_baseline_scorecard.md)  
**Metric definition:** [Forecast evaluation](../../forecasting/evaluation_and_results.md)

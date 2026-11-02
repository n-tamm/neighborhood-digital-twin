# Figure 4: FHFA Annual HPI Behavior Over Time

**File:** `04_hpi_temporal_behavior.png`

## Question

How much do annual tract HPI changes vary across years and among the national and pilot-state
populations?

## Construction

For each observation year from 1990 onward, the figure shows the median annual FHFA tract HPI
change and the 10th-to-90th percentile range for the United States, Arizona, Michigan, and
Pennsylvania.

## Interpretation

Housing-price changes vary substantially by time and place. This supports time-based model splits
and the inclusion of transparent county and state trend baselines. It also warns against treating
millions of tract rows as millions of independent time observations.

The shaded band describes dispersion across the tracts available in that year. It is not a model
uncertainty interval.

## Limits

- Historical FHFA coverage changes over time; the percentile band does not reweight years to a
  fixed tract population.
- The three states are visual examples rather than the full national analysis.
- Observed association with time or state does not explain the cause of HPI changes.

**Source contract:** [`gold_eda_hpi_temporal`](../../data/31_gold_eda_hpi_temporal.md)

**Related design:** [Forecast target and split design](../../forecasting/target_and_split_design.md)

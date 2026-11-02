# Figure 7: Model-Feature Completeness

**File:** `07_model_feature_completeness.png`

## Question

Which approved point-in-time model inputs have the most missing observations before model
preprocessing?

## Construction

The figure reads the `feature_missingness` section of `gold_model_readiness_summary`, selects the
fifteen lowest non-null rates, and displays them against a 95% completeness reference line.

## Interpretation

Even the least-complete approved features are broadly available. The remaining missingness is
large enough to require an explicit preprocessing rule but not large enough to justify discarding
all incomplete rows. The implemented linear pipeline therefore learns median replacements from
training rows instead of using complete-case filtering.

Median gross rent is the least complete selected ACS field at about 97.2%. Exact HPI lag coverage
also falls as the requested history length grows, which contributes to horizon-specific
eligibility.

## Limits

- A high non-null rate does not establish that a feature is accurate or useful.
- This is measured before training-fitted imputation.
- Missingness may vary by year, geography, housing composition, or cohort even when the national
  rate is high.

**Source contract:** [`gold_model_readiness_summary`](../../data/46_gold_model_readiness_summary.md)  
**Related implementation:** [Forecasting module](../../forecasting/forecasting_module.md)

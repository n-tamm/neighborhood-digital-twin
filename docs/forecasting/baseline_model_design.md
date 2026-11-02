# Baseline Model Design

## Purpose of the baseline ladder

The first forecast workflow is designed to establish honest difficulty, not to search many
algorithms. Every method predicts the same cumulative log-change target on the same validation
population. A fitted model only earns further development if it improves on transparent rules in
a consistent and interpretable way.

## Fixed prediction rules

### Zero change

`zero_change` predicts no future HPI movement. It anchors the skill calculation and reveals how
much error exists even before a trend assumption is introduced.

### Latest-change persistence

`latest_change_persistence` assumes the tract's latest one-year percentage change continues at
the same annual rate for the full horizon. It tests short-term momentum but can amplify an unusual
single year.

### Recent three-year mean

`recent_three_year_mean` continues the tract's average recent three-year annual change. It is a
smoother tract-history baseline and reduces dependence on one unusually strong or weak year.

### County current trend

`county_current_trend` continues the county's mean annual change observed at the forecast origin.
It tests whether local market context is more reliable than the tract's own recent movement.

### State current trend

`state_current_trend` continues the state mean annual change at the origin. It is broader than the
county rule and is the strongest simple multi-horizon comparator in the first validation run.

The fixed annual rates are converted to cumulative log change for the requested horizon so all
methods are scored on the same target scale.

## Regularized linear model

`regularized_linear` combines 26 point-in-time inputs after training-fitted median imputation and
standardization. A separate direct model is fit for each horizon. It uses L2 regularization with
`regParam = 0.05`, `elasticNetParam = 0.0`, and at most 100 iterations.

L2 regularization shrinks coefficients when features overlap, which is useful for correlated
housing, tenure, and affordability measures. It does not make the relationship nonlinear, select
causal variables, or eliminate the need for error slices.

### Feature families

| Family | Implemented inputs |
|---|---|
| HPI history | Origin change; 1-, 3-, and 5-year changes; 3-year mean; 5-year volatility; observation and gap counts |
| Regional context | County and state origin-year mean change |
| Community scale | Population and housing units |
| Occupancy and tenure | Occupancy, vacancy, owner-occupancy, and renter-occupancy rates |
| Housing structure | Single-family, multifamily, and mobile-home shares |
| Affordability | Household income, owner-occupied value, and gross rent |
| Data timing and quality | ACS age and relative margins of error for income, value, and rent |

## Design boundaries

- No nonlinear candidate is implemented yet.
- No feature-family ablation has been run.
- No tract adjacency or distance feature is present because current geometry is display-only.
- The linear model produces point predictions only; uncertainty is not calibrated.
- Coefficients should not be described as causal effects.

# Historical Analogue Design

## Goal

The historical analogue system answers:

> Which earlier tract-year states looked most like a selected neighborhood at its query year, and
> what happened to their FHFA single-family HPI afterward?

The output supports two related application views. First, users can inspect the matched
communities, years, shared characteristics, differences, and later trajectories. Second, the
later outcomes can be summarized as an analogue-based estimate and compared with the supervised
forecast. Similarity remains supporting historical evidence; it is not a causal claim that the
selected neighborhood will follow the same path.

## Implemented development population

The first historical workflow uses one- and three-year validation query rows from
`gold_modeling_panel`. It samples
queries deterministically within forecast origin, horizon, Census region, and geographic role so
the review set covers multiple periods and both development and held-out states without creating
an impractical all-query cross join.

Candidate analogues must:

- have the same forecast horizon as the query;
- have an observed later outcome;
- come from a geographic-development state;
- be a different tract from the query; and
- have a target end year no later than the query's forecast-origin year.

The last rule is the central time-safety constraint:

```text
candidate origin + horizon <= query origin
```

It ensures that both the candidate's state and its later outcome would already have been known at
the query date. A three-year analogue from 2018 can be used for a 2021 query because its outcome
ends in 2021; a 2020 analogue cannot because its three-year outcome would still be in the future.

## Historical feature representation

The first representation uses five feature families. Features are transformed and standardized
with parameters fitted only on governed point-model training rows for the applicable horizon.

| Family | Features | Historical treatment |
|---|---|---|
| Community scale | log population; log housing units | `log1p` reduces skew while retaining actual tract scale |
| Occupancy and tenure | occupancy rate; owner-occupancy rate | vacancy and renter shares are omitted because they are mathematical complements |
| Housing structure | single-family, multifamily, and mobile-home shares | family weighting prevents three columns from overwhelming smaller families |
| Affordability | owner value divided by household income; annual rent divided by household income | dimensionless ratios replace nominal dollars that are not comparable across years |
| Market trajectory | recent three-year HPI change; recent five-year HPI volatility; tract change minus state trend | captures direction, instability, and relative market movement using only origin-time history |

Median imputation and standardization are learned from training rows. Each family receives equal
total squared-distance weight; that weight is divided equally among the columns in the family.
The workflow compares exact Euclidean neighbors in the weighted standardized space with neighbors
in a six-component PCA representation of the same weighted vector.

The ratios solve the immediate nominal-dollar problem without adding a macroeconomic source. They
do not fully measure affordability burden because ACS income, rent, and value describe different
populations and five-year periods. Their use must remain explicit in match explanations.

## Query and candidate geography

Pre-2021 feature rows are limited to the conservative stable tract cohort. Later queries may come
from the broader post-2020 cohort, but their earlier candidate universe is necessarily smaller.
The output carries both query and candidate cohort labels so this coverage difference remains
visible.

The same tract is excluded to prevent its own earlier history from becoming a trivial match. The
same county is allowed and recorded as a diagnostic. Display geometry is not used in retrieval.

## Analogue outcome estimates

Each query and representation produces two development estimates from the top matches:

1. `analogue_median` uses the median later cumulative log HPI change.
2. `analogue_inverse_distance` uses a normalized inverse-distance weighted mean.

The match outcome's 10th and 90th percentiles are retained as descriptive historical spread, not
as a calibrated prediction interval. Both estimates are compared on the same sampled query rows
with zero change, state trend, and the current regularized linear forecast.

No analogue estimate is blended with the supervised forecast in this stage. A later ensemble
would require a validation improvement and a frozen combination rule before locked-test use.

## Evaluation

The development scorecard reports MAE, RMSE, median and 90th-percentile absolute error, signed
bias, R-squared, directional lift over the majority direction, query coverage, and match counts.
It is sliced by horizon, query origin, geographic transfer role, Census region, and modeling
cohort.

Retrieval diagnostics include distance spread, same-county and cross-state shares, candidate age,
PCA explained variance, and raw/PCA top-k overlap. These describe representation behavior but do
not replace later-outcome evaluation.

## Current boundaries

- The first run uses a deterministic validation sample rather than every tract-year query.
- The workflow evaluates one- and three-year outcomes. A leakage-safe five-year analogue backtest
  is not available under the current split: its validation query origin is 2014, model-ready
  historical features begin in 2011, and an outcome known by 2014 would require a candidate origin
  no later than 2009. The workflow fails clearly if a requested horizon has no eligible analogue
  history rather than relaxing the time rule.
- The feature set remains housing-focused and does not yet include education, employment,
  household composition, commuting, amenities, or environmental context.
- Historical outcome spread is not a calibrated uncertainty interval.
- Locked temporal test rows remain unopened.
- Current application-serving matches are not published until this retrospective design passes
  review.

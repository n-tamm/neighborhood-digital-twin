# Forecast Target and Split Design

## Target

The implemented target is cumulative log change in FHFA tract HPI from forecast origin `t` to the
end of horizon `h`:

```text
target(t, h) = log(HPI(t + h) / HPI(t))
```

In plain language, the model predicts how much the tract's measured single-family HPI changes over
the next one, three, or five years. It does not predict an individual home price or the value of
all housing in the tract.

The origin and target endpoint must be in the same calendar decade (for example, both in
2010-2019 or both in 2020-2029). Targets that cross a decade boundary are censored and cannot be
used for fitting or evaluation. Thus, a 2019-to-2022 three-year target is excluded, even when both
HPI observations exist.

Log change is used because multi-year changes combine consistently and because prediction errors
have a clear signed interpretation. For display, predictions are converted to annualized percent
change:

```text
(exp(predicted log change / horizon) - 1) * 100
```

## Modeling grain

[`gold_modeling_panel`](../data/45_gold_modeling_panel.md) has one row per tract, forecast-origin
year, and horizon. It joins point-in-time features, direct outcomes, and the assignment contract
without fitting preprocessing. It contains 2,090,658 rows across 63,367 tracts.

Observed target counts decline with horizon because a longer future endpoint is not available for
every origin:

| Horizon | Observed targets | Locked-test rows |
|---|---:|---:|
| 1 year | 571,237 | 42,082 |
| 3 years | 380,562 | 45,887 |
| 5 years | 203,694 | 34,644 |

## Point-in-time feature rule

For origin `t`, features use HPI observations ending at `t`, county and state context available at
`t`, and the most recent ACS release whose release year is no later than `t`. A newer ACS release
is not used merely because it is available today. `acs_measurement_age_years` records how old the
selected release is at the origin.

## Geography cohorts

- The **stable longitudinal cohort** is used when history crosses the 2020 tract redesign.
- The **broad post-2020 cohort** is used for later origins that do not require comparable older
  geography.

The two cohorts are evaluated separately. Otherwise a change in tract population could be
mistaken for a change in forecast performance. See
[Tract Vintage Coverage](../TRACT_VINTAGE_COVERAGE.md) for the 59,607-tract geography rule and
Connecticut handling.

## Frozen temporal roles

Random tract-row splitting is prohibited because the same tract appears repeatedly, nearby tracts
share conditions, and adjacent ACS releases overlap. Assignments are frozen in
[`gold_model_split_assignment`](../data/44_gold_model_split_assignment.md).

| Horizon | Training origins | Validation origins | Calibration | Locked test |
|---|---:|---|---:|---:|
| 1 year | 9 | 2021-2022 | 2023 | 2024 |
| 3 years | 3 | 2014-2015 | 2016 | 2022 |
| 5 years | 2 | 2013 | 2014 | 2020 |

Labels that would end after the applicable locked-test origin are purged from development. The
one-year horizon is primary, three years is secondary, and five years is exploratory because only
two independent training origins support it. Calibration and validation origins are selected
backward from the locked-test origin, skipping any origin whose horizon crosses a calendar-decade
boundary.

## Geographic transfer role

Maine, North Dakota, West Virginia, and New Mexico are deterministic held-out states, one per
Census region. Training eligibility excludes their rows. Validation outputs retain them as a
geographic transfer slice so the same time periods can be compared inside and outside development
states.

This does not replace the locked temporal test. The four states are relatively small and cannot
represent every transfer setting.

## Leakage controls

- Split assignments exist before preprocessing or model fitting.
- Imputation and scaling are fit only on `eligible_for_point_model_fit` rows.
- Validation predictions contain only the validation temporal role.
- Calibration and locked-test predictions are not published by the baseline workflow.
- County and state trend features are calculated at the origin, not from future outcomes.
- Display geometry is not used as analytical spatial data.

Changing the target, cohort, or split policy should create a new contract version rather than
silently replacing the meaning of an existing result.

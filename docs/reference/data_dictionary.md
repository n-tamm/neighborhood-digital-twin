# Data Dictionary

This is the authoritative human-readable index of fields used in curated tables, models, and the application. Update it when a field is introduced or its meaning changes; do not wait until the final report.

## Dataset registry

| Dataset | Grain | Primary key | Time coverage | Geography vintage | Status | Contract |
|---|---|---|---|---|---|---|
| Neighborhood state | Tract-year | `tract_geoid`, `year` | TBD | TBD | Planned | [Neighborhood state contract](../contracts/neighborhood_state.md) |
| Serving bundle | Release | `bundle_version` | TBD | TBD | Planned | [Serving bundle contract](../contracts/serving_bundle.md) |

Add source-specific and model-output tables when their contracts are approved.

## Field definition template

| Field | Table | Type | Unit | Definition | Source or derivation | Available as of | Null allowed | Quality rule | Sensitive or restricted |
|---|---|---|---|---|---|---|---|---|---|
| `tract_geoid` | Neighborhood state | string | — | Census tract identifier for the contract's geography vintage | Census geography | Observation year | No | Fixed-width, valid in geography crosswalk | No |
| `year` | Neighborhood state | integer | calendar year | State observation year | Derived during temporal alignment | End of year, subject to source lag | No | Within declared coverage | No |

## Definition rules

- Use one row per field and name the exact table in which it appears.
- State whether dollars are nominal or inflation-adjusted and identify the base year.
- For rates, identify the numerator, denominator, scale, and population universe.
- For estimates, record the associated margin-of-error field where available.
- Distinguish observation year from publication or availability date.
- Document imputation, winsorization, transformations, and category mappings.
- Do not describe a modeled or imputed value as observed.

## Change control

A breaking definition change requires a schema version change, migration note, and impact review for downstream features, models, and application views. Renaming a field without changing meaning may be backward-compatible only when the old name is supported or the change is contained within one unreleased branch.


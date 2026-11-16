# Similarity Representation Design

## Current objective

The current baseline asks whether a small set of interpretable housing and economic features can
retrieve plausible communities from a national candidate pool, and how much the retrieved list
changes after PCA compression.

It does not ask whether the matches predict what happens next. Similarity is descriptive: two
tracts can look alike on the selected dimensions and still follow different paths.

## Candidate population

[`gold_similarity_candidate_current`](../data/18_gold_similarity_candidate_current.md) contains
current tracts with positive population and housing-unit counts and the twelve required features.
FHFA history is not required. This preserves ACS-based matching for multifamily-heavy communities
and other tracts where the single-family HPI is unavailable or less representative.

## Feature registry

| Dimension | Features |
|---|---|
| Scale | Population and housing units |
| Occupancy and tenure | Occupancy, vacancy, owner-occupancy, and renter-occupancy rates |
| Housing structure | Single-family, multifamily, and mobile-home shares |
| Affordability and value | Household income, owner-occupied value, and gross rent |

This is intentionally housing-focused. It does not yet represent education, employment,
commuting, amenities, health, environment, development activity, or subjective lived experience.

## Transformations

Population, housing units, income, owner value, and rent receive a `log1p` transform. This reduces
the influence of large right-skewed values while preserving zero. All twelve fields are then
median-imputed and standardized to zero-centered, unit-variance scales.

Imputation and standardization are fit to the current candidate population. That is acceptable
for the current-state inspection baseline but is not the correct design for historical evaluation,
where transforms must be learned from an earlier development period and reused unchanged.

## Compared representations

### Standardized raw

Exact Euclidean distance is calculated in the twelve standardized feature dimensions. This space
is easier to explain because every dimension corresponds to an approved source feature.

### Six-component PCA

Principal component analysis compresses the standardized vector to six weighted combinations that
retain as much total variance as possible. PCA can reduce redundancy but makes individual
dimensions less interpretable. Explained variance is a compression diagnostic, not proof of match
quality.

Distances are comparable only within the same representation. Raw and PCA distances have
different dimensions and scales.

## Retrieval rule

For each query, the workflow calculates exact distance to every candidate, removes the query
tract itself, orders by distance with GEOID as the tie-breaker, and returns ten matches. Exact
search is transparent and feasible for six queries but is not intended as a final national app
serving strategy.

## Current design boundaries

- Feature families have equal per-column influence after standardization; no explicit family
  weighting is implemented.
- The same county and nearby tracts are allowed; only self-match is excluded.
- No geographic distance is used.
- No future outcome is used to select a match.
- No similarity explanation yet identifies the strongest shared traits and differences.

## Historical analogue application choice

The current-state job-501 comparison above remains an exploratory baseline. For retrospective
historical analogues, jobs 502 and 601 use five explicit feature families with equal total family
weight and include recent housing-market trajectory. The stability audit and expanded job-602
evaluation support weighted standardized distance as the application representation:

- small family-weight changes retain 93.4% of the top ten on average and are
  exactness-certified;
- five- and seven-component PCA lists retain 50.9% of the six-component list on average and can
  hide a large gap in an original feature family;
- expanded outcome accuracy favors weighted analogues overall at both horizons, although subgroup
  comparisons remain mixed; and
- direct weighted features support the shared-strength and important-difference explanations the
  application needs.

The application should also keep one historical state per physical candidate tract. This rule
produces ten distinct communities while retaining 93.1% of baseline matches on average. Job 602
then validated both choices on 88 one-year and 90 three-year queries with complete required
housing, size, and uncertainty category coverage. PCA and the tract-year baseline remain available
for model audit rather than becoming user-facing defaults.

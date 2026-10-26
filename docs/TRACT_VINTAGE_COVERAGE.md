# Tract Vintage Coverage

## Why this matters

The project has complete annual ACS source coverage from 2010 through 2024, but that does not
mean every tract can be followed across the entire period. ACS releases from 2010 through 2019
use 2010 Census tract geography. Releases from 2020 onward use 2020 tract geography, with an
additional reviewed bridge for Connecticut's later switch to planning-region identifiers. FHFA
history is represented on the current tract framework. A historical join therefore needs an
explicit geography rule; matching tract identifiers without one can attach observations to
boundaries that changed.

## Measured coverage change

The official Census 2010-to-2020 relationship file contains the following project-scope universe
for the 50 states and Washington, D.C.:

| Measure | Tracts |
|---|---:|
| Distinct 2010 tracts | 73,057 |
| Distinct 2020 tracts | 84,414 |
| Net increase | 11,357 |
| 2010 tracts overlapping multiple 2020 tracts | 31,865 |
| 2020 tracts receiving land from multiple 2010 tracts | 27,841 |
| 2010 tracts with a same-GEOID relationship edge | 61,619 |
| 2010 tracts passing the conservative stable rule | 59,607 |
| 2010 tracts requiring harmonization or exclusion | 13,450 |

The pipeline calculates these values at the tract grain. It does not count relationship rows as
tracts because one changed tract can create several source-to-target edges.

## The stable-tract rule

A 2010 tract is considered stable for the first historical modeling baseline only when:

1. the 2010 and 2020 GEOIDs are identical;
2. the selected relationship is the dominant edge for the 2010 tract;
3. at least 95% of the 2010 tract's land lies in the matched 2020 tract; and
4. at least 95% of the 2020 tract's land came from the matched 2010 tract.

This rule retains 59,607 of the 73,057 source tracts, or 81.6%. It is deliberately conservative.
It says the tract boundary is sufficiently comparable for an initial baseline; it does not say
the residents, housing stock, or economic conditions were unchanged.

## Coverage by time span

| ACS releases | Analytical geography treatment | Resulting coverage |
|---|---|---|
| 2010-2019 | Keep only tracts passing the stable 2010-to-2020 rule | Stable subset, not all 2020 tracts |
| 2020-2021 | Join directly to the canonical 2020 tract dimension | Broad 2020-geography coverage |
| 2022-2024 Connecticut | Apply the audited current-to-2020 Connecticut bridge | Land tracts are retained; water-only exceptions stay explicit |
| 2022-2024 outside Connecticut | Join directly to the canonical 2020 tract dimension | Broad 2020-geography coverage |

As a result, historical charts, modeling tables, evaluation samples, and analogue searches that
cross the 2019-to-2020 boundary must report which geography policy they use. A row count from the
later period must not be presented as if the same full tract universe existed in earlier years.

## Why the first model uses the stable subset

The Census relationship file contains land and water overlap, but not population or housing-unit
weights. Land share is not a defensible general-purpose weight for moving people, homes, incomes,
rents, values, rates, medians, or indexes between tract vintages. Using it indiscriminately would
create precise-looking values with unclear meaning.

The first forecasting and retrospective-analogue baselines will therefore use the stable subset
for observations that depend on pre-2020 ACS data. This gives the project a reproducible national
historical cohort without manufacturing crosswalked values. Evaluation must still compare the
stable subset with the excluded tracts on observable geography and housing characteristics so the
team can describe where results generalize.

## Possible later expansion

Broader harmonization is an extension, not a prerequisite for the first baseline. It would need a
field-family policy:

- additive counts may be allocated only with a defensible population or housing-unit weight and
  must pass conservation checks;
- medians, rates, ratios, and indexes generally require reconstruction from valid components or
  should remain unavailable;
- every transformed value must retain its source and target vintages, method, weight source, and
  confidence or coverage information; and
- model results should be compared with the stable-only cohort to show whether the crosswalk
  changes conclusions.

## Where the rule is enforced

- `silver_tract_relationship_2010_2020.is_stable_measure_mapping` implements the boundary screen.
- `geography_quality_metrics` records tract-level coverage under the
  `tract_change_2010_2020` metric group.
- Historical gold products must retain the source GEOID, canonical 2020 GEOID, source geography
  vintage, alignment method, and eligibility reason.
- Application and report language must distinguish full current coverage from the smaller
  longitudinally comparable cohort.

The official source and its limitation are documented by the
[U.S. Census Bureau relationship files](https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.2020.html).


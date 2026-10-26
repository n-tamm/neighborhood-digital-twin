# Data Guide

This folder explains the tables that currently exist across the shared Databricks bronze, silver,
gold, and quality schemas. It is the
starting point for understanding what a row represents, which table should be used for a given
task, and where important limitations enter the pipeline.

The pipeline deliberately keeps four different concerns separate:

```text
public source files and APIs
          |
          v
source snapshots and bronze tables     source-shaped, reproducible records
          |
          v
silver tables                           typed, validated, analysis-ready source products
          |
          v
gold tables                             joined profiles and explicit candidate cohorts
          |
          +---------------------> modeling, evaluation, and the interactive application
```

Each implemented table has its own document below. Small, real extracts live in the repository's
main [data samples folder](../../data/samples/) so a teammate can inspect table shape without
opening Databricks. The samples are documentation aids, not substitutes for the governed tables.

## Table documents

### Governance and bronze

1. [`source_snapshot_manifest`](01_source_snapshot_manifest.md)
2. [`bronze_fhfa_tract_hpi`](02_bronze_fhfa_tract_hpi.md)
3. [`bronze_acs5_tract`](03_bronze_acs5_tract.md)
4. [`bronze_census_tract_relationship_2010_2020`](04_bronze_census_tract_relationship_2010_2020.md)
5. [`bronze_census_tract_display_geometry_2020`](05_bronze_census_tract_display_geometry_2020.md)
6. [`bronze_census_connecticut_tract_reference`](22_bronze_census_connecticut_tract_reference.md)
7. [`bronze_quality_metrics`](06_bronze_quality_metrics.md)

### Silver analytical source tables

8. [`silver_fhfa_tract_year`](07_silver_fhfa_tract_year.md)
9. [`silver_acs_tract_measure`](08_silver_acs_tract_measure.md)
10. [`silver_acs_measure_dictionary`](09_silver_acs_measure_dictionary.md)
11. [`silver_acs_tract_year`](10_silver_acs_tract_year.md)
12. [`silver_quality_metrics`](11_silver_quality_metrics.md)
13. [`silver_tract_relationship_2010_2020`](12_silver_tract_relationship_2010_2020.md)
14. [`silver_tract_display_geometry_2020`](13_silver_tract_display_geometry_2020.md)
15. [`silver_connecticut_tract_bridge_2020_2024`](23_silver_connecticut_tract_bridge_2020_2024.md)
16. [`geography_quality_metrics`](14_geography_quality_metrics.md)
17. [`silver_canonical_tract_2020`](15_silver_canonical_tract_2020.md)
18. [`canonical_geography_quality_metrics`](16_canonical_geography_quality_metrics.md)

### Silver geography dimensions

19. [`silver_geography_country`](33_silver_geography_country.md)
20. [`silver_geography_region`](34_silver_geography_region.md)
21. [`silver_geography_division`](35_silver_geography_division.md)
22. [`silver_geography_state`](36_silver_geography_state.md)
23. [`silver_geography_county`](37_silver_geography_county.md)
24. [`silver_geography_tract_2020`](38_silver_geography_tract_2020.md)
25. [`geography_hierarchy_quality_metrics`](39_geography_hierarchy_quality_metrics.md)

### Gold current products

26. [`gold_tract_profile_current`](17_gold_tract_profile_current.md)
27. [`gold_similarity_candidate_current`](18_gold_similarity_candidate_current.md)
28. [`gold_forecast_candidate_current`](19_gold_forecast_candidate_current.md)
29. [`gold_application_demo_tract`](20_gold_application_demo_tract.md)
30. [`gold_quality_metrics`](21_gold_quality_metrics.md)

### Gold exploration and readiness

31. [`gold_eda_state_coverage`](24_gold_eda_state_coverage.md)
32. [`gold_eda_acs_measure_quality`](25_gold_eda_acs_measure_quality.md)
33. [`gold_eda_fhfa_history`](26_gold_eda_fhfa_history.md)
34. [`gold_eda_horizon_feasibility`](27_gold_eda_horizon_feasibility.md)
35. [`eda_readiness_quality_metrics`](28_eda_readiness_quality_metrics.md)
36. [`gold_eda_housing_coverage`](29_gold_eda_housing_coverage.md)
37. [`gold_eda_cohort_comparison`](30_gold_eda_cohort_comparison.md)
38. [`gold_eda_hpi_temporal`](31_gold_eda_hpi_temporal.md)
39. [`gold_eda_figure_manifest`](32_gold_eda_figure_manifest.md)

## Working conventions

- Census tract identifiers are strings so leading zeros are never lost.
- `bronze` keeps source values and snapshot lineage as close to the publisher's response as
  practical.
- `silver` is the default layer for exploration and source-specific modeling work.
- `gold_tract_profile_current` is the default current-state table for application and modeling
  prototypes. Its filtered companion tables are convenience cohorts, not new definitions of the
  project's geographic scope.
- ACS estimates remain paired with their published 90 percent margins of error. A missing value is
  not treated as zero.
- Complete source coverage does not imply complete longitudinal tract coverage. Historical work
  spanning the 2010 and 2020 tract vintages follows the documented
  [tract vintage coverage contract](../TRACT_VINTAGE_COVERAGE.md): pre-2020 ACS observations use
  the stable subset, while current-state products retain broad 2020-geography coverage.
- Simplified cartographic geometry is for display. It is not approved for adjacency, distance,
  intersection, or other analytical spatial operations.
- Table descriptions and column comments are managed in code and applied after any table rebuild
  that overwrites a schema.

## Current coverage

As of October 25, 2026, the organized schemas contain complete annual 2010-2024 ACS coverage for
the 50 states and District of Columbia, national FHFA tract HPI history through 2025, and national
Census geography support. The validated ACS contract contains all 765 required state-release
pairs, 1,152,605 selected silver tract-release rows, and 24,204,705 normalized measure rows.
Puerto Rico and the other island areas are present in parts of the geography source but are not
part of the supported ACS or country-to-tract hierarchy.

Bronze retains 1,160,833 rows across 768 immutable snapshots. The difference from silver is one
earlier 2024 snapshot for each pilot state, totaling 8,228 historical snapshot rows; silver
selects one validated snapshot per state and release. The latest national validation reports zero
missing or unexpected state-release pairs, zero missing validated sources, and no hard bronze,
silver, or gold failures. Documented warnings are limited to unavailable ACS median-dollar values
and five current Connecticut water-only tracts.

The governed hierarchy now contains one country, four Census regions, nine Census divisions, 51
states or state equivalents, 3,143 counties or county equivalents, and 84,414 canonical 2020
tracts. It intentionally covers the 50 states and District of Columbia. It does not force
territories, metro areas, or ZIP/ZCTA relationships into the country-to-tract hierarchy.

Connecticut requires a geography bridge because the 2022 ACS replaced its former counties with
[planning regions](https://www.census.gov/programs-surveys/acs/technical-documentation/user-notes/2023-01.html).
The implemented bridge maps all 879 land tracts one-to-one between the 2020 and 2024 TIGER
vintages. Current ACS profiles now populate those canonical tracts. Five current water-only tracts
remain deliberately unmatched; this leaves zero unexpected current ACS mismatches. FHFA also
uses the newer planning-region identifiers for 728 Connecticut tracts. Applying the same audited
bridge restores FHFA history for all 728 and produces 662 current forecast candidates.

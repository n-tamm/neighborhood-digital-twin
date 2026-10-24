# Data Guide

This folder explains the tables that currently exist in the shared Databricks schema. It is the
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

Use [TABLE_CATALOG.md](TABLE_CATALOG.md) for table-by-table grain, keys, purpose, and cautions.
The [samples](samples/) folder contains small, real extracts from the development tables so a
teammate can inspect their shape without opening Databricks. These samples are documentation,
not substitutes for the governed tables.

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
- Simplified cartographic geometry is for display. It is not approved for adjacency, distance,
  intersection, or other analytical spatial operations.
- Table descriptions and column comments are managed in code and applied after any table rebuild
  that overwrites a schema.

## Current coverage

As of October 24, 2026, the development schema contains nationwide 2024 ACS coverage for the 50
states and District of Columbia, annual 2010–2024 ACS coverage for Arizona, Michigan, and
Pennsylvania, national FHFA tract HPI history through 2025, and national Census geography support.
Puerto Rico and the other island areas are present in parts of the geography source but were not
included in the current ACS acquisition.

Connecticut requires special handling. Beginning with the 2022 ACS, its former counties were
[replaced by planning regions](https://www.census.gov/programs-surveys/acs/technical-documentation/user-notes/2023-01.html),
which changed tract GEOIDs even though almost all tract shapes stayed the same. The current gold
join therefore leaves Connecticut ACS fields unavailable until an explicit, validated
2020-to-current Connecticut bridge is added. The records remain visible in the complete tract
profile rather than being silently dropped.

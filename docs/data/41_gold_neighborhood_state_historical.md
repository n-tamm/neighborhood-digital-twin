# `gold_neighborhood_state_historical`

[Back to the data documentation index](README.md)

- **Layer:** Gold historical products
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_neighborhood_state_historical`
- **Sample:** [gold_neighborhood_state_historical.jsonl](../../data/samples/gold_neighborhood_state_historical.jsonl)
- **Grain and key:** one row per canonical 2020 tract GEOID and ACS release year.
- **Purpose:** provides the governed longitudinal neighborhood-state panel used to construct
  point-in-time features and retrospective analogue queries.
- **Main structure:** canonical and source tract identifiers; full Census hierarchy; ACS survey,
  release, and conservative availability years; source geography vintage and alignment method;
  the compact governed ACS profile; source lineage; and historical build lineage.

The table deliberately has different tract coverage before and after the 2020 geography change.
Rows from 2010-2019 exist only when the source tract passes the stable relationship rule. Later
releases retain broad supported 2020-geography coverage, including Connecticut land tracts that
use the reviewed identity bridge. Excluded source tracts are counted in
`gold_historical_tract_coverage`; they are not silently imputed here.

`acs_available_year` equals `acs_release_year + 1`. This is a conservative annual availability
rule based on ACS five-year products generally being released after their data year. It supports
annual retrospective modeling but is not an exact historical publication timestamp. Feature
construction must select only rows whose availability year is no later than the forecast origin.

This table describes observed neighborhood state. It does not contain training-fitted scaling,
imputation, feature selection, targets, or split assignments.

The first published build contains 1,018,099 rows covering ACS releases from 2010 through 2024
and 84,414 distinct canonical tracts overall. Exactly 59,607 rows are available in each pre-2020
release because those years use the stable tract subset. Coverage expands after the geography
change; that larger later-period population must not be described as a balanced 2010-2024 panel.
All uniqueness, availability-year, alignment-method, and stable-only pre-2020 checks passed.

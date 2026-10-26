# `gold_historical_tract_coverage`

[Back to the data documentation index](README.md)

- **Layer:** Gold historical products
- **Databricks table:** `workspace.neighborhood_twin_gold.gold_historical_tract_coverage`
- **Grain and key:** one row per ACS release and geography-alignment outcome; the natural key is
  `acs_release_year` plus `geography_alignment_method`.
- **Purpose:** makes longitudinal tract retention and exclusion visible before historical states
  or models are built.
- **Main structure:** ACS release and conservative availability year; source tract vintage;
  alignment method and eligibility; source rows, distinct source tracts, distinct canonical
  tracts, release denominator, retained share; and build lineage.

For 2010-2019 releases, eligible rows use only the conservative stable 2010-to-2020 subset.
Changed or unmatched 2010 tracts remain in this table as explicit ineligible outcomes. Releases
on 2020 geography use direct identity where possible and the audited Connecticut bridge where
necessary. See the [tract vintage coverage contract](../TRACT_VINTAGE_COVERAGE.md) before
comparing counts across releases.

This table is an attrition and interpretation product. It is not a model-training table.


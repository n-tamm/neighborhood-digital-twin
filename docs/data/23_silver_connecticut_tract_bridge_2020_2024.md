# `silver_connecticut_tract_bridge_2020_2024`

[Back to the data documentation index](README.md)

- **Layer:** Silver geography
- **Databricks table:** `workspace.neighborhood_twin_dev.silver_connecticut_tract_bridge_2020_2024`
- **Sample:** [silver_connecticut_tract_bridge_2020_2024.jsonl](../../data/samples/silver_connecticut_tract_bridge_2020_2024.jsonl)

- **Grain and key:** one row per safely matched pair of 2020 and current Connecticut land-tract
  GEOIDs. Both `geoid_2020` and `geoid_current` are unique.
- **Purpose:** lets current Connecticut ACS profiles join to the project's canonical 2020 tract
  backbone after the state replaced its former counties with planning regions.
- **Method:** match only tract codes that are unique in both official source vintages and have
  positive land area on both sides. The build fails if any land tract is unmatched or if either
  GEOID becomes duplicated.
- **Current volume:** 879 mappings. All 879 current land tracts reconcile one-to-one to all 879
  2020 land tracts and are marked `is_statistical_profile_safe=true`.
- **Caution:** the bridge transfers tract identity, not geometry. TIGER boundary maintenance
  changed reported land area for 213 matched tracts, so no area-weighted values are inferred.
  Water-only tracts are intentionally excluded because their universe changed from four records
  to five and they contain no resident population to profile.

This bridge is specific to the Connecticut planning-region change. It is not a general substitute
for the official 2010-to-2020 relationship table or for field-specific historical harmonization.

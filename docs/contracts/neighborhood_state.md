# Neighborhood State Contract

This contract defines the central longitudinal table used for exploration, feature construction, analogue search, and application profiles. It is a design contract until the first pipeline release; accepted field definitions belong in the data dictionary.

## Grain and keys

- **Grain:** one canonical Census tract for one reference year.
- **Primary key:** `tract_geoid`, `year`.
- **Geography:** one declared tract vintage per released table.
- **Time:** annual unless a separate, explicitly named table supports another cadence.

Rows must be unique on the primary key. The same tract and year may not appear under multiple boundary vintages in one release.

## Required metadata fields

| Field | Type | Requirement |
|---|---|---|
| `tract_geoid` | string | Fixed-width valid GEOID in the release geography |
| `year` | integer | Reference year for the state |
| `geography_vintage` | string | Boundary vintage used for all tract fields |
| `state_schema_version` | string | Contract version |
| `source_cutoff_date` | date | Latest permitted source availability for this state |
| `coverage_status` | category | Approved coverage or suppression status |

## Feature families

The released table may contain approved measures from housing market, affordability, supply, demographic, labor-market, mobility, development, environmental, and metro-context families. Each field must record source, unit, reference period, availability lag, missingness rule, and transformation in the data dictionary.

Protected or sensitive demographic context must not be collapsed into a desirability measure. Raw counts and margins of error should be retained upstream where licensing and size permit even when the serving layer uses rates.

## Lineage

Every release must be traceable to source snapshots and the code/configuration that created it. The manifest should identify:

- pipeline commit and run ID;
- source snapshot IDs and checksums;
- geography crosswalk and allocation method;
- transformations, inflation base year, and imputation version;
- validation result and excluded rows.

## Quality checks

- primary-key completeness and uniqueness;
- valid GEOID and geography membership;
- year within declared coverage;
- physical and logical ranges for measures;
- cross-field identities where applicable;
- missingness and coverage thresholds by source, year, and metro;
- no use of data published after `source_cutoff_date`;
- stable row counts or explained changes between releases.

## Compatibility

Adding a nullable field is normally backward-compatible. Changing grain, keys, geography vintage, unit, derivation, or meaning requires a new major schema version and a migration note. Downstream training and serving artifacts must state the state-schema version they accept.


"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Databricks table and column descriptions for the implemented data products.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from neighborhood_twin.data.databricks import qualified_name


@dataclass(frozen=True)
class TableMetadata:
    """Human-readable description and declared grain for one managed table."""

    description: str
    grain: str


TABLE_METADATA: dict[str, TableMetadata] = {
    "source_snapshot_manifest": TableMetadata(
        "Governed lineage, retrieval, licensing, and validation record for every source object.",
        "One row per immutable source snapshot.",
    ),
    "bronze_fhfa_tract_hpi": TableMetadata(
        "Source-shaped FHFA annual tract HPI records with immutable snapshot lineage.",
        "One row per source snapshot, tract GEOID, and observation year.",
    ),
    "bronze_acs5_tract": TableMetadata(
        "Source-shaped ACS five-year tract responses with estimates, "
        "margins of error, and lineage.",
        "One row per source snapshot, tract GEOID, and ACS release year.",
    ),
    "bronze_census_tract_relationship_2010_2020": TableMetadata(
        "Official Census source rows describing 2010-to-2020 tract land and water overlap.",
        "One row per unique 2010 tract and 2020 tract relationship edge.",
    ),
    "bronze_census_tract_display_geometry_2020": TableMetadata(
        "Parsed source attributes and WKB from the simplified 2020 tract cartographic archive.",
        "One row per displayable 2020 Census tract GEOID.",
    ),
    "bronze_quality_metrics": TableMetadata(
        "Append-only validation and feasibility metrics for bronze data builds.",
        "One row per quality run, table, metric, and dimension.",
    ),
    "silver_fhfa_tract_year": TableMetadata(
        "Typed FHFA single-family HPI history with availability flags and build lineage.",
        "One row per 2020 Census tract GEOID and observation year.",
    ),
    "silver_acs_tract_measure": TableMetadata(
        "Primary normalized ACS product retaining estimate, uncertainty, definition, and lineage.",
        "One row per tract GEOID, ACS release year, and governed measure.",
    ),
    "silver_acs_measure_dictionary": TableMetadata(
        "Governed definitions and source codes for every selected ACS measure.",
        "One row per selected ACS measure.",
    ),
    "silver_acs_tract_year": TableMetadata(
        "Generated wide ACS convenience table with readable measures and housing ratios.",
        "One row per tract GEOID and ACS release year.",
    ),
    "silver_quality_metrics": TableMetadata(
        "Append-only validation, reconciliation, missingness, and coverage "
        "metrics for silver builds.",
        "One row per quality run, table, metric, and dimension.",
    ),
    "silver_tract_relationship_2010_2020": TableMetadata(
        "Typed tract relationship edges with mapping structure and conservative stability flags.",
        "One row per unique 2010 tract and 2020 tract relationship edge.",
    ),
    "silver_tract_display_geometry_2020": TableMetadata(
        "Simplified WKB tract geometry for application maps; not approved for spatial analysis.",
        "One row per displayable 2020 Census tract GEOID.",
    ),
    "geography_quality_metrics": TableMetadata(
        "Append-only validation and coverage metrics for relationship and display geometry builds.",
        "One row per geography quality run, metric, and dimension.",
    ),
    "silver_canonical_tract_2020": TableMetadata(
        "Complete relationship-defined 2020 tract dimension with optional display geometry.",
        "One row per 2020 Census tract GEOID.",
    ),
    "canonical_geography_quality_metrics": TableMetadata(
        "Append-only reconciliation and coverage metrics for canonical tract builds.",
        "One row per canonical geography quality run and metric.",
    ),
    "gold_tract_profile_current": TableMetadata(
        "Current national tract profile joining canonical geography, ACS context, "
        "and FHFA history.",
        "One row per 2020 Census tract GEOID.",
    ),
    "gold_similarity_candidate_current": TableMetadata(
        "Current tracts meeting the documented minimum feature-availability screen "
        "for similarity modeling.",
        "One row per candidate 2020 Census tract GEOID.",
    ),
    "gold_forecast_candidate_current": TableMetadata(
        "Current tracts with sufficient recent FHFA history for initial forecasting experiments.",
        "One row per candidate 2020 Census tract GEOID.",
    ),
    "gold_application_demo_tract": TableMetadata(
        "Small configurable state cohort for application development; it does not "
        "define final scope.",
        "One row per displayable current-profile tract in the configured demo states.",
    ),
    "gold_quality_metrics": TableMetadata(
        "Append-only integrity, reconciliation, and volume metrics for current gold products.",
        "One row per gold quality run, table, and metric.",
    ),
}

COMMON_COLUMN_COMMENTS = {
    "geoid": "Eleven-character Census tract GEOID stored as text to preserve leading zeros.",
    "geoid_2010": "Eleven-character 2010 Census tract GEOID.",
    "geoid_2020": "Eleven-character 2020 Census tract GEOID.",
    "state_fips": "Two-character state FIPS code.",
    "county_fips": "Three-character county FIPS code within a state.",
    "county_geoid": "Five-character state and county FIPS identifier.",
    "tract_code": "Six-character Census tract code within a county.",
    "tract_name": "Human-readable Census tract name supplied by the source.",
    "observation_year": "Calendar year of the FHFA HPI observation.",
    "acs_release_year": "Year identifying the published ACS five-year release.",
    "acs_survey_start_year": "First year included in the ACS five-year survey window.",
    "acs_survey_end_year": "Last year included in the ACS five-year survey window.",
    "acs_reference_period": "Text representation of the ACS five-year survey window.",
    "estimate": "Published ACS estimate after documented special values are converted to null.",
    "margin_of_error": "Published ACS 90 percent margin of error paired with the estimate.",
    "relative_margin_of_error": "Margin of error divided by the absolute estimate when defined.",
    "measure_name": "Stable project name for a selected ACS measure.",
    "measure_label": "Readable label describing the selected measure.",
    "universe": "Population or housing universe to which the measure applies.",
    "unit": "Declared unit for the measure.",
    "hpi": "FHFA annual single-family house price index value.",
    "annual_change_pct": "FHFA annual percentage change; null remains distinct from zero change.",
    "hpi_available": "True when the FHFA HPI value is usable for this tract-year.",
    "annual_change_available": "True when the FHFA annual-change value is usable.",
    "latest_hpi_year": "Most recent year with a usable FHFA HPI value for the tract.",
    "latest_hpi": "Most recent usable FHFA annual single-family house price index value.",
    "latest_hpi_annual_change_pct": "Annual HPI percentage change paired with the latest HPI year.",
    "hpi_observation_count": "Number of years with a usable FHFA HPI value for the tract.",
    "hpi_first_year": "Earliest year with a usable FHFA HPI value for the tract.",
    "hpi_last_year": "Latest year with a usable FHFA HPI value for the tract.",
    "has_display_geometry": "True when simplified cartographic geometry is available for mapping.",
    "display_geometry_wkb": "Simplified cartographic geometry encoded as well-known binary.",
    "geometry_wkb": "Geometry encoded as well-known binary.",
    "display_geometry_role": "Declared permitted role of the attached display geometry.",
    "geometry_role": "Declared permitted role of the geometry.",
    "mapping_type": "Exact relationship structure: one-to-one, split, merge, or complex.",
    "source_land_share": "Relationship land overlap divided by 2010 source-tract land area.",
    "target_land_share": "Relationship land overlap divided by 2020 target-tract land area.",
    "is_stable_measure_mapping": "Conservative same-GEOID, two-sided 95 percent land-overlap flag.",
    "is_dominant_source_mapping": (
        "True for the largest source edge when land overlap is at least 95 percent."
    ),
    "validation_status": "Current source-snapshot validation state.",
    "source_snapshot_id": "Content-addressed identifier for the immutable source snapshot.",
    "source_retrieval_timestamp_utc": "UTC timestamp when the source snapshot was retrieved.",
    "source_file_path": "Governed Unity Catalog volume path for the source object.",
    "quality_run_id": "Identifier shared by metrics produced during one validation run.",
    "metric_group": "Quality category such as integrity, coverage, volume, or run summary.",
    "metric_name": "Stable programmatic name of the reported quality measure.",
    "metric_value": "Numeric value recorded for the quality measure.",
    "status": "Quality result: pass, warn, fail, or info.",
    "expectation": "Human-readable condition used to interpret the metric.",
    "notes": "Additional interpretation or limitation for the metric.",
    "has_current_acs_profile": "True when the tract has data in the latest ingested ACS release.",
    "has_fhfa_history": "True when at least one usable FHFA HPI observation exists for the tract.",
    "similarity_feature_count": (
        "Number of the 12 governed similarity inputs available for the tract."
    ),
    "similarity_candidate": (
        "True when current ACS, positive scale fields, and at least eight similarity "
        "inputs are available."
    ),
    "forecast_candidate": (
        "True when current ACS and at least ten recent usable FHFA HPI observations "
        "are available."
    ),
}


def column_comment(column: str) -> str:
    """Return a useful comment for explicit and generated table columns."""

    if column in COMMON_COLUMN_COMMENTS:
        return COMMON_COLUMN_COMMENTS[column]
    if column.endswith("_estimate_missing_reason"):
        return "Reason the associated ACS estimate is unavailable after source-code handling."
    if column.endswith("_margin_of_error_missing_reason"):
        return "Reason the associated ACS margin of error is unavailable."
    if column.endswith("_estimate"):
        return "Published or transparently derived ACS estimate; see the measure dictionary."
    if column.endswith("_margin_of_error"):
        return "Published ACS 90 percent margin of error for the associated estimate."
    if column.endswith("_moe"):
        return "Published ACS 90 percent margin of error paired with the named estimate."
    if column.endswith("_rate") or column.endswith("_share"):
        return (
            "Derived proportion on a zero-to-one scale unless the table description says otherwise."
        )
    if column.endswith("_build_id"):
        return "Identifier for the pipeline build that published this row."
    if column.endswith("_built_at_utc"):
        return "UTC timestamp when the publishing pipeline build completed."
    if column.endswith("_schema_version"):
        return "Version of the executable table contract used for this row."
    return f"{column.replace('_', ' ').capitalize()} as defined by this table's source contract."


def apply_table_metadata(spark: Any, *, catalog: str, schema: str) -> list[str]:
    """Apply idempotent table descriptions and column comments to existing managed tables."""

    updated: list[str] = []
    for table, metadata in TABLE_METADATA.items():
        raw_name = f"{catalog}.{schema}.{table}"
        if not spark.catalog.tableExists(raw_name):
            continue
        name = qualified_name(catalog, schema, table)
        description = f"{metadata.description} Grain: {metadata.grain}".replace("'", "''")
        spark.sql(f"COMMENT ON TABLE {name} IS '{description}'")
        for column in spark.table(raw_name).columns:
            if "`" in column:
                raise ValueError(f"Unsafe column identifier in {raw_name}: {column!r}")
            comment = column_comment(column).replace("'", "''")
            spark.sql(f"ALTER TABLE {name} ALTER COLUMN `{column}` COMMENT '{comment}'")
        updated.append(raw_name)
    return updated

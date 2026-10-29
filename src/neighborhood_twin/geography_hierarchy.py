"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Valid Census hierarchy dimensions for the 50 states and District of Columbia.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.validate import QualityMetric, hard_failures, new_quality_run_id

GEOGRAPHY_SCHEMA_VERSION = "1.0.0"
GEOGRAPHY_QUALITY_TABLE = "geography_hierarchy_quality_metrics"
GEOGRAPHY_TABLES = {
    "country": "silver_geography_country",
    "region": "silver_geography_region",
    "division": "silver_geography_division",
    "state": "silver_geography_state",
    "county": "silver_geography_county",
    "tract": "silver_geography_tract_2020",
}

COUNTRY_ROWS = (
    {"country_code": "US", "country_name": "United States"},
)

REGION_ROWS = (
    {"region_code": "1", "region_name": "Northeast", "country_code": "US"},
    {"region_code": "2", "region_name": "Midwest", "country_code": "US"},
    {"region_code": "3", "region_name": "South", "country_code": "US"},
    {"region_code": "4", "region_name": "West", "country_code": "US"},
)

DIVISION_ROWS = (
    {"division_code": "1", "division_name": "New England", "region_code": "1"},
    {"division_code": "2", "division_name": "Middle Atlantic", "region_code": "1"},
    {"division_code": "3", "division_name": "East North Central", "region_code": "2"},
    {"division_code": "4", "division_name": "West North Central", "region_code": "2"},
    {"division_code": "5", "division_name": "South Atlantic", "region_code": "3"},
    {"division_code": "6", "division_name": "East South Central", "region_code": "3"},
    {"division_code": "7", "division_name": "West South Central", "region_code": "3"},
    {"division_code": "8", "division_name": "Mountain", "region_code": "4"},
    {"division_code": "9", "division_name": "Pacific", "region_code": "4"},
)

_STATE_GROUPS = {
    "1": (
        ("09", "CT", "Connecticut"),
        ("23", "ME", "Maine"),
        ("25", "MA", "Massachusetts"),
        ("33", "NH", "New Hampshire"),
        ("44", "RI", "Rhode Island"),
        ("50", "VT", "Vermont"),
    ),
    "2": (
        ("34", "NJ", "New Jersey"),
        ("36", "NY", "New York"),
        ("42", "PA", "Pennsylvania"),
    ),
    "3": (
        ("17", "IL", "Illinois"),
        ("18", "IN", "Indiana"),
        ("26", "MI", "Michigan"),
        ("39", "OH", "Ohio"),
        ("55", "WI", "Wisconsin"),
    ),
    "4": (
        ("19", "IA", "Iowa"),
        ("20", "KS", "Kansas"),
        ("27", "MN", "Minnesota"),
        ("29", "MO", "Missouri"),
        ("31", "NE", "Nebraska"),
        ("38", "ND", "North Dakota"),
        ("46", "SD", "South Dakota"),
    ),
    "5": (
        ("10", "DE", "Delaware"),
        ("11", "DC", "District of Columbia"),
        ("12", "FL", "Florida"),
        ("13", "GA", "Georgia"),
        ("24", "MD", "Maryland"),
        ("37", "NC", "North Carolina"),
        ("45", "SC", "South Carolina"),
        ("51", "VA", "Virginia"),
        ("54", "WV", "West Virginia"),
    ),
    "6": (
        ("01", "AL", "Alabama"),
        ("21", "KY", "Kentucky"),
        ("28", "MS", "Mississippi"),
        ("47", "TN", "Tennessee"),
    ),
    "7": (
        ("05", "AR", "Arkansas"),
        ("22", "LA", "Louisiana"),
        ("40", "OK", "Oklahoma"),
        ("48", "TX", "Texas"),
    ),
    "8": (
        ("04", "AZ", "Arizona"),
        ("08", "CO", "Colorado"),
        ("16", "ID", "Idaho"),
        ("30", "MT", "Montana"),
        ("32", "NV", "Nevada"),
        ("35", "NM", "New Mexico"),
        ("49", "UT", "Utah"),
        ("56", "WY", "Wyoming"),
    ),
    "9": (
        ("02", "AK", "Alaska"),
        ("06", "CA", "California"),
        ("15", "HI", "Hawaii"),
        ("41", "OR", "Oregon"),
        ("53", "WA", "Washington"),
    ),
}

STATE_ROWS = tuple(
    {
        "state_fips": state_fips,
        "state_abbreviation": abbreviation,
        "state_name": state_name,
        "division_code": division_code,
    }
    for division_code, states in _STATE_GROUPS.items()
    for state_fips, abbreviation, state_name in states
)
SUPPORTED_STATE_FIPS = tuple(sorted(row["state_fips"] for row in STATE_ROWS))


@dataclass(frozen=True)
class GeographyHierarchyBuild:
    """Validated hierarchy frames and their unpublished quality metrics."""

    build_id: str
    built_at_utc: str
    frames: dict[str, Any]
    metrics: list[QualityMetric]


def _with_lineage(frame: Any, *, build_id: str, built_at_utc: str) -> Any:
    """Attach the hierarchy vintage, schema version, and build lineage."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        frame.withColumn("geography_vintage", functions.lit(2020))
        .withColumn("geography_schema_version", functions.lit(GEOGRAPHY_SCHEMA_VERSION))
        .withColumn("geography_build_id", functions.lit(build_id))
        .withColumn(
            "geography_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
    )


def _metric(
    *,
    build_id: str,
    built_at_utc: str,
    table_name: str,
    metric_name: str,
    value: int | float,
    status: str,
    expectation: str,
    metric_group: str = "integrity",
    notes: str = "",
) -> QualityMetric:
    """Create one consistently shaped hierarchy quality metric."""

    return QualityMetric(
        quality_run_id=build_id,
        profiled_at_utc=built_at_utc,
        table_name=table_name,
        metric_group=metric_group,
        metric_name=metric_name,
        dimension="all",
        metric_value=float(value),
        status=status,
        expectation=expectation,
        notes=notes,
    )


def _profile_frame(
    frame: Any,
    *,
    key: str,
    table_name: str,
    build_id: str,
    built_at_utc: str,
    expected_count: int | None = None,
) -> list[QualityMetric]:
    """Validate one hierarchy dimension's volume and key uniqueness."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    summary = frame.agg(
        functions.count(functions.lit(1)).alias("row_count"),
        functions.countDistinct(key).alias("distinct_key_count"),
    ).first()
    row_count = int(summary["row_count"])
    duplicate_count = row_count - int(summary["distinct_key_count"])
    metrics = [
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=table_name,
            metric_group="volume",
            metric_name="row_count",
            value=row_count,
            status="pass" if row_count > 0 else "fail",
            expectation="> 0",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=table_name,
            metric_name="duplicate_key_count",
            value=duplicate_count,
            status="pass" if duplicate_count == 0 else "fail",
            expectation="= 0",
        ),
    ]
    if expected_count is not None:
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=table_name,
                metric_group="reconciliation",
                metric_name="expected_row_difference",
                value=row_count - expected_count,
                status="pass" if row_count == expected_count else "fail",
                expectation="= 0",
            )
        )
    return metrics


def prepare_geography_hierarchy_build(
    spark: Any,
    *,
    catalog: str,
    silver_schema: str,
    built_at: datetime | None = None,
) -> GeographyHierarchyBuild:
    """Build the valid country-to-tract hierarchy for the supported U.S. scope."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    canonical_name = f"{catalog}.{silver_schema}.silver_canonical_tract_2020"
    if not spark.catalog.tableExists(canonical_name):
        raise ValueError(f"Required canonical geography table does not exist: {canonical_name}")

    build_id, built_at_utc = new_quality_run_id(built_at)
    country = spark.createDataFrame(list(COUNTRY_ROWS))
    region = spark.createDataFrame(list(REGION_ROWS)).join(country, "country_code", "inner")
    division = (
        spark.createDataFrame(list(DIVISION_ROWS))
        .join(
            region.select("region_code", "region_name", "country_code", "country_name"),
            "region_code",
        )
    )
    state = (
        spark.createDataFrame(list(STATE_ROWS))
        .join(
            division.select(
                "division_code",
                "division_name",
                "region_code",
                "region_name",
                "country_code",
                "country_name",
            ),
            "division_code",
        )
    )

    canonical = spark.table(canonical_name).where(
        functions.col("state_fips").isin(*SUPPORTED_STATE_FIPS)
    )
    county = (
        canonical.groupBy("county_geoid", "state_fips", "county_fips")
        .agg(functions.max("county_name").alias("county_name"))
        .join(state, "state_fips", "inner")
    )
    tract = (
        canonical.alias("tract")
        .join(
            county.select(
                "county_geoid",
                "county_name",
                "state_fips",
                "state_abbreviation",
                "state_name",
                "division_code",
                "division_name",
                "region_code",
                "region_name",
                "country_code",
                "country_name",
            ).alias("county"),
            functions.col("tract.county_geoid") == functions.col("county.county_geoid"),
            "inner",
        )
        .select(
            functions.col("tract.geoid_2020"),
            functions.col("tract.tract_code"),
            functions.col("tract.tract_name"),
            functions.col("county.county_geoid"),
            functions.col("county.county_name"),
            functions.col("county.state_fips"),
            functions.col("county.state_abbreviation"),
            functions.col("county.state_name"),
            functions.col("county.division_code"),
            functions.col("county.division_name"),
            functions.col("county.region_code"),
            functions.col("county.region_name"),
            functions.col("county.country_code"),
            functions.col("county.country_name"),
            functions.col("tract.land_area_sqm"),
            functions.col("tract.water_area_sqm"),
            functions.col("tract.has_display_geometry"),
        )
    )

    raw_frames = {
        GEOGRAPHY_TABLES["country"]: country,
        GEOGRAPHY_TABLES["region"]: region,
        GEOGRAPHY_TABLES["division"]: division,
        GEOGRAPHY_TABLES["state"]: state,
        GEOGRAPHY_TABLES["county"]: county,
        GEOGRAPHY_TABLES["tract"]: tract,
    }
    frames = {
        name: _with_lineage(frame, build_id=build_id, built_at_utc=built_at_utc)
        for name, frame in raw_frames.items()
    }

    expected_counts = {
        GEOGRAPHY_TABLES["country"]: 1,
        GEOGRAPHY_TABLES["region"]: 4,
        GEOGRAPHY_TABLES["division"]: 9,
        GEOGRAPHY_TABLES["state"]: 51,
        GEOGRAPHY_TABLES["tract"]: canonical.count(),
    }
    keys = {
        GEOGRAPHY_TABLES["country"]: "country_code",
        GEOGRAPHY_TABLES["region"]: "region_code",
        GEOGRAPHY_TABLES["division"]: "division_code",
        GEOGRAPHY_TABLES["state"]: "state_fips",
        GEOGRAPHY_TABLES["county"]: "county_geoid",
        GEOGRAPHY_TABLES["tract"]: "geoid_2020",
    }
    metrics: list[QualityMetric] = []
    for table_name, frame in frames.items():
        metrics.extend(
            _profile_frame(
                frame,
                key=keys[table_name],
                table_name=f"{catalog}.{silver_schema}.{table_name}",
                build_id=build_id,
                built_at_utc=built_at_utc,
                expected_count=expected_counts.get(table_name),
            )
        )

    missing_county_names = county.where(functions.col("county_name").isNull()).count()
    metrics.append(
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=f"{catalog}.{silver_schema}.{GEOGRAPHY_TABLES['county']}",
            metric_group="completeness",
            metric_name="missing_county_name_count",
            value=missing_county_names,
            status="pass" if missing_county_names == 0 else "fail",
            expectation="= 0",
        )
    )
    failure_count = len(hard_failures(metrics))
    metrics.append(
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name="geography_hierarchy_build",
            metric_group="run_summary",
            metric_name="failure_count",
            value=failure_count,
            status="pass" if failure_count == 0 else "fail",
            expectation="= 0",
            notes=(
                "The hierarchy intentionally covers the 50 states and District of Columbia; "
                "territories remain outside Census regions and divisions."
            ),
        )
    )
    return GeographyHierarchyBuild(build_id, built_at_utc, frames, metrics)


def publish_geography_hierarchy_build(
    build: GeographyHierarchyBuild,
    *,
    catalog: str,
    silver_schema: str,
) -> tuple[str, ...]:
    """Publish all hierarchy dimensions only after every hard check passes."""

    failures = hard_failures(build.metrics)
    if failures:
        names = ", ".join(metric.metric_name for metric in failures)
        raise ValueError(f"Geography hierarchy build has hard failures: {names}")

    published: list[str] = []
    for table, frame in build.frames.items():
        table_name = qualified_name(catalog, silver_schema, table)
        (
            frame.write.format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(table_name)
        )
        published.append(table_name)
    return tuple(published)

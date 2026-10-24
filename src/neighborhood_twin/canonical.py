"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Canonical 2020 tract dimension built from the complete relationship universe.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.validate import QualityMetric, hard_failures, new_quality_run_id

CANONICAL_SCHEMA_VERSION = "1.0.0"
CANONICAL_TRACT_TABLE = "silver_canonical_tract_2020"
CANONICAL_QUALITY_TABLE = "canonical_geography_quality_metrics"

CANONICAL_TRACT_COLUMNS = (
    "geoid_2020",
    "state_fips",
    "county_fips",
    "county_geoid",
    "tract_code",
    "tract_name",
    "land_area_sqm",
    "water_area_sqm",
    "state_abbreviation",
    "state_name",
    "county_name",
    "has_display_geometry",
    "display_geometry_wkb",
    "display_geometry_type",
    "minimum_longitude",
    "minimum_latitude",
    "maximum_longitude",
    "maximum_latitude",
    "display_geometry_role",
    "relationship_source_snapshot_id",
    "display_source_snapshot_id",
    "canonical_schema_version",
    "canonical_build_id",
    "canonical_built_at_utc",
)


@dataclass(frozen=True)
class CanonicalBuild:
    """Validated canonical tract frame and its unpublished quality metrics."""

    build_id: str
    built_at_utc: str
    tract_frame: Any
    metrics: list[QualityMetric]


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


def _build_tract_frame(
    relationship: Any,
    display: Any,
    *,
    build_id: str,
    built_at_utc: str,
) -> Any:
    from pyspark.sql import functions  # type: ignore[import-not-found]

    target = relationship.groupBy("geoid_2020").agg(
        functions.max("state_fips_2020").alias("state_fips"),
        functions.max("tract_name_2020").alias("tract_name"),
        functions.max("land_area_2020_sqm").alias("land_area_sqm"),
        functions.max("water_area_2020_sqm").alias("water_area_sqm"),
        functions.max("source_snapshot_id").alias("relationship_source_snapshot_id"),
    )
    display_fields = display.select(
        "geoid_2020",
        "state_abbreviation",
        "state_name",
        "county_name",
        functions.col("geometry_wkb").alias("display_geometry_wkb"),
        functions.col("geometry_type").alias("display_geometry_type"),
        "minimum_longitude",
        "minimum_latitude",
        "maximum_longitude",
        "maximum_latitude",
        functions.col("geometry_role").alias("display_geometry_role"),
        functions.col("source_snapshot_id").alias("display_source_snapshot_id"),
    )
    return (
        target.join(display_fields, "geoid_2020", "left")
        .withColumn("county_fips", functions.substring("geoid_2020", 3, 3))
        .withColumn("county_geoid", functions.substring("geoid_2020", 1, 5))
        .withColumn("tract_code", functions.substring("geoid_2020", 6, 6))
        .withColumn("has_display_geometry", functions.col("display_geometry_wkb").isNotNull())
        .withColumn("canonical_schema_version", functions.lit(CANONICAL_SCHEMA_VERSION))
        .withColumn("canonical_build_id", functions.lit(build_id))
        .withColumn(
            "canonical_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
        .select(*CANONICAL_TRACT_COLUMNS)
    )


def _profile(
    relationship: Any,
    canonical: Any,
    *,
    build_id: str,
    built_at_utc: str,
    table_name: str,
) -> list[QualityMetric]:
    from pyspark.sql import functions  # type: ignore[import-not-found]

    target_count = relationship.select("geoid_2020").distinct().count()
    summary = (
        canonical.agg(
            functions.count(functions.lit(1)).alias("row_count"),
            functions.countDistinct("geoid_2020").alias("distinct_geoid_count"),
            functions.sum(
                functions.when(~functions.col("geoid_2020").rlike("^[0-9]{11}$"), 1).otherwise(0)
            ).alias("invalid_geoid_count"),
            functions.sum(
                functions.when(functions.col("has_display_geometry"), 1).otherwise(0)
            ).alias("display_geometry_count"),
        )
        .first()
        .asDict()
    )
    row_count = int(summary["row_count"])
    duplicate_count = row_count - int(summary["distinct_geoid_count"])
    reconciliation_difference = row_count - target_count
    display_count = int(summary["display_geometry_count"])
    missing_display_count = row_count - display_count

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
        )
    ]
    for name, value in (
        ("duplicate_geoid_count", duplicate_count),
        ("invalid_geoid_count", int(summary["invalid_geoid_count"])),
        ("relationship_reconciliation_difference", reconciliation_difference),
    ):
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=table_name,
                metric_name=name,
                value=value,
                status="pass" if value == 0 else "fail",
                expectation="= 0",
            )
        )
    metrics.extend(
        [
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=table_name,
                metric_group="coverage",
                metric_name="display_geometry_count",
                value=display_count,
                status="info",
                expectation="reported, not required for canonical membership",
            ),
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=table_name,
                metric_group="coverage",
                metric_name="missing_display_geometry_count",
                value=missing_display_count,
                status="info",
                expectation="reported, not treated as tract exclusion",
            ),
        ]
    )
    failure_count = len(hard_failures(metrics))
    metrics.append(
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name="canonical_geography_build",
            metric_group="run_summary",
            metric_name="failure_count",
            value=failure_count,
            status="pass" if failure_count == 0 else "fail",
            expectation="= 0",
        )
    )
    return metrics


def prepare_canonical_build(
    spark: Any,
    *,
    catalog: str,
    schema: str,
    table: str = CANONICAL_TRACT_TABLE,
    built_at: datetime | None = None,
) -> CanonicalBuild:
    """Build the complete relationship-defined tract universe with optional display geometry."""

    relationship_name = f"{catalog}.{schema}.silver_tract_relationship_2010_2020"
    display_name = f"{catalog}.{schema}.silver_tract_display_geometry_2020"
    for name in (relationship_name, display_name):
        if not spark.catalog.tableExists(name):
            raise ValueError(f"Required geography table does not exist: {name}")
    build_id, built_at_utc = new_quality_run_id(built_at)
    relationship = spark.table(relationship_name)
    frame = _build_tract_frame(
        relationship,
        spark.table(display_name),
        build_id=build_id,
        built_at_utc=built_at_utc,
    )
    metrics = _profile(
        relationship,
        frame,
        build_id=build_id,
        built_at_utc=built_at_utc,
        table_name=f"{catalog}.{schema}.{table}",
    )
    return CanonicalBuild(build_id, built_at_utc, frame, metrics)


def publish_canonical_build(
    build: CanonicalBuild,
    *,
    catalog: str,
    schema: str,
    table: str = CANONICAL_TRACT_TABLE,
) -> str:
    """Publish the canonical tract dimension after every hard check passes."""

    failures = hard_failures(build.metrics)
    if failures:
        names = ", ".join(metric.metric_name for metric in failures)
        raise ValueError(f"Canonical geography build has hard failures: {names}")
    table_name = qualified_name(catalog, schema, table)
    (
        build.tract_frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table_name)
    )
    build.tract_frame.sparkSession.sql(
        f"COMMENT ON TABLE {table_name} IS 'Complete 2020 tract dimension with optional "
        "simplified display geometry and explicit coverage flags.'"
    )
    return table_name

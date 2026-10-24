"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Validated 2010-to-2020 census-tract relationship products.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.validate import (
    QualityMetric,
    hard_failures,
    new_quality_run_id,
)

GEOGRAPHY_SCHEMA_VERSION = "1.0.0"
TRACT_RELATIONSHIP_SILVER_TABLE = "silver_tract_relationship_2010_2020"
GEOGRAPHY_QUALITY_TABLE = "geography_quality_metrics"
STABLE_LAND_SHARE_THRESHOLD = 0.95

TRACT_RELATIONSHIP_SILVER_COLUMNS = (
    "geoid_2010",
    "geoid_2020",
    "state_fips_2010",
    "state_fips_2020",
    "tract_name_2010",
    "tract_name_2020",
    "land_area_2010_sqm",
    "land_area_2020_sqm",
    "overlap_land_area_sqm",
    "water_area_2010_sqm",
    "water_area_2020_sqm",
    "overlap_water_area_sqm",
    "source_land_share",
    "target_land_share",
    "source_target_count",
    "target_source_count",
    "mapping_type",
    "source_land_share_rank",
    "is_dominant_source_mapping",
    "is_stable_measure_mapping",
    "weight_limitation",
    "source_snapshot_id",
    "source_retrieval_timestamp_utc",
    "source_file_path",
    "geography_schema_version",
    "geography_build_id",
    "geography_built_at_utc",
)


@dataclass(frozen=True)
class GeographyBuild:
    """Validated, unpublished tract-relationship frame and its quality metrics."""

    build_id: str
    built_at_utc: str
    relationship_frame: Any
    metrics: list[QualityMetric]


def classify_tract_mapping(source_target_count: int, target_source_count: int) -> str:
    """Classify one relationship edge from its source and target degrees."""

    if source_target_count < 1 or target_source_count < 1:
        raise ValueError("Relationship counts must be positive")
    if source_target_count == 1 and target_source_count == 1:
        return "one_to_one"
    if source_target_count > 1 and target_source_count == 1:
        return "split"
    if source_target_count == 1 and target_source_count > 1:
        return "merge"
    return "complex"


def stable_measure_mapping(
    *,
    same_geoid: bool,
    source_land_share: float,
    target_land_share: float,
    threshold: float = STABLE_LAND_SHARE_THRESHOLD,
) -> bool:
    """Return whether a dominant edge is conservative enough for nonadditive measures."""

    if not 0 < threshold <= 1:
        raise ValueError("threshold must be between zero and one")
    return same_geoid and source_land_share >= threshold and target_land_share >= threshold


def _metric(
    *,
    build_id: str,
    built_at_utc: str,
    table_name: str,
    metric_group: str,
    metric_name: str,
    value: int | float,
    status: str,
    expectation: str,
    dimension: str = "all",
    notes: str = "",
) -> QualityMetric:
    return QualityMetric(
        quality_run_id=build_id,
        profiled_at_utc=built_at_utc,
        table_name=table_name,
        metric_group=metric_group,
        metric_name=metric_name,
        dimension=dimension,
        metric_value=float(value),
        status=status,
        expectation=expectation,
        notes=notes,
    )


def _count_when(functions: Any, condition: Any, alias: str) -> Any:
    return (
        functions.coalesce(
            functions.sum(functions.when(condition, 1).otherwise(0)),
            functions.lit(0),
        )
        .cast("long")
        .alias(alias)
    )


def _latest_snapshot(frame: Any) -> Any:
    from pyspark.sql import functions  # type: ignore[import-not-found]

    latest = (
        frame.select("source_snapshot_id", "source_retrieval_timestamp_utc")
        .distinct()
        .orderBy(
            functions.to_timestamp("source_retrieval_timestamp_utc").desc(),
            functions.col("source_snapshot_id").desc(),
        )
        .first()
    )
    if latest is None:
        raise ValueError("Census tract relationship bronze table is empty")
    return frame.where(functions.col("source_snapshot_id") == latest["source_snapshot_id"])


def _safe_share(functions: Any, numerator: Any, denominator: Any) -> Any:
    return functions.when(
        numerator.isNotNull() & denominator.isNotNull() & (denominator > 0),
        numerator / denominator,
    ).otherwise(functions.lit(None).cast("double"))


def _transform_relationship(
    frame: Any,
    *,
    build_id: str,
    built_at_utc: str,
) -> Any:
    from pyspark.sql import (
        Window,  # type: ignore[import-not-found]
        functions,  # type: ignore[import-not-found]
    )

    base = frame.select(
        functions.col("GEOID_TRACT_10").alias("geoid_2010"),
        functions.col("GEOID_TRACT_20").alias("geoid_2020"),
        functions.substring("GEOID_TRACT_10", 1, 2).alias("state_fips_2010"),
        functions.substring("GEOID_TRACT_20", 1, 2).alias("state_fips_2020"),
        functions.col("NAMELSAD_TRACT_10").alias("tract_name_2010"),
        functions.col("NAMELSAD_TRACT_20").alias("tract_name_2020"),
        functions.col("AREALAND_TRACT_10").cast("long").alias("land_area_2010_sqm"),
        functions.col("AREALAND_TRACT_20").cast("long").alias("land_area_2020_sqm"),
        functions.col("AREALAND_PART").cast("long").alias("overlap_land_area_sqm"),
        functions.col("AREAWATER_TRACT_10").cast("long").alias("water_area_2010_sqm"),
        functions.col("AREAWATER_TRACT_20").cast("long").alias("water_area_2020_sqm"),
        functions.col("AREAWATER_PART").cast("long").alias("overlap_water_area_sqm"),
        "source_snapshot_id",
        functions.to_timestamp("source_retrieval_timestamp_utc").alias(
            "source_retrieval_timestamp_utc"
        ),
        "source_file_path",
    )
    source_degree = base.groupBy("geoid_2010").agg(
        functions.countDistinct("geoid_2020").cast("int").alias("source_target_count")
    )
    target_degree = base.groupBy("geoid_2020").agg(
        functions.countDistinct("geoid_2010").cast("int").alias("target_source_count")
    )
    enriched = (
        base.join(source_degree, "geoid_2010", "inner")
        .join(target_degree, "geoid_2020", "inner")
        .withColumn(
            "source_land_share",
            _safe_share(
                functions,
                functions.col("overlap_land_area_sqm"),
                functions.col("land_area_2010_sqm"),
            ),
        )
        .withColumn(
            "target_land_share",
            _safe_share(
                functions,
                functions.col("overlap_land_area_sqm"),
                functions.col("land_area_2020_sqm"),
            ),
        )
    )
    source_rank_window = Window.partitionBy("geoid_2010").orderBy(
        functions.col("source_land_share").desc_nulls_last(),
        functions.col("geoid_2020"),
    )
    mapping_type = (
        functions.when(
            (functions.col("source_target_count") == 1)
            & (functions.col("target_source_count") == 1),
            functions.lit("one_to_one"),
        )
        .when(
            (functions.col("source_target_count") > 1)
            & (functions.col("target_source_count") == 1),
            functions.lit("split"),
        )
        .when(
            (functions.col("source_target_count") == 1)
            & (functions.col("target_source_count") > 1),
            functions.lit("merge"),
        )
        .otherwise(functions.lit("complex"))
    )
    return (
        enriched.withColumn("mapping_type", mapping_type)
        .withColumn(
            "source_land_share_rank",
            functions.row_number().over(source_rank_window).cast("int"),
        )
        .withColumn(
            "is_dominant_source_mapping",
            (functions.col("source_land_share_rank") == 1)
            & (functions.col("source_land_share") >= STABLE_LAND_SHARE_THRESHOLD),
        )
        .withColumn(
            "is_stable_measure_mapping",
            (functions.col("source_land_share_rank") == 1)
            & (functions.col("geoid_2010") == functions.col("geoid_2020"))
            & (functions.col("source_land_share") >= STABLE_LAND_SHARE_THRESHOLD)
            & (functions.col("target_land_share") >= STABLE_LAND_SHARE_THRESHOLD),
        )
        .withColumn(
            "weight_limitation",
            functions.lit(
                "Land-overlap shares are not population or housing weights; do not use "
                "them to transform medians, rates, or indexes."
            ),
        )
        .withColumn("geography_schema_version", functions.lit(GEOGRAPHY_SCHEMA_VERSION))
        .withColumn("geography_build_id", functions.lit(build_id))
        .withColumn(
            "geography_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
        .select(*TRACT_RELATIONSHIP_SILVER_COLUMNS)
    )


def _profile_relationship(
    frame: Any,
    *,
    build_id: str,
    built_at_utc: str,
    table_name: str,
) -> list[QualityMetric]:
    from pyspark.sql import functions  # type: ignore[import-not-found]

    summary = (
        frame.agg(
            functions.count(functions.lit(1)).alias("row_count"),
            functions.countDistinct("geoid_2010").alias("source_tract_count"),
            functions.countDistinct("geoid_2020").alias("target_tract_count"),
            _count_when(
                functions,
                (~functions.col("geoid_2010").rlike("^[0-9]{11}$"))
                | (~functions.col("geoid_2020").rlike("^[0-9]{11}$")),
                "invalid_geoid_count",
            ),
            _count_when(
                functions,
                functions.col("source_land_share").isNull()
                | functions.col("target_land_share").isNull()
                | (functions.col("source_land_share") < 0)
                | (functions.col("source_land_share") > 1.000001)
                | (functions.col("target_land_share") < 0)
                | (functions.col("target_land_share") > 1.000001),
                "invalid_land_share_count",
            ),
            _count_when(
                functions,
                functions.col("is_stable_measure_mapping"),
                "stable_measure_mapping_count",
            ),
            _count_when(
                functions,
                functions.col("is_dominant_source_mapping"),
                "dominant_source_mapping_count",
            ),
        )
        .first()
        .asDict()
    )
    duplicate_pair_count = (
        frame.groupBy("geoid_2010", "geoid_2020").count().where(functions.col("count") > 1).count()
    )
    source_share_failures = (
        frame.groupBy("geoid_2010")
        .agg(functions.sum("source_land_share").alias("share_sum"))
        .where(functions.abs(functions.col("share_sum") - 1.0) > 0.001)
        .count()
    )
    target_share_failures = (
        frame.groupBy("geoid_2020")
        .agg(functions.sum("target_land_share").alias("share_sum"))
        .where(functions.abs(functions.col("share_sum") - 1.0) > 0.001)
        .count()
    )

    metrics = [
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=table_name,
            metric_group="volume",
            metric_name="row_count",
            value=summary["row_count"],
            status="pass" if summary["row_count"] > 0 else "fail",
            expectation="> 0",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=table_name,
            metric_group="coverage",
            metric_name="source_tract_count",
            value=summary["source_tract_count"],
            status="info",
            expectation="monitored against the official source",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=table_name,
            metric_group="coverage",
            metric_name="target_tract_count",
            value=summary["target_tract_count"],
            status="info",
            expectation="monitored against the official source",
        ),
    ]
    for metric_name, value in (
        ("invalid_geoid_count", summary["invalid_geoid_count"]),
        ("invalid_land_share_count", summary["invalid_land_share_count"]),
        ("duplicate_relationship_pair_count", duplicate_pair_count),
        ("source_land_share_sum_failure_count", source_share_failures),
        ("target_land_share_sum_failure_count", target_share_failures),
    ):
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=table_name,
                metric_group="integrity",
                metric_name=metric_name,
                value=value,
                status="pass" if value == 0 else "fail",
                expectation="= 0",
            )
        )

    source_count = int(summary["source_tract_count"])
    for metric_name, value in (
        ("stable_measure_mapping_count", summary["stable_measure_mapping_count"]),
        ("dominant_source_mapping_count", summary["dominant_source_mapping_count"]),
    ):
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=table_name,
                metric_group="mapping_coverage",
                metric_name=metric_name,
                value=value,
                status="info",
                expectation="reported, not treated as universal crosswalk coverage",
            )
        )
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=table_name,
                metric_group="mapping_coverage",
                metric_name=f"{metric_name.removesuffix('_count')}_rate",
                value=value / source_count if source_count else 0,
                status="info",
                expectation="reported, not treated as a quality threshold",
            )
        )

    mapping_counts = frame.groupBy("mapping_type").count().collect()
    for row in mapping_counts:
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=table_name,
                metric_group="mapping_structure",
                metric_name="relationship_row_count",
                value=int(row["count"]),
                status="info",
                expectation="descriptive edge classification",
                dimension=f"mapping_type={row['mapping_type']}",
            )
        )

    stable_by_state = (
        frame.where(functions.col("source_land_share_rank") == 1)
        .groupBy("state_fips_2010")
        .agg(
            functions.count(functions.lit(1)).alias("source_tract_count"),
            _count_when(
                functions,
                functions.col("is_stable_measure_mapping"),
                "stable_count",
            ),
        )
        .collect()
    )
    for row in stable_by_state:
        source_tract_count = int(row["source_tract_count"])
        stable_count = int(row["stable_count"])
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=table_name,
                metric_group="mapping_coverage",
                metric_name="stable_measure_mapping_rate",
                value=stable_count / source_tract_count if source_tract_count else 0,
                status="info",
                expectation="reported by source state",
                dimension=f"state={row['state_fips_2010']}",
            )
        )

    failure_count = len(hard_failures(metrics))
    warning_count = sum(metric.status == "warn" for metric in metrics)
    metrics.extend(
        [
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name="geography_build",
                metric_group="run_summary",
                metric_name="failure_count",
                value=failure_count,
                status="pass" if failure_count == 0 else "fail",
                expectation="= 0",
            ),
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name="geography_build",
                metric_group="run_summary",
                metric_name="warning_count",
                value=warning_count,
                status="pass" if warning_count == 0 else "warn",
                expectation="review every nonzero warning count",
            ),
        ]
    )
    return metrics


def prepare_geography_build(
    spark: Any,
    *,
    catalog: str,
    schema: str,
    relationship_table: str = TRACT_RELATIONSHIP_SILVER_TABLE,
    built_at: datetime | None = None,
) -> GeographyBuild:
    """Transform the latest validated relationship snapshot and run hard checks."""

    bronze_name = f"{catalog}.{schema}.bronze_census_tract_relationship_2010_2020"
    if not spark.catalog.tableExists(bronze_name):
        raise ValueError(f"Required bronze table does not exist: {bronze_name}")
    build_id, built_at_utc = new_quality_run_id(built_at)
    relationship = _transform_relationship(
        _latest_snapshot(spark.table(bronze_name)),
        build_id=build_id,
        built_at_utc=built_at_utc,
    )
    table_name = f"{catalog}.{schema}.{relationship_table}"
    metrics = _profile_relationship(
        relationship,
        build_id=build_id,
        built_at_utc=built_at_utc,
        table_name=table_name,
    )
    return GeographyBuild(build_id, built_at_utc, relationship, metrics)


def publish_geography_build(
    build: GeographyBuild,
    *,
    catalog: str,
    schema: str,
    relationship_table: str = TRACT_RELATIONSHIP_SILVER_TABLE,
) -> str:
    """Publish the current relationship table after every hard check passes."""

    failures = hard_failures(build.metrics)
    if failures:
        names = ", ".join(f"{metric.metric_name}:{metric.dimension}" for metric in failures)
        raise ValueError(f"Geography build has hard quality failures: {names}")
    table_name = qualified_name(catalog, schema, relationship_table)
    (
        build.relationship_frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table_name)
    )
    build.relationship_frame.sparkSession.sql(
        f"COMMENT ON TABLE {table_name} IS 'Official 2010-to-2020 tract overlap relationships "
        "with explicit land-share and nonadditive-measure limitations.'"
    )
    return table_name

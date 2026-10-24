"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Validated Connecticut 2020-to-current tract identity bridge.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.validate import QualityMetric, hard_failures, new_quality_run_id

CONNECTICUT_BRONZE_TABLE = "bronze_census_connecticut_tract_reference"
CONNECTICUT_BRIDGE_TABLE = "silver_connecticut_tract_bridge_2020_2024"
CONNECTICUT_QUALITY_TABLE = "geography_quality_metrics"
CONNECTICUT_BRIDGE_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class ConnecticutBridgeBuild:
    """Validated bridge and its unpublished quality results."""

    build_id: str
    built_at_utc: str
    bridge_frame: Any
    metrics: list[QualityMetric]


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


def _latest_vintage_snapshot(frame: Any, vintage: int) -> Any:
    """Return every row from the most recently retrieved snapshot for one vintage."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    snapshots = (
        frame.where(functions.col("geography_vintage") == vintage)
        .select("source_snapshot_id", "source_retrieval_timestamp_utc")
        .distinct()
        .orderBy(
            functions.to_timestamp("source_retrieval_timestamp_utc").desc(),
            functions.col("source_snapshot_id").desc(),
        )
        .limit(1)
    )
    if snapshots.count() != 1:
        raise ValueError(f"No Connecticut tract reference snapshot exists for {vintage}")
    return frame.join(snapshots.select("source_snapshot_id"), "source_snapshot_id", "inner")


def _build_bridge(
    source_2020: Any,
    source_2024: Any,
    *,
    build_id: str,
    built_at_utc: str,
) -> Any:
    """Join unique non-water tract codes after validating both vintage universes."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    old = source_2020.where(functions.col("land_area_sqm") > 0).alias("old")
    current = source_2024.where(functions.col("land_area_sqm") > 0).alias("current")
    return (
        old.join(current, functions.col("old.tract_code") == functions.col("current.tract_code"))
        .select(
            functions.col("old.geoid").alias("geoid_2020"),
            functions.col("current.geoid").alias("geoid_current"),
            functions.col("old.tract_code").alias("tract_code"),
            functions.col("old.county_fips").alias("county_fips_2020"),
            functions.col("current.county_fips").alias("county_fips_current"),
            functions.col("old.tract_label").alias("tract_label_2020"),
            functions.col("current.tract_label").alias("tract_label_current"),
            functions.col("old.land_area_sqm").alias("land_area_sqm_2020"),
            functions.col("current.land_area_sqm").alias("land_area_sqm_current"),
            functions.col("old.water_area_sqm").alias("water_area_sqm_2020"),
            functions.col("current.water_area_sqm").alias("water_area_sqm_current"),
            functions.lit("unique_state_tract_code_nonwater").alias("mapping_method"),
            functions.lit(True).alias("is_statistical_profile_safe"),
            functions.col("old.source_snapshot_id").alias("source_snapshot_id_2020"),
            functions.col("current.source_snapshot_id").alias("source_snapshot_id_current"),
            functions.lit(CONNECTICUT_BRIDGE_SCHEMA_VERSION).alias("bridge_schema_version"),
            functions.lit(build_id).alias("bridge_build_id"),
            functions.to_timestamp(functions.lit(built_at_utc)).alias("bridge_built_at_utc"),
        )
    )


def _profile_bridge(
    source_2020: Any,
    source_2024: Any,
    bridge: Any,
    *,
    build_id: str,
    built_at_utc: str,
    table_name: str,
) -> list[QualityMetric]:
    """Reconcile bridge coverage and enforce safe one-to-one profile transfer."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    old_land = source_2020.where(functions.col("land_area_sqm") > 0)
    current_land = source_2024.where(functions.col("land_area_sqm") > 0)
    old_water_count = source_2020.where(functions.col("land_area_sqm") == 0).count()
    current_water_count = source_2024.where(functions.col("land_area_sqm") == 0).count()
    old_land_count = old_land.count()
    current_land_count = current_land.count()
    bridge_count = bridge.count()
    duplicate_old = bridge_count - bridge.select("geoid_2020").distinct().count()
    duplicate_current = bridge_count - bridge.select("geoid_current").distinct().count()
    old_unmatched = old_land.join(
        bridge, old_land.geoid == bridge.geoid_2020, "left_anti"
    ).count()
    current_unmatched = current_land.join(
        bridge, current_land.geoid == bridge.geoid_current, "left_anti"
    ).count()
    changed_land_area = bridge.where(
        functions.col("land_area_sqm_2020") != functions.col("land_area_sqm_current")
    ).count()

    metrics = [
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=table_name,
            metric_group="volume",
            metric_name="bridge_row_count",
            value=bridge_count,
            status="pass" if bridge_count > 0 else "fail",
            expectation="> 0",
        )
    ]
    for metric_name, value in (
        ("duplicate_2020_geoid_count", duplicate_old),
        ("duplicate_current_geoid_count", duplicate_current),
        ("unmatched_2020_land_tract_count", old_unmatched),
        ("unmatched_current_land_tract_count", current_unmatched),
        ("2020_land_tract_reconciliation_difference", bridge_count - old_land_count),
        ("current_land_tract_reconciliation_difference", bridge_count - current_land_count),
    ):
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=table_name,
                metric_group="reconciliation",
                metric_name=metric_name,
                value=value,
                status="pass" if value == 0 else "fail",
                expectation="= 0",
            )
        )
    for metric_name, value, notes in (
        (
            "2020_water_only_tract_count",
            old_water_count,
            "Water-only tracts are reconciled but intentionally receive no ACS profile transfer.",
        ),
        (
            "current_water_only_tract_count",
            current_water_count,
            "Planning-region changes alter the water-only tract universe.",
        ),
        (
            "mapped_land_tract_with_area_change_count",
            changed_land_area,
            "TIGER vintages can include boundary maintenance; the bridge transfers tract identity, "
            "not geometry or area-weighted values.",
        ),
    ):
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=table_name,
                metric_group="review",
                metric_name=metric_name,
                value=value,
                status="info",
                expectation="reported",
                notes=notes,
            )
        )
    failures = hard_failures(metrics)
    metrics.append(
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name="connecticut_tract_bridge_build",
            metric_group="run_summary",
            metric_name="failure_count",
            value=len(failures),
            status="pass" if not failures else "fail",
            expectation="= 0",
        )
    )
    return metrics


def prepare_connecticut_bridge_build(
    spark: Any,
    *,
    catalog: str,
    schema: str,
    bridge_table: str = CONNECTICUT_BRIDGE_TABLE,
    built_at: datetime | None = None,
) -> ConnecticutBridgeBuild:
    """Build a checked land-tract bridge from the two accepted source snapshots."""

    bronze_name = f"{catalog}.{schema}.{CONNECTICUT_BRONZE_TABLE}"
    if not spark.catalog.tableExists(bronze_name):
        raise ValueError(f"Required Connecticut reference table does not exist: {bronze_name}")
    source = spark.table(bronze_name)
    source_2020 = _latest_vintage_snapshot(source, 2020)
    source_2024 = _latest_vintage_snapshot(source, 2024)
    build_id, built_at_utc = new_quality_run_id(built_at)
    bridge = _build_bridge(
        source_2020,
        source_2024,
        build_id=build_id,
        built_at_utc=built_at_utc,
    )
    metrics = _profile_bridge(
        source_2020,
        source_2024,
        bridge,
        build_id=build_id,
        built_at_utc=built_at_utc,
        table_name=f"{catalog}.{schema}.{bridge_table}",
    )
    return ConnecticutBridgeBuild(build_id, built_at_utc, bridge, metrics)


def publish_connecticut_bridge_build(
    build: ConnecticutBridgeBuild,
    *,
    catalog: str,
    schema: str,
    bridge_table: str = CONNECTICUT_BRIDGE_TABLE,
) -> str:
    """Publish the bridge only after complete one-to-one land reconciliation."""

    failures = hard_failures(build.metrics)
    if failures:
        names = ", ".join(metric.metric_name for metric in failures)
        raise ValueError(f"Connecticut bridge has hard quality failures: {names}")
    table_name = qualified_name(catalog, schema, bridge_table)
    (
        build.bridge_frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table_name)
    )
    return table_name

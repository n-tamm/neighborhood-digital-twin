"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Bronze-to-silver transformations for the initial FHFA and ACS source tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from neighborhood_twin.data.acs import ACS_CORE_MEASURES
from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.validate import (
    ACS_SPECIAL_VALUES,
    QualityMetric,
    hard_failures,
    new_quality_run_id,
)

SILVER_SCHEMA_VERSION = "1.0.0"
FHFA_SILVER_TABLE = "silver_fhfa_tract_year"
ACS_SILVER_TABLE = "silver_acs_tract_year"
SILVER_QUALITY_TABLE = "silver_quality_metrics"

ACS_DERIVED_RATIO_COLUMNS = (
    "occupancy_rate_estimate",
    "vacancy_rate_estimate",
    "owner_occupancy_rate_estimate",
    "renter_occupancy_rate_estimate",
    "single_family_share_estimate",
    "multifamily_share_estimate",
    "mobile_home_share_estimate",
    "other_structure_share_estimate",
)


@dataclass(frozen=True)
class SilverBuild:
    """Validated, unpublished silver frames and the metrics that describe them."""

    build_id: str
    built_at_utc: str
    fhfa_frame: Any
    acs_frame: Any
    metrics: list[QualityMetric]


def parse_acs_numeric_value(raw_value: str | None) -> tuple[float | None, str | None]:
    """Apply the documented silver missing-value policy to one ACS string value."""

    if raw_value is None or not raw_value.strip():
        return None, "blank"
    try:
        value = float(raw_value.strip())
    except ValueError:
        return None, "parse_failure"
    if value in ACS_SPECIAL_VALUES:
        return None, f"census_special_value:{raw_value.strip()}"
    return value, None


def acs_silver_measure_columns() -> tuple[str, ...]:
    """Return the stable human-readable fields emitted for the ACS measures."""

    return tuple(
        column_name
        for measure in ACS_CORE_MEASURES
        for column_name in (
            f"{measure.name}_estimate",
            f"{measure.name}_moe",
            f"{measure.name}_estimate_missing_reason",
            f"{measure.name}_moe_missing_reason",
            f"{measure.name}_relative_moe",
        )
    )


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


def _latest_fhfa_snapshot(frame: Any) -> Any:
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
        raise ValueError("FHFA bronze table is empty")
    return frame.where(functions.col("source_snapshot_id") == latest["source_snapshot_id"])


def _latest_acs_snapshots(frame: Any) -> Any:
    from pyspark.sql import (  # type: ignore[import-not-found]
        Window,
        functions,
    )

    candidates = frame.select(
        "state",
        "acs_release_year",
        "source_snapshot_id",
        "source_retrieval_timestamp_utc",
    ).distinct()
    window = Window.partitionBy("state", "acs_release_year").orderBy(
        functions.to_timestamp("source_retrieval_timestamp_utc").desc(),
        functions.col("source_snapshot_id").desc(),
    )
    selected = (
        candidates.withColumn("snapshot_rank", functions.row_number().over(window))
        .where(functions.col("snapshot_rank") == 1)
        .select("state", "acs_release_year", "source_snapshot_id")
    )
    if selected.limit(1).count() == 0:
        raise ValueError("ACS bronze table is empty")
    return frame.join(
        functions.broadcast(selected),
        ["state", "acs_release_year", "source_snapshot_id"],
        "inner",
    )


def _acs_numeric_expressions(functions: Any, column_name: str) -> tuple[Any, Any]:
    text_value = functions.trim(functions.col(column_name))
    numeric_value = text_value.cast("double")
    is_blank = functions.col(column_name).isNull() | (text_value == "")
    is_special = numeric_value.isin([float(item) for item in ACS_SPECIAL_VALUES])
    parsed_value = (
        functions.when(is_blank | is_special | numeric_value.isNull(), None)
        .otherwise(numeric_value)
        .cast("double")
    )
    missing_reason = (
        functions.when(is_blank, functions.lit("blank"))
        .when(
            is_special,
            functions.concat(functions.lit("census_special_value:"), text_value),
        )
        .when(numeric_value.isNull(), functions.lit("parse_failure"))
        .otherwise(functions.lit(None).cast("string"))
    )
    return parsed_value, missing_reason


def _safe_ratio(functions: Any, numerator: Any, denominator: Any) -> Any:
    return functions.when(
        numerator.isNotNull() & denominator.isNotNull() & (denominator > 0),
        numerator / denominator,
    ).otherwise(functions.lit(None).cast("double"))


def _transform_fhfa(frame: Any, *, build_id: str, built_at_utc: str) -> Any:
    from pyspark.sql import functions  # type: ignore[import-not-found]

    return frame.select(
        functions.col("tract").alias("geoid"),
        functions.substring("tract", 1, 2).alias("state_fips"),
        functions.upper(functions.trim("state_abbr")).alias("state_abbr"),
        functions.col("year").cast("int").alias("observation_year"),
        functions.col("annual_change").cast("double").alias("annual_change_pct"),
        functions.col("hpi").cast("double").alias("hpi"),
        functions.col("hpi1990").cast("double").alias("hpi_1990_base"),
        functions.col("hpi2000").cast("double").alias("hpi_2000_base"),
        functions.col("hpi").isNotNull().alias("hpi_available"),
        functions.col("annual_change").isNotNull().alias("annual_change_available"),
        functions.lit("2020").alias("source_geography_vintage"),
        functions.col("source_snapshot_id"),
        functions.to_timestamp("source_retrieval_timestamp_utc").alias(
            "source_retrieval_timestamp_utc"
        ),
        functions.col("source_file_path"),
        functions.lit(SILVER_SCHEMA_VERSION).alias("silver_schema_version"),
        functions.lit(build_id).alias("silver_build_id"),
        functions.to_timestamp(functions.lit(built_at_utc)).alias("silver_built_at_utc"),
    )


def _transform_acs(frame: Any, *, build_id: str, built_at_utc: str) -> Any:
    from pyspark.sql import functions  # type: ignore[import-not-found]

    transformed = frame.select(
        functions.col("geoid"),
        functions.col("state").alias("state_fips"),
        functions.concat(functions.col("state"), functions.col("county")).alias(
            "county_geoid"
        ),
        functions.col("county").alias("county_fips"),
        functions.col("tract").alias("tract_code"),
        functions.col("NAME").alias("tract_name"),
        functions.col("acs_release_year").cast("int"),
        functions.col("acs_survey_start_year").cast("int"),
        functions.col("acs_survey_end_year").cast("int"),
        functions.concat_ws(
            "-",
            functions.col("acs_survey_start_year"),
            functions.col("acs_survey_end_year"),
        ).alias("acs_reference_period"),
        functions.lit("2020").alias("source_geography_vintage"),
        *[functions.col(code) for measure in ACS_CORE_MEASURES for code in (
            measure.estimate_code,
            measure.margin_of_error_code,
        )],
        functions.col("source_snapshot_id"),
        functions.to_timestamp("source_retrieval_timestamp_utc").alias(
            "source_retrieval_timestamp_utc"
        ),
        functions.col("source_file_path"),
        functions.lit(SILVER_SCHEMA_VERSION).alias("silver_schema_version"),
        functions.lit(build_id).alias("silver_build_id"),
        functions.to_timestamp(functions.lit(built_at_utc)).alias("silver_built_at_utc"),
    )

    raw_columns: list[str] = []
    for measure in ACS_CORE_MEASURES:
        estimate, estimate_reason = _acs_numeric_expressions(
            functions, measure.estimate_code
        )
        margin_of_error, moe_reason = _acs_numeric_expressions(
            functions, measure.margin_of_error_code
        )
        estimate_name = f"{measure.name}_estimate"
        moe_name = f"{measure.name}_moe"
        transformed = (
            transformed.withColumn(estimate_name, estimate)
            .withColumn(moe_name, margin_of_error)
            .withColumn(
                f"{measure.name}_estimate_missing_reason",
                estimate_reason,
            )
            .withColumn(f"{measure.name}_moe_missing_reason", moe_reason)
            .withColumn(
                f"{measure.name}_relative_moe",
                _safe_ratio(
                    functions,
                    functions.abs(functions.col(moe_name)),
                    functions.abs(functions.col(estimate_name)),
                ),
            )
        )
        raw_columns.extend((measure.estimate_code, measure.margin_of_error_code))

    transformed = transformed.drop(*raw_columns)
    housing_units = functions.col("housing_units_total_estimate")
    occupied_units = functions.col("occupied_units_estimate")
    vacant_units = functions.col("vacant_units_estimate")
    tenure_total = functions.col("occupied_tenure_total_estimate")
    owner_units = functions.col("owner_occupied_units_estimate")
    renter_units = functions.col("renter_occupied_units_estimate")
    structure_total = functions.col("units_in_structure_total_estimate")
    single_family_units = (
        functions.col("single_family_detached_estimate")
        + functions.col("single_family_attached_estimate")
    )
    multifamily_units = functions.col("units_in_2_unit_buildings_estimate")
    for name in (
        "units_in_3_to_4_unit_buildings_estimate",
        "units_in_5_to_9_unit_buildings_estimate",
        "units_in_10_to_19_unit_buildings_estimate",
        "units_in_20_to_49_unit_buildings_estimate",
        "units_in_50_plus_unit_buildings_estimate",
    ):
        multifamily_units = multifamily_units + functions.col(name)

    return (
        transformed.withColumn(
            "occupancy_rate_estimate",
            _safe_ratio(functions, occupied_units, housing_units),
        )
        .withColumn(
            "vacancy_rate_estimate",
            _safe_ratio(functions, vacant_units, housing_units),
        )
        .withColumn(
            "owner_occupancy_rate_estimate",
            _safe_ratio(functions, owner_units, tenure_total),
        )
        .withColumn(
            "renter_occupancy_rate_estimate",
            _safe_ratio(functions, renter_units, tenure_total),
        )
        .withColumn(
            "single_family_share_estimate",
            _safe_ratio(functions, single_family_units, structure_total),
        )
        .withColumn(
            "multifamily_share_estimate",
            _safe_ratio(functions, multifamily_units, structure_total),
        )
        .withColumn(
            "mobile_home_share_estimate",
            _safe_ratio(
                functions,
                functions.col("mobile_homes_estimate"),
                structure_total,
            ),
        )
        .withColumn(
            "other_structure_share_estimate",
            _safe_ratio(
                functions,
                functions.col("boats_rvs_vans_other_estimate"),
                structure_total,
            ),
        )
    )


def _profile_silver_frames(
    fhfa: Any,
    acs: Any,
    *,
    build_id: str,
    built_at_utc: str,
    fhfa_table_name: str,
    acs_table_name: str,
) -> list[QualityMetric]:
    from pyspark.sql import functions  # type: ignore[import-not-found]

    fhfa_summary = (
        fhfa.agg(
            functions.count(functions.lit(1)).alias("row_count"),
            functions.countDistinct("geoid").alias("tract_count"),
            functions.countDistinct("source_snapshot_id").alias("snapshot_count"),
            functions.min("observation_year").alias("minimum_year"),
            functions.max("observation_year").alias("maximum_year"),
            _count_when(
                functions,
                functions.col("geoid").isNull()
                | (~functions.col("geoid").rlike("^[0-9]{11}$")),
                "invalid_geoid_count",
            ),
            _count_when(functions, functions.col("hpi").isNull(), "null_hpi_count"),
            _count_when(
                functions,
                functions.col("annual_change_pct").isNull(),
                "null_annual_change_count",
            ),
        )
        .first()
        .asDict()
    )
    fhfa_duplicates = (
        fhfa.groupBy("geoid", "observation_year")
        .count()
        .where(functions.col("count") > 1)
        .count()
    )

    parse_failure_condition = functions.lit(False)
    for measure in ACS_CORE_MEASURES:
        parse_failure_condition = parse_failure_condition | (
            functions.col(f"{measure.name}_estimate_missing_reason") == "parse_failure"
        ) | (functions.col(f"{measure.name}_moe_missing_reason") == "parse_failure")
    out_of_range_condition = functions.lit(False)
    for column_name in ACS_DERIVED_RATIO_COLUMNS:
        out_of_range_condition = out_of_range_condition | (
            functions.col(column_name).isNotNull()
            & ((functions.col(column_name) < 0) | (functions.col(column_name) > 1))
        )
    acs_summary = (
        acs.agg(
            functions.count(functions.lit(1)).alias("row_count"),
            functions.countDistinct("geoid").alias("tract_count"),
            functions.countDistinct("state_fips").alias("state_count"),
            functions.countDistinct("source_snapshot_id").alias("snapshot_count"),
            _count_when(
                functions,
                functions.col("geoid").isNull()
                | (~functions.col("geoid").rlike("^[0-9]{11}$")),
                "invalid_geoid_count",
            ),
            _count_when(
                functions,
                parse_failure_condition,
                "parse_failure_row_count",
            ),
            _count_when(
                functions,
                out_of_range_condition,
                "out_of_range_ratio_row_count",
            ),
        )
        .first()
        .asDict()
    )
    acs_duplicates = (
        acs.groupBy("geoid", "acs_release_year")
        .count()
        .where(functions.col("count") > 1)
        .count()
    )

    metrics = [
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=fhfa_table_name,
            metric_group="volume",
            metric_name="row_count",
            value=fhfa_summary["row_count"],
            status="pass" if fhfa_summary["row_count"] > 0 else "fail",
            expectation="> 0",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=fhfa_table_name,
            metric_group="coverage",
            metric_name="tract_count",
            value=fhfa_summary["tract_count"],
            status="info",
            expectation="monitored over time",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=fhfa_table_name,
            metric_group="lineage",
            metric_name="selected_snapshot_count",
            value=fhfa_summary["snapshot_count"],
            status="pass" if fhfa_summary["snapshot_count"] == 1 else "fail",
            expectation="= 1 latest accepted snapshot",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=fhfa_table_name,
            metric_group="time",
            metric_name="minimum_year",
            value=fhfa_summary["minimum_year"] or 0,
            status="info",
            expectation="monitored over time",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=fhfa_table_name,
            metric_group="time",
            metric_name="maximum_year",
            value=fhfa_summary["maximum_year"] or 0,
            status="info",
            expectation="monitored over time",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=fhfa_table_name,
            metric_group="integrity",
            metric_name="invalid_geoid_count",
            value=fhfa_summary["invalid_geoid_count"],
            status="pass" if fhfa_summary["invalid_geoid_count"] == 0 else "fail",
            expectation="= 0",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=fhfa_table_name,
            metric_group="integrity",
            metric_name="duplicate_tract_year_count",
            value=fhfa_duplicates,
            status="pass" if fhfa_duplicates == 0 else "fail",
            expectation="= 0",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=fhfa_table_name,
            metric_group="missingness",
            metric_name="null_hpi_count",
            value=fhfa_summary["null_hpi_count"],
            status="info",
            expectation="retained and flagged; never converted to zero",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=fhfa_table_name,
            metric_group="missingness",
            metric_name="null_annual_change_count",
            value=fhfa_summary["null_annual_change_count"],
            status="info",
            expectation="retained and flagged; never converted to zero",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=acs_table_name,
            metric_group="volume",
            metric_name="row_count",
            value=acs_summary["row_count"],
            status="pass" if acs_summary["row_count"] > 0 else "fail",
            expectation="> 0",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=acs_table_name,
            metric_group="coverage",
            metric_name="tract_count",
            value=acs_summary["tract_count"],
            status="info",
            expectation="monitored over time",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=acs_table_name,
            metric_group="coverage",
            metric_name="state_count",
            value=acs_summary["state_count"],
            status="info",
            expectation="monitored over time",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=acs_table_name,
            metric_group="lineage",
            metric_name="selected_snapshot_count",
            value=acs_summary["snapshot_count"],
            status="pass"
            if acs_summary["snapshot_count"] == acs_summary["state_count"]
            else "fail",
            expectation="one latest snapshot per state and release",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=acs_table_name,
            metric_group="integrity",
            metric_name="invalid_geoid_count",
            value=acs_summary["invalid_geoid_count"],
            status="pass" if acs_summary["invalid_geoid_count"] == 0 else "fail",
            expectation="= 0",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=acs_table_name,
            metric_group="integrity",
            metric_name="duplicate_tract_release_count",
            value=acs_duplicates,
            status="pass" if acs_duplicates == 0 else "fail",
            expectation="= 0",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=acs_table_name,
            metric_group="parseability",
            metric_name="parse_failure_row_count",
            value=acs_summary["parse_failure_row_count"],
            status="pass" if acs_summary["parse_failure_row_count"] == 0 else "fail",
            expectation="= 0",
        ),
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=acs_table_name,
            metric_group="range",
            metric_name="out_of_range_derived_ratio_row_count",
            value=acs_summary["out_of_range_ratio_row_count"],
            status="pass" if acs_summary["out_of_range_ratio_row_count"] == 0 else "fail",
            expectation="= 0; non-null housing ratios remain between 0 and 1",
        ),
    ]

    fhfa_keys = fhfa.select(
        "geoid",
        functions.col("observation_year").alias("acs_release_year"),
        "hpi_available",
    )
    coverage = (
        acs.select("geoid", "state_fips", "acs_release_year")
        .join(fhfa_keys, ["geoid", "acs_release_year"], "left")
        .groupBy("state_fips")
        .agg(
            functions.count(functions.lit(1)).alias("acs_tract_count"),
            _count_when(
                functions,
                functions.col("hpi_available") == functions.lit(True),
                "usable_hpi_count",
            ),
        )
        .collect()
    )
    total_acs = sum(int(row["acs_tract_count"]) for row in coverage)
    total_usable = sum(int(row["usable_hpi_count"]) for row in coverage)
    coverage_rows = [("all", total_acs, total_usable)] + [
        (
            str(row["state_fips"]),
            int(row["acs_tract_count"]),
            int(row["usable_hpi_count"]),
        )
        for row in coverage
    ]
    for state, acs_count, usable_count in coverage_rows:
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=f"{fhfa_table_name}__to__{acs_table_name}",
                metric_group="target_coverage",
                metric_name="same_year_usable_hpi_rate",
                value=usable_count / acs_count if acs_count else 0,
                status="info",
                expectation="reported, not silently filtered",
                dimension=f"state={state}",
            )
        )

    failure_count = len(hard_failures(metrics))
    warning_count = sum(metric.status == "warn" for metric in metrics)
    metrics.extend(
        [
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name="silver_build",
                metric_group="run_summary",
                metric_name="failure_count",
                value=failure_count,
                status="pass" if failure_count == 0 else "fail",
                expectation="= 0",
            ),
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name="silver_build",
                metric_group="run_summary",
                metric_name="warning_count",
                value=warning_count,
                status="pass" if warning_count == 0 else "warn",
                expectation="review every nonzero warning count",
            ),
        ]
    )
    return metrics


def prepare_silver_build(
    spark: Any,
    *,
    catalog: str,
    schema: str,
    fhfa_table: str = FHFA_SILVER_TABLE,
    acs_table: str = ACS_SILVER_TABLE,
    built_at: datetime | None = None,
) -> SilverBuild:
    """Select accepted bronze snapshots, transform them, and validate the result."""

    bronze_fhfa_name = f"{catalog}.{schema}.bronze_fhfa_tract_hpi"
    bronze_acs_name = f"{catalog}.{schema}.bronze_acs5_tract"
    for table_name in (bronze_fhfa_name, bronze_acs_name):
        if not spark.catalog.tableExists(table_name):
            raise ValueError(f"Required bronze table does not exist: {table_name}")

    build_id, built_at_utc = new_quality_run_id(built_at)
    fhfa = _transform_fhfa(
        _latest_fhfa_snapshot(spark.table(bronze_fhfa_name)),
        build_id=build_id,
        built_at_utc=built_at_utc,
    )
    acs = _transform_acs(
        _latest_acs_snapshots(spark.table(bronze_acs_name)),
        build_id=build_id,
        built_at_utc=built_at_utc,
    )
    fhfa_table_name = f"{catalog}.{schema}.{fhfa_table}"
    acs_table_name = f"{catalog}.{schema}.{acs_table}"
    metrics = _profile_silver_frames(
        fhfa,
        acs,
        build_id=build_id,
        built_at_utc=built_at_utc,
        fhfa_table_name=fhfa_table_name,
        acs_table_name=acs_table_name,
    )
    return SilverBuild(
        build_id=build_id,
        built_at_utc=built_at_utc,
        fhfa_frame=fhfa,
        acs_frame=acs,
        metrics=metrics,
    )


def publish_silver_build(
    build: SilverBuild,
    *,
    catalog: str,
    schema: str,
    fhfa_table: str = FHFA_SILVER_TABLE,
    acs_table: str = ACS_SILVER_TABLE,
) -> tuple[str, str]:
    """Overwrite the current derived silver tables after all hard checks pass."""

    failures = hard_failures(build.metrics)
    if failures:
        names = ", ".join(
            f"{metric.table_name}:{metric.metric_name}:{metric.dimension}"
            for metric in failures
        )
        raise ValueError(f"Silver build has hard quality failures: {names}")

    fhfa_name = qualified_name(catalog, schema, fhfa_table)
    acs_name = qualified_name(catalog, schema, acs_table)
    (
        build.fhfa_frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(fhfa_name)
    )
    (
        build.acs_frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(acs_name)
    )
    return fhfa_name, acs_name

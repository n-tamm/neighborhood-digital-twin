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

from neighborhood_twin.data.acs import (
    ACS_CORE_MEASURES,
    ACS_GROUP_METADATA,
    acs_measure_dictionary_records,
)
from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.validate import (
    ACS_SPECIAL_VALUES,
    QualityMetric,
    hard_failures,
    new_quality_run_id,
)

SILVER_SCHEMA_VERSION = "1.1.0"
FHFA_SILVER_TABLE = "silver_fhfa_tract_year"
ACS_SILVER_TABLE = "silver_acs_tract_year"
ACS_MEASURE_SILVER_TABLE = "silver_acs_tract_measure"
ACS_DICTIONARY_SILVER_TABLE = "silver_acs_measure_dictionary"
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
    acs_measure_frame: Any
    acs_dictionary_frame: Any
    metrics: list[QualityMetric]


FHFA_SILVER_COLUMNS = (
    "geoid",
    "state_fips",
    "state_abbr",
    "observation_year",
    "annual_change_pct",
    "hpi",
    "hpi_1990_base",
    "hpi_2000_base",
    "hpi_available",
    "annual_change_available",
    "source_geography_vintage",
    "source_snapshot_id",
    "source_retrieval_timestamp_utc",
    "source_file_path",
    "silver_schema_version",
    "silver_build_id",
    "silver_built_at_utc",
)

ACS_WIDE_IDENTIFIER_COLUMNS = (
    "geoid",
    "state_fips",
    "county_geoid",
    "county_fips",
    "tract_code",
    "tract_name",
    "acs_release_year",
    "acs_survey_start_year",
    "acs_survey_end_year",
    "acs_reference_period",
    "source_geography_vintage",
    "source_snapshot_id",
    "source_retrieval_timestamp_utc",
    "source_file_path",
    "silver_schema_version",
    "silver_build_id",
    "silver_built_at_utc",
)

ACS_MEASURE_SILVER_COLUMNS = (
    "geoid",
    "state_fips",
    "county_geoid",
    "county_fips",
    "tract_code",
    "tract_name",
    "acs_release_year",
    "acs_survey_start_year",
    "acs_survey_end_year",
    "acs_reference_period",
    "source_geography_vintage",
    "measure_order",
    "measure_name",
    "group_code",
    "measure_label",
    "table_concept",
    "universe",
    "unit",
    "estimate",
    "margin_of_error",
    "relative_margin_of_error",
    "estimate_missing_reason",
    "margin_of_error_missing_reason",
    "source_snapshot_id",
    "source_retrieval_timestamp_utc",
    "source_file_path",
    "silver_schema_version",
    "silver_build_id",
    "silver_built_at_utc",
)

ACS_DICTIONARY_SILVER_COLUMNS = (
    "measure_order",
    "measure_name",
    "group_code",
    "measure_label",
    "table_concept",
    "universe",
    "unit",
    "estimate_code",
    "margin_of_error_code",
    "metadata_release_year",
    "metadata_url",
    "silver_schema_version",
    "silver_build_id",
    "silver_built_at_utc",
)


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


def acs_wide_silver_columns() -> tuple[str, ...]:
    """Return the exact column contract for the generated wide ACS table."""

    return (
        *ACS_WIDE_IDENTIFIER_COLUMNS,
        *acs_silver_measure_columns(),
        *ACS_DERIVED_RATIO_COLUMNS,
    )


def _schema_contract_mismatch_count(
    frame: Any,
    *,
    expected_columns: tuple[str, ...],
    expected_types: dict[str, str],
) -> int:
    """Count missing, unexpected, reordered, and incorrectly typed fields."""

    actual_columns = tuple(frame.columns)
    actual_types = dict(frame.dtypes)
    mismatch_count = len(set(expected_columns).symmetric_difference(actual_columns))
    mismatch_count += int(actual_columns != expected_columns)
    mismatch_count += sum(
        actual_types.get(column_name) != expected_type
        for column_name, expected_type in expected_types.items()
    )
    return mismatch_count


def _silver_schema_contracts() -> dict[str, tuple[tuple[str, ...], dict[str, str]]]:
    """Return executable column and Spark-type contracts for each silver product."""

    fhfa_types = {
        **{column: "string" for column in FHFA_SILVER_COLUMNS},
        "observation_year": "int",
        "annual_change_pct": "double",
        "hpi": "double",
        "hpi_1990_base": "double",
        "hpi_2000_base": "double",
        "hpi_available": "boolean",
        "annual_change_available": "boolean",
        "source_retrieval_timestamp_utc": "timestamp",
        "silver_built_at_utc": "timestamp",
    }
    acs_wide_types = {
        **{column: "string" for column in acs_wide_silver_columns()},
        "acs_release_year": "int",
        "acs_survey_start_year": "int",
        "acs_survey_end_year": "int",
        "source_retrieval_timestamp_utc": "timestamp",
        "silver_built_at_utc": "timestamp",
        **{
            column: "double"
            for column in acs_silver_measure_columns()
            if not column.endswith("_missing_reason")
        },
        **{column: "double" for column in ACS_DERIVED_RATIO_COLUMNS},
    }
    acs_measure_types = {
        **{column: "string" for column in ACS_MEASURE_SILVER_COLUMNS},
        "acs_release_year": "int",
        "acs_survey_start_year": "int",
        "acs_survey_end_year": "int",
        "measure_order": "int",
        "estimate": "double",
        "margin_of_error": "double",
        "relative_margin_of_error": "double",
        "source_retrieval_timestamp_utc": "timestamp",
        "silver_built_at_utc": "timestamp",
    }
    acs_dictionary_types = {
        **{column: "string" for column in ACS_DICTIONARY_SILVER_COLUMNS},
        "measure_order": "int",
        "metadata_release_year": "int",
        "silver_built_at_utc": "timestamp",
    }
    return {
        "fhfa": (FHFA_SILVER_COLUMNS, fhfa_types),
        "acs_wide": (acs_wide_silver_columns(), acs_wide_types),
        "acs_measure": (ACS_MEASURE_SILVER_COLUMNS, acs_measure_types),
        "acs_dictionary": (ACS_DICTIONARY_SILVER_COLUMNS, acs_dictionary_types),
    }


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
    """Create one consistently shaped silver quality metric."""

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
    """Return a null-safe Spark expression that counts rows meeting a condition."""

    return (
        functions.coalesce(
            functions.sum(functions.when(condition, 1).otherwise(0)),
            functions.lit(0),
        )
        .cast("long")
        .alias(alias)
    )


def _latest_fhfa_snapshot(frame: Any) -> Any:
    """Select every row from the most recently retrieved FHFA snapshot."""

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
    """Select the latest ACS snapshot independently for each state and release."""

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
    """Build Spark expressions for a cleaned ACS value and its missing reason."""

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
    """Divide valid Spark columns with a positive denominator and null otherwise."""

    return functions.when(
        numerator.isNotNull() & denominator.isNotNull() & (denominator > 0),
        numerator / denominator,
    ).otherwise(functions.lit(None).cast("double"))


def _acs_geography_vintage(functions: Any) -> Any:
    """Map ACS releases to the decennial tract definitions used by Census."""

    release_year = functions.col("acs_release_year").cast("int")
    return (
        functions.when(release_year >= 2020, functions.lit("2020"))
        .when(release_year >= 2010, functions.lit("2010"))
        .when(release_year == 2009, functions.lit("2000"))
        .otherwise(functions.lit(None).cast("string"))
    )


def _transform_fhfa(frame: Any, *, build_id: str, built_at_utc: str) -> Any:
    """Standardize accepted FHFA bronze rows and attach silver lineage."""

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
    """Clean accepted ACS bronze rows into the governed wide silver contract."""

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
        _acs_geography_vintage(functions).alias("source_geography_vintage"),
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


def _transform_acs_measures(acs: Any) -> Any:
    """Normalize the wide ACS convenience table to one row per tract and measure."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    identifier_columns = ACS_WIDE_IDENTIFIER_COLUMNS[:11]
    lineage_columns = ACS_WIDE_IDENTIFIER_COLUMNS[11:]
    measure_frames = []
    for measure_order, measure in enumerate(ACS_CORE_MEASURES, start=1):
        group = ACS_GROUP_METADATA[measure.group_code]
        measure_frames.append(
            acs.select(
                *identifier_columns,
                functions.lit(measure_order).cast("int").alias("measure_order"),
                functions.lit(measure.name).alias("measure_name"),
                functions.lit(measure.group_code).alias("group_code"),
                functions.lit(measure.concept).alias("measure_label"),
                functions.lit(group.concept).alias("table_concept"),
                functions.lit(group.universe).alias("universe"),
                functions.lit(group.unit).alias("unit"),
                functions.col(f"{measure.name}_estimate").alias("estimate"),
                functions.col(f"{measure.name}_moe").alias("margin_of_error"),
                functions.col(f"{measure.name}_relative_moe").alias(
                    "relative_margin_of_error"
                ),
                functions.col(f"{measure.name}_estimate_missing_reason").alias(
                    "estimate_missing_reason"
                ),
                functions.col(f"{measure.name}_moe_missing_reason").alias(
                    "margin_of_error_missing_reason"
                ),
                *lineage_columns,
            )
        )

    normalized = measure_frames[0]
    for measure_frame in measure_frames[1:]:
        normalized = normalized.unionByName(measure_frame)
    return normalized.select(*ACS_MEASURE_SILVER_COLUMNS)


def _build_acs_measure_dictionary(
    spark: Any,
    *,
    metadata_release_year: int,
    build_id: str,
    built_at_utc: str,
) -> Any:
    """Build the governed dictionary for normalized ACS measure rows."""

    from pyspark.sql import functions  # type: ignore[import-not-found]
    from pyspark.sql.types import (  # type: ignore[import-not-found]
        IntegerType,
        StringType,
        StructField,
        StructType,
    )

    schema = StructType(
        [
            StructField("measure_order", IntegerType(), False),
            StructField("measure_name", StringType(), False),
            StructField("group_code", StringType(), False),
            StructField("measure_label", StringType(), False),
            StructField("table_concept", StringType(), False),
            StructField("universe", StringType(), False),
            StructField("unit", StringType(), False),
            StructField("estimate_code", StringType(), False),
            StructField("margin_of_error_code", StringType(), False),
            StructField("metadata_url", StringType(), False),
        ]
    )
    records = [dict(record) for record in acs_measure_dictionary_records(
        release_year=metadata_release_year
    )]
    return (
        spark.createDataFrame(records, schema=schema)
        .withColumn("metadata_release_year", functions.lit(metadata_release_year).cast("int"))
        .withColumn("silver_schema_version", functions.lit(SILVER_SCHEMA_VERSION))
        .withColumn("silver_build_id", functions.lit(build_id))
        .withColumn(
            "silver_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
        .select(*ACS_DICTIONARY_SILVER_COLUMNS)
    )


def _profile_silver_frames(
    fhfa_source: Any,
    acs_source: Any,
    manifest: Any,
    fhfa: Any,
    acs: Any,
    acs_measures: Any,
    acs_dictionary: Any,
    *,
    build_id: str,
    built_at_utc: str,
    fhfa_table_name: str,
    acs_table_name: str,
    acs_measure_table_name: str,
    acs_dictionary_table_name: str,
    manifest_table_name: str,
) -> list[QualityMetric]:
    """Validate all silver products, their balances, schemas, and source coverage."""

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
            functions.countDistinct("state_fips", "acs_release_year").alias(
                "state_release_count"
            ),
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
            _count_when(
                functions,
                functions.col("source_geography_vintage") != "2020",
                "unharmonized_acs_row_count",
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

    schema_contracts = _silver_schema_contracts()
    schema_mismatches = {
        fhfa_table_name: _schema_contract_mismatch_count(
            fhfa,
            expected_columns=schema_contracts["fhfa"][0],
            expected_types=schema_contracts["fhfa"][1],
        ),
        acs_table_name: _schema_contract_mismatch_count(
            acs,
            expected_columns=schema_contracts["acs_wide"][0],
            expected_types=schema_contracts["acs_wide"][1],
        ),
        acs_measure_table_name: _schema_contract_mismatch_count(
            acs_measures,
            expected_columns=schema_contracts["acs_measure"][0],
            expected_types=schema_contracts["acs_measure"][1],
        ),
        acs_dictionary_table_name: _schema_contract_mismatch_count(
            acs_dictionary,
            expected_columns=schema_contracts["acs_dictionary"][0],
            expected_types=schema_contracts["acs_dictionary"][1],
        ),
    }

    nonnegative_condition = functions.lit(False)
    for measure in ACS_CORE_MEASURES:
        nonnegative_condition = nonnegative_condition | (
            functions.col(f"{measure.name}_estimate") < 0
        ) | (functions.col(f"{measure.name}_moe") < 0)

    structure_components = functions.col("single_family_detached_estimate")
    for component in (
        "single_family_attached_estimate",
        "units_in_2_unit_buildings_estimate",
        "units_in_3_to_4_unit_buildings_estimate",
        "units_in_5_to_9_unit_buildings_estimate",
        "units_in_10_to_19_unit_buildings_estimate",
        "units_in_20_to_49_unit_buildings_estimate",
        "units_in_50_plus_unit_buildings_estimate",
        "mobile_homes_estimate",
        "boats_rvs_vans_other_estimate",
    ):
        structure_components = structure_components + functions.col(component)

    balance_summary = (
        acs.agg(
            _count_when(
                functions,
                functions.col("housing_units_total_estimate").isNotNull()
                & functions.col("occupied_units_estimate").isNotNull()
                & functions.col("vacant_units_estimate").isNotNull()
                & (
                    functions.col("housing_units_total_estimate")
                    != functions.col("occupied_units_estimate")
                    + functions.col("vacant_units_estimate")
                ),
                "occupancy_balance_failure_count",
            ),
            _count_when(
                functions,
                functions.col("occupied_tenure_total_estimate").isNotNull()
                & functions.col("owner_occupied_units_estimate").isNotNull()
                & functions.col("renter_occupied_units_estimate").isNotNull()
                & (
                    functions.col("occupied_tenure_total_estimate")
                    != functions.col("owner_occupied_units_estimate")
                    + functions.col("renter_occupied_units_estimate")
                ),
                "tenure_balance_failure_count",
            ),
            _count_when(
                functions,
                functions.col("units_in_structure_total_estimate").isNotNull()
                & structure_components.isNotNull()
                & (functions.col("units_in_structure_total_estimate") != structure_components),
                "structure_balance_failure_count",
            ),
            _count_when(
                functions,
                nonnegative_condition,
                "negative_value_row_count",
            ),
            _count_when(
                functions,
                functions.col("source_geography_vintage").isNull(),
                "unresolved_geography_vintage_count",
            ),
        )
        .first()
        .asDict()
    )

    measure_summary = (
        acs_measures.agg(
            functions.count(functions.lit(1)).alias("row_count"),
            functions.countDistinct("measure_name").alias("measure_count"),
            _count_when(
                functions,
                (functions.col("estimate").isNull())
                != functions.col("estimate_missing_reason").isNotNull(),
                "estimate_reason_mismatch_count",
            ),
            _count_when(
                functions,
                (functions.col("margin_of_error").isNull())
                != functions.col("margin_of_error_missing_reason").isNotNull(),
                "moe_reason_mismatch_count",
            ),
        )
        .first()
        .asDict()
    )
    measure_duplicates = (
        acs_measures.groupBy("geoid", "acs_release_year", "measure_name")
        .count()
        .where(functions.col("count") > 1)
        .count()
    )
    expected_measure_rows = int(acs_summary["row_count"]) * len(ACS_CORE_MEASURES)

    dictionary_summary = (
        acs_dictionary.agg(
            functions.count(functions.lit(1)).alias("row_count"),
            functions.countDistinct("measure_name").alias("measure_name_count"),
            functions.countDistinct("estimate_code").alias("estimate_code_count"),
            functions.countDistinct("margin_of_error_code").alias("moe_code_count"),
        )
        .first()
        .asDict()
    )

    selected_snapshot_ids = (
        fhfa.select(functions.col("source_snapshot_id").alias("snapshot_id"))
        .union(acs.select(functions.col("source_snapshot_id").alias("snapshot_id")))
        .distinct()
    )
    manifest_status = manifest.select("snapshot_id", "validation_status").distinct()
    unregistered_snapshot_count = selected_snapshot_ids.join(
        manifest_status.select("snapshot_id"), "snapshot_id", "left_anti"
    ).count()
    nonvalidated_snapshot_count = (
        selected_snapshot_ids.join(manifest_status, "snapshot_id", "inner")
        .where(functions.col("validation_status") != "bronze_validated")
        .count()
    )

    fhfa_source_count = fhfa_source.count()
    acs_reconciliation_count = (
        acs_source.groupBy(
            functions.col("state").alias("state_fips"), "acs_release_year"
        )
        .count()
        .withColumnRenamed("count", "source_count")
        .join(
            acs.groupBy("state_fips", "acs_release_year")
            .count()
            .withColumnRenamed("count", "silver_count"),
            ["state_fips", "acs_release_year"],
            "full",
        )
        .where(
            functions.coalesce("source_count", functions.lit(-1))
            != functions.coalesce("silver_count", functions.lit(-1))
        )
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
            if acs_summary["snapshot_count"] == acs_summary["state_release_count"]
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
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name=acs_table_name,
            metric_group="geography",
            metric_name="unharmonized_acs_row_count",
            value=acs_summary["unharmonized_acs_row_count"],
            status="info",
            expectation=(
                "reported and excluded from direct FHFA coverage joins until Stage 03 "
                "geography harmonization"
            ),
        ),
    ]

    for table_name, mismatch_count in schema_mismatches.items():
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=table_name,
                metric_group="schema",
                metric_name="schema_column_mismatch_count",
                value=mismatch_count,
                status="pass" if mismatch_count == 0 else "fail",
                expectation="= 0; no missing or unexpected columns",
            )
        )

    for metric_name, value in (
        ("occupancy_balance_failure_count", balance_summary["occupancy_balance_failure_count"]),
        ("tenure_balance_failure_count", balance_summary["tenure_balance_failure_count"]),
        ("structure_balance_failure_count", balance_summary["structure_balance_failure_count"]),
        ("negative_value_row_count", balance_summary["negative_value_row_count"]),
        (
            "unresolved_geography_vintage_count",
            balance_summary["unresolved_geography_vintage_count"],
        ),
    ):
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=acs_table_name,
                metric_group="integrity",
                metric_name=metric_name,
                value=value,
                status="pass" if value == 0 else "fail",
                expectation="= 0",
            )
        )

    long_table_checks = (
        (
            "row_count",
            measure_summary["row_count"],
            measure_summary["row_count"] == expected_measure_rows,
            f"= wide row count x {len(ACS_CORE_MEASURES)} measures",
        ),
        (
            "distinct_measure_count",
            measure_summary["measure_count"],
            measure_summary["measure_count"] == len(ACS_CORE_MEASURES),
            f"= {len(ACS_CORE_MEASURES)}",
        ),
        (
            "duplicate_tract_release_measure_count",
            measure_duplicates,
            measure_duplicates == 0,
            "= 0",
        ),
        (
            "estimate_missing_reason_mismatch_count",
            measure_summary["estimate_reason_mismatch_count"],
            measure_summary["estimate_reason_mismatch_count"] == 0,
            "= 0; null estimates have a reason and non-null estimates do not",
        ),
        (
            "moe_missing_reason_mismatch_count",
            measure_summary["moe_reason_mismatch_count"],
            measure_summary["moe_reason_mismatch_count"] == 0,
            "= 0; null margins of error have a reason and non-null values do not",
        ),
    )
    for metric_name, value, passed, expectation in long_table_checks:
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=acs_measure_table_name,
                metric_group="integrity",
                metric_name=metric_name,
                value=value,
                status="pass" if passed else "fail",
                expectation=expectation,
            )
        )

    dictionary_checks = (
        ("row_count", dictionary_summary["row_count"]),
        ("distinct_measure_name_count", dictionary_summary["measure_name_count"]),
        ("distinct_estimate_code_count", dictionary_summary["estimate_code_count"]),
        ("distinct_margin_of_error_code_count", dictionary_summary["moe_code_count"]),
    )
    for metric_name, value in dictionary_checks:
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=acs_dictionary_table_name,
                metric_group="integrity",
                metric_name=metric_name,
                value=value,
                status="pass" if value == len(ACS_CORE_MEASURES) else "fail",
                expectation=f"= {len(ACS_CORE_MEASURES)}",
            )
        )

    reconciliation_checks = (
        (
            fhfa_table_name,
            "source_to_silver_row_count_difference",
            abs(fhfa_source_count - int(fhfa_summary["row_count"])),
            "= 0 after selecting the latest accepted source snapshot",
        ),
        (
            acs_table_name,
            "state_release_row_count_mismatch_count",
            acs_reconciliation_count,
            "= 0 between selected source groups and silver groups",
        ),
        (
            manifest_table_name,
            "unregistered_selected_snapshot_count",
            unregistered_snapshot_count,
            "= 0",
        ),
        (
            manifest_table_name,
            "nonvalidated_selected_snapshot_count",
            nonvalidated_snapshot_count,
            "= 0; every selected snapshot has bronze_validated status",
        ),
    )
    for table_name, metric_name, value, expectation in reconciliation_checks:
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=table_name,
                metric_group="reconciliation",
                metric_name=metric_name,
                value=value,
                status="pass" if value == 0 else "fail",
                expectation=expectation,
            )
        )

    fhfa_keys = fhfa.select(
        "geoid",
        functions.col("observation_year").alias("acs_release_year"),
        "hpi_available",
    )
    coverage = (
        acs.where(functions.col("source_geography_vintage") == "2020")
        .select("geoid", "state_fips", "acs_release_year")
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
    bronze_schema: str | None = None,
    fhfa_table: str = FHFA_SILVER_TABLE,
    acs_table: str = ACS_SILVER_TABLE,
    acs_measure_table: str = ACS_MEASURE_SILVER_TABLE,
    acs_dictionary_table: str = ACS_DICTIONARY_SILVER_TABLE,
    built_at: datetime | None = None,
) -> SilverBuild:
    """Select accepted bronze snapshots, transform them, and validate the result."""

    bronze_schema = bronze_schema or schema
    bronze_fhfa_name = f"{catalog}.{bronze_schema}.bronze_fhfa_tract_hpi"
    bronze_acs_name = f"{catalog}.{bronze_schema}.bronze_acs5_tract"
    manifest_name = f"{catalog}.{bronze_schema}.source_snapshot_manifest"
    for table_name in (bronze_fhfa_name, bronze_acs_name, manifest_name):
        if not spark.catalog.tableExists(table_name):
            raise ValueError(f"Required bronze table does not exist: {table_name}")

    build_id, built_at_utc = new_quality_run_id(built_at)
    fhfa_source = _latest_fhfa_snapshot(spark.table(bronze_fhfa_name))
    acs_source = _latest_acs_snapshots(spark.table(bronze_acs_name))
    fhfa = _transform_fhfa(
        fhfa_source,
        build_id=build_id,
        built_at_utc=built_at_utc,
    )
    acs = _transform_acs(
        acs_source,
        build_id=build_id,
        built_at_utc=built_at_utc,
    )
    acs_measures = _transform_acs_measures(acs)
    metadata_release_year = int(acs_source.agg({"acs_release_year": "max"}).first()[0])
    acs_dictionary = _build_acs_measure_dictionary(
        spark,
        metadata_release_year=metadata_release_year,
        build_id=build_id,
        built_at_utc=built_at_utc,
    )
    fhfa_table_name = f"{catalog}.{schema}.{fhfa_table}"
    acs_table_name = f"{catalog}.{schema}.{acs_table}"
    acs_measure_table_name = f"{catalog}.{schema}.{acs_measure_table}"
    acs_dictionary_table_name = f"{catalog}.{schema}.{acs_dictionary_table}"
    metrics = _profile_silver_frames(
        fhfa_source,
        acs_source,
        spark.table(manifest_name),
        fhfa,
        acs,
        acs_measures,
        acs_dictionary,
        build_id=build_id,
        built_at_utc=built_at_utc,
        fhfa_table_name=fhfa_table_name,
        acs_table_name=acs_table_name,
        acs_measure_table_name=acs_measure_table_name,
        acs_dictionary_table_name=acs_dictionary_table_name,
        manifest_table_name=manifest_name,
    )
    return SilverBuild(
        build_id=build_id,
        built_at_utc=built_at_utc,
        fhfa_frame=fhfa,
        acs_frame=acs,
        acs_measure_frame=acs_measures,
        acs_dictionary_frame=acs_dictionary,
        metrics=metrics,
    )


def publish_silver_build(
    build: SilverBuild,
    *,
    catalog: str,
    schema: str,
    fhfa_table: str = FHFA_SILVER_TABLE,
    acs_table: str = ACS_SILVER_TABLE,
    acs_measure_table: str = ACS_MEASURE_SILVER_TABLE,
    acs_dictionary_table: str = ACS_DICTIONARY_SILVER_TABLE,
) -> tuple[str, str, str, str]:
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
    acs_measure_name = qualified_name(catalog, schema, acs_measure_table)
    acs_dictionary_name = qualified_name(catalog, schema, acs_dictionary_table)
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
    (
        build.acs_measure_frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(acs_measure_name)
    )
    (
        build.acs_dictionary_frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(acs_dictionary_name)
    )

    table_comments = {
        fhfa_name: "Typed FHFA tract-year house price index history with source lineage.",
        acs_name: (
            "Generated wide ACS tract-release convenience table. Use the normalized measure "
            "table for general exploration and joins."
        ),
        acs_measure_name: (
            "Primary normalized ACS analytical table with one tract-release-measure row, "
            "paired margins of error, missing reasons, and source lineage."
        ),
        acs_dictionary_name: (
            "Data dictionary for every measure in the normalized ACS silver table."
        ),
    }
    for table_name, comment in table_comments.items():
        spark = build.fhfa_frame.sparkSession
        spark.sql(f"COMMENT ON TABLE {table_name} IS '{comment}'")

    return fhfa_name, acs_name, acs_measure_name, acs_dictionary_name

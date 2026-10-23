"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Persisted quality profiling for the Databricks bronze data layer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from neighborhood_twin.data.acs import acs_variable_codes
from neighborhood_twin.data.databricks import qualified_name

QUALITY_STATUSES = frozenset({"pass", "warn", "fail", "info"})

# Census uses these numeric placeholders when an estimate or margin of error cannot be
# represented as an ordinary number. They remain visible in bronze and become null plus a
# reason field during silver processing.
ACS_SPECIAL_VALUES = frozenset(
    {
        -999_999_999,
        -888_888_888,
        -666_666_666,
        -555_555_555,
        -333_333_333,
        -222_222_222,
    }
)


@dataclass(frozen=True)
class QualityMetric:
    """One interpretable quality or coverage measurement from a profiling run."""

    quality_run_id: str
    profiled_at_utc: str
    table_name: str
    metric_group: str
    metric_name: str
    dimension: str
    metric_value: float
    status: str
    expectation: str
    notes: str

    def __post_init__(self) -> None:
        if self.status not in QUALITY_STATUSES:
            raise ValueError(f"Unsupported quality status: {self.status}")
        for field_name in (
            "quality_run_id",
            "profiled_at_utc",
            "table_name",
            "metric_group",
            "metric_name",
            "dimension",
            "expectation",
        ):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} cannot be blank")

    def to_spark_record(self) -> dict[str, object]:
        """Return stable primitive fields for Spark DataFrame construction."""

        return asdict(self)


def new_quality_run_id(profiled_at: datetime | None = None) -> tuple[str, str]:
    """Create a UTC run identifier and its ISO timestamp."""

    timestamp = profiled_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("profiled_at must include timezone information")
    timestamp = timestamp.astimezone(UTC)
    timestamp_text = timestamp.isoformat(timespec="microseconds").replace("+00:00", "Z")
    run_id = timestamp.strftime("%Y%m%dT%H%M%S%fZ")
    return run_id, timestamp_text


def hard_failures(metrics: list[QualityMetric]) -> list[QualityMetric]:
    """Return metrics that should stop downstream pipeline tasks."""

    return [metric for metric in metrics if metric.status == "fail"]


def _metric(
    *,
    run_id: str,
    profiled_at_utc: str,
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
        quality_run_id=run_id,
        profiled_at_utc=profiled_at_utc,
        table_name=table_name,
        metric_group=metric_group,
        metric_name=metric_name,
        dimension=dimension,
        metric_value=float(value),
        status=status,
        expectation=expectation,
        notes=notes,
    )


def _zero_status(value: int | float, *, failure_status: str = "fail") -> str:
    return "pass" if value == 0 else failure_status


def _positive_status(value: int | float) -> str:
    return "pass" if value > 0 else "fail"


def _count_when(functions: Any, condition: Any, alias: str) -> Any:
    return (
        functions.coalesce(
            functions.sum(functions.when(condition, 1).otherwise(0)),
            functions.lit(0),
        )
        .cast("long")
        .alias(alias)
    )


def _number_or_zero(value: int | float | None) -> int | float:
    """Keep metric rows numeric even when an empty Spark input has no min or max."""

    return 0 if value is None else value


def _profile_fhfa(
    frame: Any,
    *,
    run_id: str,
    profiled_at_utc: str,
    table_name: str,
) -> list[QualityMetric]:
    from pyspark.sql import functions  # type: ignore[import-not-found]

    summary = (
        frame.agg(
            functions.count(functions.lit(1)).alias("row_count"),
            functions.countDistinct("tract").alias("distinct_tract_count"),
            functions.countDistinct("source_snapshot_id").alias("snapshot_count"),
            functions.min("year").alias("minimum_year"),
            functions.max("year").alias("maximum_year"),
            _count_when(
                functions,
                functions.col("tract").isNull()
                | (~functions.col("tract").rlike("^[0-9]{11}$")),
                "invalid_geoid_count",
            ),
            _count_when(functions, functions.col("year").isNull(), "null_year_count"),
            _count_when(functions, functions.col("hpi").isNull(), "null_hpi_count"),
            _count_when(
                functions,
                functions.col("hpi").isNotNull() & (functions.col("hpi") <= 0),
                "nonpositive_hpi_count",
            ),
            _count_when(
                functions,
                functions.col("annual_change").isNull(),
                "null_annual_change_count",
            ),
        )
        .first()
        .asDict()
    )
    duplicate_key_count = (
        frame.groupBy("tract", "year")
        .count()
        .where(functions.col("count") > 1)
        .count()
    )
    history = frame.where(
        functions.col("tract").isNotNull() & functions.col("year").isNotNull()
    ).groupBy("tract").agg(functions.countDistinct("year").alias("observed_year_count"))
    history_quantiles = history.approxQuantile(
        "observed_year_count", [0.10, 0.50, 0.90], 0.01
    )
    if len(history_quantiles) != 3:
        history_quantiles = [0.0, 0.0, 0.0]

    metrics = [
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="volume",
            metric_name="row_count",
            value=summary["row_count"],
            status=_positive_status(summary["row_count"]),
            expectation="> 0",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="coverage",
            metric_name="distinct_tract_count",
            value=summary["distinct_tract_count"],
            status="info",
            expectation="monitored over time",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="lineage",
            metric_name="snapshot_count",
            value=summary["snapshot_count"],
            status=_positive_status(summary["snapshot_count"]),
            expectation="> 0",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="time",
            metric_name="minimum_year",
            value=_number_or_zero(summary["minimum_year"]),
            status="info",
            expectation="monitored over time",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="time",
            metric_name="maximum_year",
            value=_number_or_zero(summary["maximum_year"]),
            status="info",
            expectation="monitored over time",
        ),
    ]

    for metric_name, expectation in (
        ("invalid_geoid_count", "= 0"),
        ("null_year_count", "= 0"),
        ("nonpositive_hpi_count", "= 0"),
    ):
        value = summary[metric_name]
        metrics.append(
            _metric(
                run_id=run_id,
                profiled_at_utc=profiled_at_utc,
                table_name=table_name,
                metric_group="integrity",
                metric_name=metric_name,
                value=value,
                status=_zero_status(value),
                expectation=expectation,
            )
        )

    metrics.extend(
        [
            _metric(
                run_id=run_id,
                profiled_at_utc=profiled_at_utc,
                table_name=table_name,
                metric_group="integrity",
                metric_name="duplicate_tract_year_key_count",
                value=duplicate_key_count,
                status=_zero_status(duplicate_key_count),
                expectation="= 0",
            ),
            _metric(
                run_id=run_id,
                profiled_at_utc=profiled_at_utc,
                table_name=table_name,
                metric_group="missingness",
                metric_name="null_hpi_count",
                value=summary["null_hpi_count"],
                status="info",
                expectation="measured before silver policy",
            ),
            _metric(
                run_id=run_id,
                profiled_at_utc=profiled_at_utc,
                table_name=table_name,
                metric_group="missingness",
                metric_name="null_annual_change_count",
                value=summary["null_annual_change_count"],
                status="info",
                expectation="expected for the first observation in some histories",
            ),
        ]
    )

    for percentile, value in zip((10, 50, 90), history_quantiles, strict=True):
        metrics.append(
            _metric(
                run_id=run_id,
                profiled_at_utc=profiled_at_utc,
                table_name=table_name,
                metric_group="coverage",
                metric_name=f"tract_history_years_p{percentile}",
                value=value,
                status="info",
                expectation="monitored over time",
            )
        )
    return metrics


def _usable_acs_value(functions: Any, column_name: str) -> Any:
    value = functions.trim(functions.col(column_name)).cast("double")
    return functions.when(value.isin([float(item) for item in ACS_SPECIAL_VALUES]), None).otherwise(
        value
    )


def _profile_acs(
    frame: Any,
    *,
    run_id: str,
    profiled_at_utc: str,
    table_name: str,
) -> list[QualityMetric]:
    from pyspark.sql import functions  # type: ignore[import-not-found]

    variable_codes = acs_variable_codes()
    aggregate_expressions = [
        functions.count(functions.lit(1)).alias("row_count"),
        functions.countDistinct("geoid").alias("distinct_tract_count"),
        functions.countDistinct("state").alias("state_count"),
        functions.countDistinct("source_snapshot_id").alias("snapshot_count"),
        functions.min("acs_release_year").alias("minimum_release_year"),
        functions.max("acs_release_year").alias("maximum_release_year"),
        _count_when(
            functions,
            functions.col("geoid").isNull()
            | (~functions.col("geoid").rlike("^[0-9]{11}$")),
            "invalid_geoid_count",
        ),
    ]
    for code in variable_codes:
        text_value = functions.trim(functions.col(code))
        numeric_value = text_value.cast("double")
        aggregate_expressions.extend(
            [
                _count_when(
                    functions,
                    functions.col(code).isNull() | (text_value == ""),
                    f"{code}__blank_count",
                ),
                _count_when(
                    functions,
                    numeric_value.isin([float(item) for item in ACS_SPECIAL_VALUES]),
                    f"{code}__special_value_count",
                ),
                _count_when(
                    functions,
                    functions.col(code).isNotNull()
                    & (text_value != "")
                    & numeric_value.isNull(),
                    f"{code}__parse_failure_count",
                ),
            ]
        )

    housing_units = _usable_acs_value(functions, "B25001_001E")
    occupied_units = _usable_acs_value(functions, "B25002_002E")
    vacant_units = _usable_acs_value(functions, "B25002_003E")
    tenure_total = _usable_acs_value(functions, "B25003_001E")
    owner_units = _usable_acs_value(functions, "B25003_002E")
    renter_units = _usable_acs_value(functions, "B25003_003E")
    structure_total = _usable_acs_value(functions, "B25024_001E")
    structure_parts = [
        _usable_acs_value(functions, f"B25024_{index:03d}E") for index in range(2, 12)
    ]
    structure_sum = structure_parts[0]
    for part in structure_parts[1:]:
        structure_sum = structure_sum + part

    aggregate_expressions.extend(
        [
            _count_when(
                functions,
                housing_units.isNotNull()
                & occupied_units.isNotNull()
                & vacant_units.isNotNull()
                & (functions.abs(housing_units - occupied_units - vacant_units) > 1),
                "housing_occupancy_balance_error_count",
            ),
            _count_when(
                functions,
                tenure_total.isNotNull()
                & owner_units.isNotNull()
                & renter_units.isNotNull()
                & (functions.abs(tenure_total - owner_units - renter_units) > 1),
                "tenure_balance_error_count",
            ),
            _count_when(
                functions,
                structure_total.isNotNull()
                & structure_sum.isNotNull()
                & (functions.abs(structure_total - structure_sum) > 1),
                "structure_balance_error_count",
            ),
        ]
    )
    summary = frame.agg(*aggregate_expressions).first().asDict()
    duplicate_key_count = (
        frame.groupBy("geoid", "acs_release_year")
        .count()
        .where(functions.col("count") > 1)
        .count()
    )

    metrics = [
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="volume",
            metric_name="row_count",
            value=summary["row_count"],
            status=_positive_status(summary["row_count"]),
            expectation="> 0",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="coverage",
            metric_name="distinct_tract_count",
            value=summary["distinct_tract_count"],
            status="info",
            expectation="monitored over time",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="coverage",
            metric_name="state_count",
            value=summary["state_count"],
            status="info",
            expectation="equals the requested pilot-state count",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="lineage",
            metric_name="snapshot_count",
            value=summary["snapshot_count"],
            status=_positive_status(summary["snapshot_count"]),
            expectation="> 0",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="time",
            metric_name="minimum_release_year",
            value=_number_or_zero(summary["minimum_release_year"]),
            status="info",
            expectation="monitored over time",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="time",
            metric_name="maximum_release_year",
            value=_number_or_zero(summary["maximum_release_year"]),
            status="info",
            expectation="monitored over time",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="integrity",
            metric_name="invalid_geoid_count",
            value=summary["invalid_geoid_count"],
            status=_zero_status(summary["invalid_geoid_count"]),
            expectation="= 0",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="integrity",
            metric_name="duplicate_tract_release_key_count",
            value=duplicate_key_count,
            status=_zero_status(duplicate_key_count),
            expectation="= 0",
        ),
    ]

    for metric_name in (
        "housing_occupancy_balance_error_count",
        "tenure_balance_error_count",
        "structure_balance_error_count",
    ):
        value = summary[metric_name]
        metrics.append(
            _metric(
                run_id=run_id,
                profiled_at_utc=profiled_at_utc,
                table_name=table_name,
                metric_group="internal_consistency",
                metric_name=metric_name,
                value=value,
                status=_zero_status(value, failure_status="warn"),
                expectation="= 0, allowing one-unit rounding differences",
            )
        )

    for code in variable_codes:
        for suffix, metric_group, failure_status, expectation in (
            ("blank_count", "missingness", "warn", "= 0 before documented missing policy"),
            (
                "special_value_count",
                "special_values",
                "info",
                "measured using Census-documented special values",
            ),
            ("parse_failure_count", "parseability", "fail", "= 0"),
        ):
            value = summary[f"{code}__{suffix}"]
            status = (
                "info"
                if failure_status == "info"
                else _zero_status(value, failure_status=failure_status)
            )
            metrics.append(
                _metric(
                    run_id=run_id,
                    profiled_at_utc=profiled_at_utc,
                    table_name=table_name,
                    metric_group=metric_group,
                    metric_name=suffix,
                    value=value,
                    status=status,
                    expectation=expectation,
                    dimension=f"column={code}",
                )
            )
    return metrics


def _profile_manifest(
    frame: Any,
    *,
    run_id: str,
    profiled_at_utc: str,
    table_name: str,
) -> list[QualityMetric]:
    from pyspark.sql import functions  # type: ignore[import-not-found]

    accepted_statuses = ("acquired", "registered", "bronze_validated")
    summary = (
        frame.agg(
            functions.count(functions.lit(1)).alias("row_count"),
            functions.countDistinct("snapshot_id").alias("distinct_snapshot_count"),
            functions.countDistinct("source_id").alias("distinct_source_count"),
            _count_when(
                functions,
                functions.col("sha256").isNull()
                | (~functions.col("sha256").rlike("^[a-f0-9]{64}$")),
                "invalid_sha256_count",
            ),
            _count_when(
                functions,
                functions.col("validation_status").isNull()
                | (~functions.col("validation_status").isin(*accepted_statuses)),
                "unexpected_status_count",
            ),
        )
        .first()
        .asDict()
    )
    return [
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="volume",
            metric_name="row_count",
            value=summary["row_count"],
            status=_positive_status(summary["row_count"]),
            expectation="> 0",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="lineage",
            metric_name="distinct_snapshot_count",
            value=summary["distinct_snapshot_count"],
            status=_positive_status(summary["distinct_snapshot_count"]),
            expectation="> 0",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="lineage",
            metric_name="distinct_source_count",
            value=summary["distinct_source_count"],
            status=_positive_status(summary["distinct_source_count"]),
            expectation="> 0",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="integrity",
            metric_name="invalid_sha256_count",
            value=summary["invalid_sha256_count"],
            status=_zero_status(summary["invalid_sha256_count"]),
            expectation="= 0",
        ),
        _metric(
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=table_name,
            metric_group="integrity",
            metric_name="unexpected_validation_status_count",
            value=summary["unexpected_status_count"],
            status=_zero_status(summary["unexpected_status_count"]),
            expectation=f"status in {accepted_statuses}",
        ),
    ]


def _profile_geography_match(
    fhfa: Any,
    acs: Any,
    *,
    run_id: str,
    profiled_at_utc: str,
    table_name: str,
) -> list[QualityMetric]:
    from pyspark.sql import functions  # type: ignore[import-not-found]

    fhfa_keys = (
        fhfa.select(
            functions.col("tract").alias("geoid"),
            functions.col("year").alias("acs_release_year"),
            functions.when(functions.col("hpi").isNotNull(), 1)
            .otherwise(0)
            .alias("has_usable_hpi"),
        )
        .where(functions.col("geoid").isNotNull())
        .groupBy("geoid", "acs_release_year")
        .agg(functions.max("has_usable_hpi").alias("has_usable_hpi"))
        .withColumn("has_same_year_fhfa", functions.lit(1))
    )
    acs_keys = acs.select("geoid", "state", "acs_release_year").distinct()
    matched = acs_keys.join(fhfa_keys, ["geoid", "acs_release_year"], "left")
    by_state = matched.groupBy("state").agg(
        functions.count(functions.lit(1)).alias("acs_tract_count"),
        functions.sum(
            functions.coalesce(functions.col("has_same_year_fhfa"), functions.lit(0))
        ).alias("matched_tract_count"),
        functions.sum(
            functions.coalesce(functions.col("has_usable_hpi"), functions.lit(0))
        ).alias("usable_hpi_count"),
    )
    state_rows = by_state.collect()
    total_acs = sum(int(row["acs_tract_count"]) for row in state_rows)
    total_matched = sum(int(row["matched_tract_count"]) for row in state_rows)
    total_usable_hpi = sum(int(row["usable_hpi_count"]) for row in state_rows)

    metrics: list[QualityMetric] = []
    for state, acs_count, matched_count, usable_hpi_count in [
        ("all", total_acs, total_matched, total_usable_hpi),
        *[
            (
                str(row["state"]),
                int(row["acs_tract_count"]),
                int(row["matched_tract_count"]),
                int(row["usable_hpi_count"]),
            )
            for row in state_rows
        ],
    ]:
        match_rate = matched_count / acs_count if acs_count else 0.0
        usable_hpi_rate = usable_hpi_count / acs_count if acs_count else 0.0
        metrics.extend(
            [
                _metric(
                    run_id=run_id,
                    profiled_at_utc=profiled_at_utc,
                    table_name=table_name,
                    metric_group="geography_match",
                    metric_name="acs_tract_count",
                    value=acs_count,
                    status="info",
                    expectation="monitored before geography harmonization",
                    dimension=f"state={state}",
                ),
                _metric(
                    run_id=run_id,
                    profiled_at_utc=profiled_at_utc,
                    table_name=table_name,
                    metric_group="geography_match",
                    metric_name="same_year_fhfa_match_count",
                    value=matched_count,
                    status="info",
                    expectation="descriptive coverage, not a pass/fail threshold",
                    dimension=f"state={state}",
                ),
                _metric(
                    run_id=run_id,
                    profiled_at_utc=profiled_at_utc,
                    table_name=table_name,
                    metric_group="geography_match",
                    metric_name="same_year_fhfa_match_rate",
                    value=match_rate,
                    status="info",
                    expectation="descriptive coverage, not a pass/fail threshold",
                    dimension=f"state={state}",
                    notes="ACS release year matched to the same FHFA observation year.",
                ),
                _metric(
                    run_id=run_id,
                    profiled_at_utc=profiled_at_utc,
                    table_name=table_name,
                    metric_group="geography_match",
                    metric_name="same_year_usable_hpi_count",
                    value=usable_hpi_count,
                    status="info",
                    expectation="descriptive target coverage, not a pass/fail threshold",
                    dimension=f"state={state}",
                ),
                _metric(
                    run_id=run_id,
                    profiled_at_utc=profiled_at_utc,
                    table_name=table_name,
                    metric_group="geography_match",
                    metric_name="same_year_usable_hpi_rate",
                    value=usable_hpi_rate,
                    status="info",
                    expectation="descriptive target coverage, not a pass/fail threshold",
                    dimension=f"state={state}",
                    notes="A matching FHFA row exists and its HPI value is not null.",
                ),
            ]
        )
    return metrics


def profile_bronze_tables(
    spark: Any,
    *,
    catalog: str,
    schema: str,
    profiled_at: datetime | None = None,
) -> list[QualityMetric]:
    """Profile the current bronze tables and return persisted-ready metrics."""

    run_id, profiled_at_utc = new_quality_run_id(profiled_at)
    fhfa_name = f"{catalog}.{schema}.bronze_fhfa_tract_hpi"
    acs_name = f"{catalog}.{schema}.bronze_acs5_tract"
    manifest_name = f"{catalog}.{schema}.source_snapshot_manifest"
    for table_name in (fhfa_name, acs_name, manifest_name):
        if not spark.catalog.tableExists(table_name):
            raise ValueError(f"Required bronze table does not exist: {table_name}")

    fhfa = spark.table(fhfa_name)
    acs = spark.table(acs_name)
    manifest = spark.table(manifest_name)
    metrics = [
        *_profile_fhfa(
            fhfa,
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=fhfa_name,
        ),
        *_profile_acs(
            acs,
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=acs_name,
        ),
        *_profile_manifest(
            manifest,
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=manifest_name,
        ),
        *_profile_geography_match(
            fhfa,
            acs,
            run_id=run_id,
            profiled_at_utc=profiled_at_utc,
            table_name=f"{fhfa_name}__to__{acs_name}",
        ),
    ]
    failure_count = len(hard_failures(metrics))
    warning_count = sum(metric.status == "warn" for metric in metrics)
    metrics.extend(
        [
            _metric(
                run_id=run_id,
                profiled_at_utc=profiled_at_utc,
                table_name=f"{catalog}.{schema}",
                metric_group="run_summary",
                metric_name="failure_count",
                value=failure_count,
                status=_zero_status(failure_count),
                expectation="= 0",
            ),
            _metric(
                run_id=run_id,
                profiled_at_utc=profiled_at_utc,
                table_name=f"{catalog}.{schema}",
                metric_group="run_summary",
                metric_name="warning_count",
                value=warning_count,
                status="pass" if warning_count == 0 else "warn",
                expectation="review every nonzero warning count",
            ),
        ]
    )
    return metrics


def write_quality_metrics(
    spark: Any,
    metrics: list[QualityMetric],
    *,
    catalog: str,
    schema: str,
    table: str = "bronze_quality_metrics",
) -> str:
    """Append one profiling run to the governed quality-metrics Delta table."""

    if not metrics:
        raise ValueError("At least one quality metric is required")
    from pyspark.sql.types import (  # type: ignore[import-not-found]
        DoubleType,
        StringType,
        StructField,
        StructType,
    )

    metric_schema = StructType(
        [
            StructField("quality_run_id", StringType(), False),
            StructField("profiled_at_utc", StringType(), False),
            StructField("table_name", StringType(), False),
            StructField("metric_group", StringType(), False),
            StructField("metric_name", StringType(), False),
            StructField("dimension", StringType(), False),
            StructField("metric_value", DoubleType(), False),
            StructField("status", StringType(), False),
            StructField("expectation", StringType(), False),
            StructField("notes", StringType(), False),
        ]
    )
    table_name = qualified_name(catalog, schema, table)
    spark.createDataFrame(
        [metric.to_spark_record() for metric in metrics], schema=metric_schema
    ).write.format("delta").mode("append").saveAsTable(table_name)
    return table_name

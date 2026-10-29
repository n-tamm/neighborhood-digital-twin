"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Reusable data-readiness summaries for coverage, uncertainty, history, and target feasibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import reduce
from typing import Any

from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.validate import QualityMetric, hard_failures, new_quality_run_id

STATE_COVERAGE_TABLE = "gold_eda_state_coverage"
ACS_QUALITY_TABLE = "gold_eda_acs_measure_quality"
FHFA_HISTORY_TABLE = "gold_eda_fhfa_history"
HORIZON_FEASIBILITY_TABLE = "gold_eda_horizon_feasibility"
READINESS_QUALITY_TABLE = "eda_readiness_quality_metrics"
READINESS_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class ReadinessBuild:
    """Validated EDA summary frames that have not yet been published."""

    build_id: str
    built_at_utc: str
    frames: dict[str, Any]
    metrics: list[QualityMetric]


def validate_horizons(horizons: tuple[int, ...]) -> tuple[int, ...]:
    """Return distinct, ordered positive forecast horizons."""

    if not horizons:
        raise ValueError("At least one forecast horizon is required")
    if any(not isinstance(horizon, int) or horizon <= 0 for horizon in horizons):
        raise ValueError("Forecast horizons must be positive integers")
    if len(horizons) != len(set(horizons)):
        raise ValueError("Forecast horizons must not contain duplicates")
    return tuple(sorted(horizons))


def _lineage(frame: Any, *, build_id: str, built_at_utc: str) -> Any:
    """Attach readiness schema and build lineage to a Spark summary frame."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        frame.withColumn("readiness_schema_version", functions.lit(READINESS_SCHEMA_VERSION))
        .withColumn("readiness_build_id", functions.lit(build_id))
        .withColumn(
            "readiness_built_at_utc", functions.to_timestamp(functions.lit(built_at_utc))
        )
    )


def _state_coverage(profile: Any, *, build_id: str, built_at_utc: str) -> Any:
    """Summarize source and product eligibility counts by state."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    summary = profile.groupBy("state_fips").agg(
        functions.first("state_abbreviation", ignorenulls=True).alias("state_abbreviation"),
        functions.first("state_name", ignorenulls=True).alias("state_name"),
        functions.count("geoid_2020").alias("canonical_tract_count"),
        functions.sum(functions.col("has_display_geometry").cast("int")).alias(
            "display_geometry_tract_count"
        ),
        functions.sum(functions.col("has_current_acs_profile").cast("int")).alias(
            "current_acs_tract_count"
        ),
        functions.sum(functions.col("has_fhfa_history").cast("int")).alias(
            "fhfa_history_tract_count"
        ),
        functions.sum(functions.col("similarity_candidate").cast("int")).alias(
            "similarity_candidate_count"
        ),
        functions.sum(functions.col("forecast_candidate").cast("int")).alias(
            "forecast_candidate_count"
        ),
    )
    denominator = functions.col("canonical_tract_count")
    for count_column in (
        "display_geometry_tract_count",
        "current_acs_tract_count",
        "fhfa_history_tract_count",
        "similarity_candidate_count",
        "forecast_candidate_count",
    ):
        summary = summary.withColumn(
            count_column.replace("_count", "_share"),
            functions.when(denominator > 0, functions.col(count_column) / denominator),
        )
    return _lineage(summary, build_id=build_id, built_at_utc=built_at_utc)


def _acs_measure_quality(acs: Any, *, build_id: str, built_at_utc: str) -> Any:
    """Summarize current ACS availability and sampling uncertainty by measure."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    latest_release = int(acs.agg(functions.max("acs_release_year")).first()[0])
    current = acs.where(functions.col("acs_release_year") == latest_release)
    summary = current.groupBy(
        "measure_order", "measure_name", "measure_label", "universe", "unit"
    ).agg(
        functions.count(functions.lit(1)).alias("tract_count"),
        functions.count("estimate").alias("available_estimate_count"),
        functions.sum(functions.col("estimate").isNull().cast("int")).alias(
            "missing_estimate_count"
        ),
        functions.sum((functions.col("relative_margin_of_error") > 0.5).cast("int")).alias(
            "relative_moe_over_50_percent_count"
        ),
        functions.expr("percentile_approx(relative_margin_of_error, 0.5, 10000)").alias(
            "median_relative_margin_of_error"
        ),
        functions.expr("percentile_approx(relative_margin_of_error, 0.9, 10000)").alias(
            "p90_relative_margin_of_error"
        ),
    )
    summary = (
        summary.withColumn("acs_release_year", functions.lit(latest_release))
        .withColumn(
            "missing_estimate_share",
            functions.col("missing_estimate_count") / functions.col("tract_count"),
        )
        .withColumn(
            "relative_moe_over_50_percent_share",
            functions.col("relative_moe_over_50_percent_count") / functions.col("tract_count"),
        )
    )
    return _lineage(summary, build_id=build_id, built_at_utc=built_at_utc)


def _fhfa_history(fhfa: Any, *, build_id: str, built_at_utc: str) -> Any:
    """Summarize usable FHFA history depth and coverage by state."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    by_tract = fhfa.groupBy("state_fips", "state_abbr", "geoid").agg(
        functions.count(functions.lit(1)).alias("source_row_count"),
        functions.count("hpi").alias("usable_hpi_year_count"),
        functions.min(
            functions.when(functions.col("hpi_available"), functions.col("observation_year"))
        ).alias("first_usable_hpi_year"),
        functions.max(
            functions.when(functions.col("hpi_available"), functions.col("observation_year"))
        ).alias("last_usable_hpi_year"),
    )
    summary = by_tract.groupBy("state_fips", "state_abbr").agg(
        functions.count("geoid").alias("source_tract_count"),
        functions.sum((functions.col("usable_hpi_year_count") > 0).cast("int")).alias(
            "usable_hpi_tract_count"
        ),
        functions.expr("percentile_approx(usable_hpi_year_count, 0.1, 10000)").alias(
            "p10_usable_hpi_year_count"
        ),
        functions.expr("percentile_approx(usable_hpi_year_count, 0.5, 10000)").alias(
            "median_usable_hpi_year_count"
        ),
        functions.expr("percentile_approx(usable_hpi_year_count, 0.9, 10000)").alias(
            "p90_usable_hpi_year_count"
        ),
        functions.min("first_usable_hpi_year").alias("earliest_usable_hpi_year"),
        functions.max("last_usable_hpi_year").alias("latest_usable_hpi_year"),
    )
    return _lineage(summary, build_id=build_id, built_at_utc=built_at_utc)


def _horizon_feasibility(
    fhfa: Any,
    *,
    horizons: tuple[int, ...],
    build_id: str,
    built_at_utc: str,
) -> Any:
    """Count usable tract-origin outcomes for each requested forecast horizon."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    usable = fhfa.where(functions.col("hpi_available") & (functions.col("hpi") > 0)).select(
        "state_fips", "geoid", "observation_year", "hpi"
    )
    pairs = []
    for horizon in horizons:
        origin = usable.alias("origin")
        future = usable.alias("future")
        pairs.append(
            origin.join(
                future,
                (functions.col("origin.geoid") == functions.col("future.geoid"))
                & (
                    functions.col("future.observation_year")
                    == functions.col("origin.observation_year") + horizon
                ),
                "inner",
            ).select(
                functions.col("origin.state_fips").alias("state_fips"),
                functions.col("origin.geoid").alias("geoid"),
                functions.col("origin.observation_year").alias("forecast_origin_year"),
                functions.lit(horizon).alias("horizon_years"),
                (
                    functions.pow(
                        functions.col("future.hpi") / functions.col("origin.hpi"),
                        functions.lit(1.0 / horizon),
                    )
                    - 1
                ).alias("annualized_hpi_change"),
            )
        )
    paired = reduce(lambda left, right: left.unionByName(right), pairs)
    summary = paired.groupBy("state_fips", "horizon_years").agg(
        functions.count(functions.lit(1)).alias("tract_origin_pair_count"),
        functions.countDistinct("geoid").alias("tract_count"),
        functions.min("forecast_origin_year").alias("earliest_forecast_origin_year"),
        functions.max("forecast_origin_year").alias("latest_forecast_origin_year"),
        functions.expr("percentile_approx(annualized_hpi_change, 0.1, 10000)").alias(
            "p10_annualized_hpi_change"
        ),
        functions.expr("percentile_approx(annualized_hpi_change, 0.5, 10000)").alias(
            "median_annualized_hpi_change"
        ),
        functions.expr("percentile_approx(annualized_hpi_change, 0.9, 10000)").alias(
            "p90_annualized_hpi_change"
        ),
    )
    return _lineage(summary, build_id=build_id, built_at_utc=built_at_utc)


def _metrics(
    frames: dict[str, Any], *, build_id: str, built_at_utc: str, catalog: str, schema: str
) -> list[QualityMetric]:
    """Validate readiness-summary row counts and natural-key uniqueness."""

    metrics = []
    key_columns = {
        STATE_COVERAGE_TABLE: ("state_fips",),
        ACS_QUALITY_TABLE: ("measure_name",),
        FHFA_HISTORY_TABLE: ("state_fips",),
        HORIZON_FEASIBILITY_TABLE: ("state_fips", "horizon_years"),
    }
    for table, frame in frames.items():
        row_count = frame.count()
        duplicate_count = row_count - frame.select(*key_columns[table]).distinct().count()
        for metric_name, value, status in (
            ("row_count", row_count, "pass" if row_count > 0 else "fail"),
            ("duplicate_key_count", duplicate_count, "pass" if duplicate_count == 0 else "fail"),
        ):
            metrics.append(
                QualityMetric(
                    quality_run_id=build_id,
                    profiled_at_utc=built_at_utc,
                    table_name=f"{catalog}.{schema}.{table}",
                    metric_group="readiness",
                    metric_name=metric_name,
                    dimension="all",
                    metric_value=float(value),
                    status=status,
                    expectation="> 0" if metric_name == "row_count" else "= 0",
                    notes="EDA checkpoint publication check.",
                )
            )
        if table == FHFA_HISTORY_TABLE:
            from pyspark.sql import functions  # type: ignore[import-not-found]

            types = dict(frame.dtypes)
            type_mismatch_count = sum(
                types[column] not in {"int", "bigint"}
                for column in ("earliest_usable_hpi_year", "latest_usable_hpi_year")
            )
            invalid_range_count = frame.where(
                functions.col("earliest_usable_hpi_year").isNull()
                | functions.col("latest_usable_hpi_year").isNull()
                | (
                    functions.col("earliest_usable_hpi_year")
                    > functions.col("latest_usable_hpi_year")
                )
            ).count()
            for metric_name, value in (
                ("year_type_mismatch_count", type_mismatch_count),
                ("invalid_year_range_count", invalid_range_count),
            ):
                metrics.append(
                    QualityMetric(
                        quality_run_id=build_id,
                        profiled_at_utc=built_at_utc,
                        table_name=f"{catalog}.{schema}.{table}",
                        metric_group="readiness",
                        metric_name=metric_name,
                        dimension="all",
                        metric_value=float(value),
                        status="pass" if value == 0 else "fail",
                        expectation="= 0",
                        notes="FHFA history-year contract check.",
                    )
                )
    return metrics


def prepare_readiness_build(
    spark: Any,
    *,
    catalog: str,
    silver_schema: str,
    gold_schema: str,
    horizons: tuple[int, ...] = (1, 3, 5),
    built_at: datetime | None = None,
) -> ReadinessBuild:
    """Build the first formal EDA checkpoint from governed silver and gold inputs."""

    horizons = validate_horizons(horizons)
    profile = spark.table(f"{catalog}.{gold_schema}.gold_tract_profile_current")
    acs = spark.table(f"{catalog}.{silver_schema}.silver_acs_tract_measure")
    fhfa = spark.table(f"{catalog}.{silver_schema}.silver_fhfa_tract_year")
    build_id, built_at_utc = new_quality_run_id(built_at)
    frames = {
        STATE_COVERAGE_TABLE: _state_coverage(
            profile, build_id=build_id, built_at_utc=built_at_utc
        ),
        ACS_QUALITY_TABLE: _acs_measure_quality(
            acs, build_id=build_id, built_at_utc=built_at_utc
        ),
        FHFA_HISTORY_TABLE: _fhfa_history(fhfa, build_id=build_id, built_at_utc=built_at_utc),
        HORIZON_FEASIBILITY_TABLE: _horizon_feasibility(
            fhfa,
            horizons=horizons,
            build_id=build_id,
            built_at_utc=built_at_utc,
        ),
    }
    metrics = _metrics(
        frames,
        build_id=build_id,
        built_at_utc=built_at_utc,
        catalog=catalog,
        schema=gold_schema,
    )
    return ReadinessBuild(build_id, built_at_utc, frames, metrics)


def publish_readiness_build(
    build: ReadinessBuild, *, catalog: str, schema: str
) -> tuple[str, ...]:
    """Publish EDA summaries only after their keys and row counts pass checks."""

    failures = hard_failures(build.metrics)
    if failures:
        raise ValueError(
            "EDA readiness build has hard failures: "
            + ", ".join(f"{item.table_name}:{item.metric_name}" for item in failures)
        )
    published = []
    for table, frame in build.frames.items():
        name = qualified_name(catalog, schema, table)
        (
            frame.write.format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(name)
        )
        published.append(name)
    return tuple(published)

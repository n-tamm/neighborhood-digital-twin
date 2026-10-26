"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Historical gold state, tract-coverage, and forecast-target products.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import reduce
from typing import Any

from neighborhood_twin.connecticut import CONNECTICUT_BRIDGE_TABLE
from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.geography import TRACT_RELATIONSHIP_SILVER_TABLE
from neighborhood_twin.products import ACS_PROFILE_COLUMNS
from neighborhood_twin.validate import QualityMetric, hard_failures, new_quality_run_id

HISTORICAL_SCHEMA_VERSION = "1.0.0"
HISTORICAL_COVERAGE_TABLE = "gold_historical_tract_coverage"
HISTORICAL_STATE_TABLE = "gold_neighborhood_state_historical"
HISTORICAL_TARGET_TABLE = "gold_forecast_target_historical"
HISTORICAL_QUALITY_TABLE = "gold_quality_metrics"
DEFAULT_FORECAST_HORIZONS = (1, 3, 5)
ACS_PUBLICATION_LAG_YEARS = 1

HISTORICAL_STATE_COLUMNS = (
    "geoid_2020",
    "acs_source_geoid",
    "state_fips",
    "state_abbreviation",
    "state_name",
    "county_geoid",
    "county_name",
    "tract_code",
    "tract_name",
    "division_code",
    "division_name",
    "region_code",
    "region_name",
    "country_code",
    "country_name",
    "acs_release_year",
    "acs_available_year",
    "acs_survey_start_year",
    "acs_survey_end_year",
    "acs_reference_period",
    "source_geography_vintage",
    "geography_alignment_method",
    *tuple(
        column
        for column in ACS_PROFILE_COLUMNS
        if column not in {"acs_release_year", "acs_reference_period"}
    ),
    "source_snapshot_id",
    "source_retrieval_timestamp_utc",
    "historical_schema_version",
    "historical_build_id",
    "historical_built_at_utc",
)


@dataclass(frozen=True)
class HistoricalBuild:
    """Validated historical gold frames and their unpublished quality metrics."""

    build_id: str
    built_at_utc: str
    frames: dict[str, Any]
    metrics: list[QualityMetric]


def acs_available_year(release_year: int) -> int:
    """Return the conservative calendar year when an ACS five-year release is usable."""

    if release_year < 2009:
        raise ValueError("ACS five-year release years must be 2009 or later")
    return release_year + ACS_PUBLICATION_LAG_YEARS


def validate_forecast_horizons(horizons: tuple[int, ...]) -> tuple[int, ...]:
    """Return distinct, ordered, positive forecast horizons."""

    if not horizons:
        raise ValueError("At least one forecast horizon is required")
    if any(not isinstance(horizon, int) or horizon <= 0 for horizon in horizons):
        raise ValueError("Forecast horizons must be positive integers")
    if len(horizons) != len(set(horizons)):
        raise ValueError("Forecast horizons must not contain duplicates")
    return tuple(sorted(horizons))


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
    """Create one consistently shaped historical-product quality metric."""

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


def _lineage(frame: Any, *, build_id: str, built_at_utc: str) -> Any:
    """Attach the historical schema version and build lineage to a Spark frame."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        frame.withColumn(
            "historical_schema_version", functions.lit(HISTORICAL_SCHEMA_VERSION)
        )
        .withColumn("historical_build_id", functions.lit(build_id))
        .withColumn(
            "historical_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
    )


def _align_acs_geography(
    acs: Any,
    relationship: Any,
    connecticut_bridge: Any,
    hierarchy: Any,
) -> Any:
    """Classify and map ACS tract releases onto the supported 2020 tract framework."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    stable = (
        relationship.where(functions.col("is_stable_measure_mapping"))
        .select(
            functions.col("geoid_2010").alias("stable_source_geoid"),
            functions.col("geoid_2020").alias("stable_target_geoid"),
        )
        .distinct()
    )
    relationship_sources = (
        relationship.select(functions.col("geoid_2010").alias("relationship_source_geoid"))
        .distinct()
        .withColumn("has_2010_2020_relationship", functions.lit(True))
    )
    bridge = connecticut_bridge.select(
        functions.col("geoid_current").alias("connecticut_source_geoid"),
        functions.col("geoid_2020").alias("connecticut_target_geoid"),
    )
    canonical = hierarchy.select(
        "geoid_2020",
        "state_fips",
        "state_abbreviation",
        "state_name",
        "county_geoid",
        "county_name",
        "tract_code",
        "tract_name",
        "division_code",
        "division_name",
        "region_code",
        "region_name",
        "country_code",
        "country_name",
    ).alias("canonical")

    aligned = (
        acs.withColumnRenamed("geoid", "acs_source_geoid")
        .withColumnRenamed("state_fips", "acs_source_state_fips")
        .withColumnRenamed("county_geoid", "acs_source_county_geoid")
        .withColumnRenamed("tract_name", "acs_source_tract_name")
        .join(
            stable,
            functions.col("acs_source_geoid") == functions.col("stable_source_geoid"),
            "left",
        )
        .join(
            relationship_sources,
            functions.col("acs_source_geoid")
            == functions.col("relationship_source_geoid"),
            "left",
        )
        .join(
            bridge,
            functions.col("acs_source_geoid")
            == functions.col("connecticut_source_geoid"),
            "left",
        )
        .withColumn(
            "candidate_geoid_2020",
            functions.when(
                functions.col("source_geography_vintage") == "2010",
                functions.col("stable_target_geoid"),
            ).otherwise(
                functions.coalesce(
                    functions.col("connecticut_target_geoid"),
                    functions.col("acs_source_geoid"),
                )
            ),
        )
        .join(
            canonical,
            functions.col("candidate_geoid_2020")
            == functions.col("canonical.geoid_2020"),
            "left",
        )
        .withColumn(
            "geography_alignment_method",
            functions.when(
                (functions.col("source_geography_vintage") == "2010")
                & functions.col("stable_target_geoid").isNotNull()
                & functions.col("canonical.geoid_2020").isNotNull(),
                functions.lit("stable_2010_to_2020"),
            )
            .when(
                (functions.col("source_geography_vintage") == "2010")
                & functions.col("has_2010_2020_relationship").isNotNull(),
                functions.lit("changed_2010_tract_not_harmonized"),
            )
            .when(
                functions.col("source_geography_vintage") == "2010",
                functions.lit("missing_2010_to_2020_relationship"),
            )
            .when(
                (functions.col("source_geography_vintage") == "2020")
                & functions.col("connecticut_target_geoid").isNotNull()
                & functions.col("canonical.geoid_2020").isNotNull(),
                functions.lit("connecticut_current_to_2020_bridge"),
            )
            .when(
                (functions.col("source_geography_vintage") == "2020")
                & functions.col("canonical.geoid_2020").isNotNull(),
                functions.lit("direct_2020_geography"),
            )
            .when(
                functions.col("source_geography_vintage") == "2020",
                functions.lit("missing_supported_2020_geography"),
            )
            .otherwise(functions.lit("unsupported_source_geography_vintage")),
        )
        .withColumn(
            "geography_alignment_eligible",
            functions.col("geography_alignment_method").isin(
                "stable_2010_to_2020",
                "connecticut_current_to_2020_bridge",
                "direct_2020_geography",
            ),
        )
        .withColumn(
            "acs_available_year",
            functions.col("acs_release_year") + functions.lit(ACS_PUBLICATION_LAG_YEARS),
        )
    )
    return aligned


def _build_coverage(aligned: Any, *, build_id: str, built_at_utc: str) -> Any:
    """Summarize release-level tract retention for every alignment outcome."""

    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    summary = aligned.groupBy(
        "acs_release_year",
        "acs_available_year",
        "source_geography_vintage",
        "geography_alignment_method",
        "geography_alignment_eligible",
    ).agg(
        functions.count(functions.lit(1)).alias("source_row_count"),
        functions.countDistinct("acs_source_geoid").alias("source_tract_count"),
        functions.countDistinct("canonical.geoid_2020").alias("canonical_tract_count"),
    )
    release_window = Window.partitionBy("acs_release_year")
    return _lineage(
        summary.withColumn(
            "release_source_tract_count",
            functions.sum("source_tract_count").over(release_window),
        ).withColumn(
            "source_tract_share",
            functions.col("source_tract_count")
            / functions.col("release_source_tract_count"),
        ),
        build_id=build_id,
        built_at_utc=built_at_utc,
    )


def _build_historical_state(aligned: Any, *, build_id: str, built_at_utc: str) -> Any:
    """Publish eligible ACS state rows using canonical 2020 tract identities."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    state = (
        aligned.where(functions.col("geography_alignment_eligible"))
        .select(
            functions.col("canonical.geoid_2020").alias("geoid_2020"),
            "acs_source_geoid",
            functions.col("canonical.state_fips").alias("state_fips"),
            "state_abbreviation",
            "state_name",
            functions.col("canonical.county_geoid").alias("county_geoid"),
            "county_name",
            "tract_code",
            functions.col("canonical.tract_name").alias("tract_name"),
            "division_code",
            "division_name",
            "region_code",
            "region_name",
            "country_code",
            "country_name",
            "acs_release_year",
            "acs_available_year",
            "acs_survey_start_year",
            "acs_survey_end_year",
            "acs_reference_period",
            "source_geography_vintage",
            "geography_alignment_method",
            *tuple(
                column
                for column in ACS_PROFILE_COLUMNS
                if column not in {"acs_release_year", "acs_reference_period"}
            ),
            "source_snapshot_id",
            "source_retrieval_timestamp_utc",
        )
    )
    return _lineage(state, build_id=build_id, built_at_utc=built_at_utc).select(
        *HISTORICAL_STATE_COLUMNS
    )


def _align_fhfa_geography(fhfa: Any, connecticut_bridge: Any, hierarchy: Any) -> Any:
    """Map FHFA source identifiers onto supported canonical 2020 tracts."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    bridge = connecticut_bridge.select(
        functions.col("geoid_current").alias("connecticut_source_geoid"),
        functions.col("geoid_2020").alias("connecticut_target_geoid"),
    )
    canonical = hierarchy.select(
        "geoid_2020",
        "state_fips",
        "state_abbreviation",
        "state_name",
        "county_geoid",
        "county_name",
        "region_code",
        "region_name",
        "division_code",
        "division_name",
    ).alias("canonical")
    return (
        fhfa.withColumnRenamed("geoid", "fhfa_source_geoid")
        .withColumnRenamed("state_fips", "fhfa_source_state_fips")
        .withColumnRenamed("state_abbr", "fhfa_source_state_abbreviation")
        .join(
            bridge,
            functions.col("fhfa_source_geoid")
            == functions.col("connecticut_source_geoid"),
            "left",
        )
        .withColumn(
            "candidate_geoid_2020",
            functions.coalesce(
                functions.col("connecticut_target_geoid"),
                functions.col("fhfa_source_geoid"),
            ),
        )
        .join(
            canonical,
            functions.col("candidate_geoid_2020")
            == functions.col("canonical.geoid_2020"),
            "inner",
        )
    )


def _one_horizon_target(fhfa: Any, horizon: int) -> Any:
    """Construct observed and censored FHFA outcomes for one forecast horizon."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    origins = (
        fhfa.where(functions.col("hpi_available") & (functions.col("hpi") > 0))
        .select(
            functions.col("canonical.geoid_2020").alias("geoid_2020"),
            functions.col("fhfa_source_geoid").alias("origin_fhfa_source_geoid"),
            functions.col("canonical.state_fips").alias("state_fips"),
            functions.col("canonical.state_abbreviation").alias("state_abbreviation"),
            functions.col("canonical.state_name").alias("state_name"),
            functions.col("canonical.county_geoid").alias("county_geoid"),
            functions.col("canonical.county_name").alias("county_name"),
            functions.col("canonical.region_code").alias("region_code"),
            functions.col("canonical.region_name").alias("region_name"),
            functions.col("canonical.division_code").alias("division_code"),
            functions.col("canonical.division_name").alias("division_name"),
            functions.col("observation_year").alias("forecast_origin_year"),
            functions.col("hpi").alias("origin_hpi"),
            functions.col("annual_change_pct").alias("origin_annual_change_pct"),
            functions.col("source_snapshot_id").alias("origin_source_snapshot_id"),
        )
        .alias("origin")
    )
    endpoints = fhfa.select(
        functions.col("canonical.geoid_2020").alias("endpoint_geoid_2020"),
        functions.col("observation_year").alias("endpoint_observation_year"),
        functions.col("hpi").alias("target_end_hpi"),
        functions.col("hpi_available").alias("target_end_hpi_available"),
        functions.col("source_snapshot_id").alias("target_end_source_snapshot_id"),
    ).alias("endpoint")
    joined = origins.join(
        endpoints,
        (functions.col("origin.geoid_2020") == functions.col("endpoint_geoid_2020"))
        & (
            functions.col("endpoint_observation_year")
            == functions.col("forecast_origin_year") + functions.lit(horizon)
        ),
        "left",
    )
    target_observed = functions.coalesce(
        functions.col("target_end_hpi_available") & (functions.col("target_end_hpi") > 0),
        functions.lit(False),
    )
    cumulative_log_change = functions.when(
        target_observed,
        functions.log(functions.col("target_end_hpi") / functions.col("origin_hpi")),
    )
    return joined.select(
        functions.col("origin.geoid_2020").alias("geoid_2020"),
        "origin_fhfa_source_geoid",
        "state_fips",
        "state_abbreviation",
        "state_name",
        "county_geoid",
        "county_name",
        "region_code",
        "region_name",
        "division_code",
        "division_name",
        "forecast_origin_year",
        functions.lit(horizon).cast("int").alias("horizon_years"),
        (functions.col("forecast_origin_year") + functions.lit(horizon)).alias(
            "target_end_year"
        ),
        "origin_hpi",
        "origin_annual_change_pct",
        "target_end_hpi",
        cumulative_log_change.alias("target_cumulative_log_change"),
        functions.when(
            target_observed,
            (functions.exp(cumulative_log_change / functions.lit(horizon)) - 1) * 100,
        ).alias("target_annualized_change_pct"),
        target_observed.alias("target_is_observed"),
        functions.when(
            functions.col("endpoint_observation_year").isNull(),
            functions.lit("missing_target_year_row"),
        )
        .when(~target_observed, functions.lit("missing_or_nonpositive_target_hpi"))
        .otherwise(functions.lit(None).cast("string"))
        .alias("target_censor_reason"),
        "origin_source_snapshot_id",
        "target_end_source_snapshot_id",
    )


def _build_historical_targets(
    fhfa: Any,
    *,
    horizons: tuple[int, ...],
    build_id: str,
    built_at_utc: str,
) -> Any:
    """Combine direct horizon-specific FHFA target contracts."""

    target_frames = [_one_horizon_target(fhfa, horizon) for horizon in horizons]
    return _lineage(
        reduce(lambda left, right: left.unionByName(right), target_frames),
        build_id=build_id,
        built_at_utc=built_at_utc,
    )


def _quality_metrics(
    frames: dict[str, Any],
    *,
    horizons: tuple[int, ...],
    build_id: str,
    built_at_utc: str,
    catalog: str,
    schema: str,
) -> list[QualityMetric]:
    """Validate historical table keys, coverage, timing, and target censoring."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    keys = {
        HISTORICAL_COVERAGE_TABLE: (
            "acs_release_year",
            "geography_alignment_method",
        ),
        HISTORICAL_STATE_TABLE: ("geoid_2020", "acs_release_year"),
        HISTORICAL_TARGET_TABLE: (
            "geoid_2020",
            "forecast_origin_year",
            "horizon_years",
        ),
    }
    metrics: list[QualityMetric] = []
    for table, frame in frames.items():
        row_count = frame.count()
        duplicate_count = row_count - frame.select(*keys[table]).distinct().count()
        for metric_name, value, status, expectation in (
            ("row_count", row_count, "pass" if row_count > 0 else "fail", "> 0"),
            (
                "duplicate_key_count",
                duplicate_count,
                "pass" if duplicate_count == 0 else "fail",
                "= 0",
            ),
        ):
            metrics.append(
                _metric(
                    build_id=build_id,
                    built_at_utc=built_at_utc,
                    table_name=f"{catalog}.{schema}.{table}",
                    metric_group="historical_products",
                    metric_name=metric_name,
                    value=value,
                    status=status,
                    expectation=expectation,
                )
            )

    coverage = frames[HISTORICAL_COVERAGE_TABLE]
    state = frames[HISTORICAL_STATE_TABLE]
    targets = frames[HISTORICAL_TARGET_TABLE]
    release_count = coverage.select("acs_release_year").distinct().count()
    invalid_state_alignment_count = state.where(
        ~functions.col("geography_alignment_method").isin(
            "stable_2010_to_2020",
            "connecticut_current_to_2020_bridge",
            "direct_2020_geography",
        )
    ).count()
    pre_2020_nonstable_count = state.where(
        (functions.col("acs_release_year") < 2020)
        & (functions.col("geography_alignment_method") != "stable_2010_to_2020")
    ).count()
    invalid_availability_count = state.where(
        functions.col("acs_available_year")
        != functions.col("acs_release_year") + ACS_PUBLICATION_LAG_YEARS
    ).count()
    target_horizons = tuple(
        int(row["horizon_years"])
        for row in targets.select("horizon_years").distinct().orderBy("horizon_years").collect()
    )
    invalid_target_timing_count = targets.where(
        functions.col("target_end_year")
        != functions.col("forecast_origin_year") + functions.col("horizon_years")
    ).count()
    invalid_observed_target_count = targets.where(
        functions.col("target_is_observed")
        & (
            functions.col("target_cumulative_log_change").isNull()
            | functions.col("target_annualized_change_pct").isNull()
            | functions.col("target_censor_reason").isNotNull()
        )
    ).count()
    invalid_censored_target_count = targets.where(
        (~functions.col("target_is_observed"))
        & functions.col("target_censor_reason").isNull()
    ).count()
    checks = (
        (
            HISTORICAL_COVERAGE_TABLE,
            "acs_release_count",
            release_count,
            release_count == 15,
            "= 15 releases from 2010 through 2024",
        ),
        (
            HISTORICAL_STATE_TABLE,
            "invalid_alignment_method_count",
            invalid_state_alignment_count,
            invalid_state_alignment_count == 0,
            "= 0 eligible rows with an unsupported alignment method",
        ),
        (
            HISTORICAL_STATE_TABLE,
            "pre_2020_nonstable_alignment_count",
            pre_2020_nonstable_count,
            pre_2020_nonstable_count == 0,
            "= 0; pre-2020 rows must use the stable subset",
        ),
        (
            HISTORICAL_STATE_TABLE,
            "invalid_acs_availability_year_count",
            invalid_availability_count,
            invalid_availability_count == 0,
            "= 0 under the one-calendar-year ACS publication-lag rule",
        ),
        (
            HISTORICAL_TARGET_TABLE,
            "unexpected_horizon_configuration_count",
            int(target_horizons != horizons),
            target_horizons == horizons,
            f"= 0; horizons must equal {horizons}",
        ),
        (
            HISTORICAL_TARGET_TABLE,
            "invalid_target_timing_count",
            invalid_target_timing_count,
            invalid_target_timing_count == 0,
            "= 0; target end must equal origin plus horizon",
        ),
        (
            HISTORICAL_TARGET_TABLE,
            "invalid_observed_target_count",
            invalid_observed_target_count,
            invalid_observed_target_count == 0,
            "= 0 observed targets with missing values or a censoring reason",
        ),
        (
            HISTORICAL_TARGET_TABLE,
            "invalid_censored_target_count",
            invalid_censored_target_count,
            invalid_censored_target_count == 0,
            "= 0 censored targets without an explicit reason",
        ),
    )
    for table, metric_name, value, passed, expectation in checks:
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=f"{catalog}.{schema}.{table}",
                metric_group="historical_products",
                metric_name=metric_name,
                value=value,
                status="pass" if passed else "fail",
                expectation=expectation,
            )
        )

    observed_by_horizon = (
        targets.groupBy("horizon_years")
        .agg(
            functions.count(functions.lit(1)).alias("origin_count"),
            functions.sum(functions.col("target_is_observed").cast("long")).alias(
                "observed_target_count"
            ),
        )
        .collect()
    )
    for row in observed_by_horizon:
        horizon = int(row["horizon_years"])
        origin_count = int(row["origin_count"])
        observed_count = int(row["observed_target_count"])
        metrics.extend(
            (
                _metric(
                    build_id=build_id,
                    built_at_utc=built_at_utc,
                    table_name=f"{catalog}.{schema}.{HISTORICAL_TARGET_TABLE}",
                    metric_group="target_coverage",
                    metric_name="observed_target_count",
                    value=observed_count,
                    status="info",
                    expectation="reported by horizon",
                    dimension=f"horizon={horizon}",
                ),
                _metric(
                    build_id=build_id,
                    built_at_utc=built_at_utc,
                    table_name=f"{catalog}.{schema}.{HISTORICAL_TARGET_TABLE}",
                    metric_group="target_coverage",
                    metric_name="observed_target_rate",
                    value=observed_count / origin_count if origin_count else 0,
                    status="info",
                    expectation="reported by horizon",
                    dimension=f"horizon={horizon}",
                ),
            )
        )
    return metrics


def prepare_historical_build(
    spark: Any,
    *,
    catalog: str,
    silver_schema: str,
    gold_schema: str,
    horizons: tuple[int, ...] = DEFAULT_FORECAST_HORIZONS,
    built_at: datetime | None = None,
) -> HistoricalBuild:
    """Build and validate historical tract coverage, state, and target products."""

    horizons = validate_forecast_horizons(horizons)
    required = {
        "acs": f"{catalog}.{silver_schema}.silver_acs_tract_year",
        "fhfa": f"{catalog}.{silver_schema}.silver_fhfa_tract_year",
        "relationship": f"{catalog}.{silver_schema}.{TRACT_RELATIONSHIP_SILVER_TABLE}",
        "bridge": f"{catalog}.{silver_schema}.{CONNECTICUT_BRIDGE_TABLE}",
        "hierarchy": f"{catalog}.{silver_schema}.silver_geography_tract_2020",
    }
    missing = [name for name in required.values() if not spark.catalog.tableExists(name)]
    if missing:
        raise ValueError(f"Required historical input tables do not exist: {', '.join(missing)}")

    build_id, built_at_utc = new_quality_run_id(built_at)
    hierarchy = spark.table(required["hierarchy"])
    bridge = spark.table(required["bridge"])
    aligned_acs = _align_acs_geography(
        spark.table(required["acs"]),
        spark.table(required["relationship"]),
        bridge,
        hierarchy,
    )
    aligned_fhfa = _align_fhfa_geography(
        spark.table(required["fhfa"]),
        bridge,
        hierarchy,
    )
    frames = {
        HISTORICAL_COVERAGE_TABLE: _build_coverage(
            aligned_acs,
            build_id=build_id,
            built_at_utc=built_at_utc,
        ),
        HISTORICAL_STATE_TABLE: _build_historical_state(
            aligned_acs,
            build_id=build_id,
            built_at_utc=built_at_utc,
        ),
        HISTORICAL_TARGET_TABLE: _build_historical_targets(
            aligned_fhfa,
            horizons=horizons,
            build_id=build_id,
            built_at_utc=built_at_utc,
        ),
    }
    metrics = _quality_metrics(
        frames,
        horizons=horizons,
        build_id=build_id,
        built_at_utc=built_at_utc,
        catalog=catalog,
        schema=gold_schema,
    )
    return HistoricalBuild(build_id, built_at_utc, frames, metrics)


def publish_historical_build(
    build: HistoricalBuild,
    *,
    catalog: str,
    schema: str,
) -> tuple[str, ...]:
    """Publish all historical gold frames only after hard checks pass."""

    failures = hard_failures(build.metrics)
    if failures:
        names = ", ".join(
            f"{metric.table_name}:{metric.metric_name}" for metric in failures
        )
        raise ValueError(f"Historical gold build has hard quality failures: {names}")
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

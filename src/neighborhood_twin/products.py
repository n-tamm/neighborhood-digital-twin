"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Current-state analytical products and transparent application-testing cohorts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import reduce
from typing import Any

from neighborhood_twin.connecticut import CONNECTICUT_BRIDGE_TABLE
from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.validate import QualityMetric, hard_failures, new_quality_run_id

PRODUCT_SCHEMA_VERSION = "1.0.0"
CURRENT_PROFILE_TABLE = "gold_tract_profile_current"
SIMILARITY_CANDIDATE_TABLE = "gold_similarity_candidate_current"
FORECAST_CANDIDATE_TABLE = "gold_forecast_candidate_current"
APPLICATION_DEMO_TABLE = "gold_application_demo_tract"
PRODUCT_QUALITY_TABLE = "gold_quality_metrics"
KNOWN_CURRENT_ACS_GEOID_EXCEPTION_STATES = ("09",)

SIMILARITY_FEATURE_COLUMNS = (
    "population_total_estimate",
    "housing_units_total_estimate",
    "occupancy_rate_estimate",
    "vacancy_rate_estimate",
    "owner_occupancy_rate_estimate",
    "renter_occupancy_rate_estimate",
    "single_family_share_estimate",
    "multifamily_share_estimate",
    "mobile_home_share_estimate",
    "median_household_income_estimate",
    "median_owner_occupied_value_estimate",
    "median_gross_rent_estimate",
)

ACS_PROFILE_COLUMNS = (
    "acs_release_year",
    "acs_reference_period",
    "population_total_estimate",
    "population_total_moe",
    "housing_units_total_estimate",
    "housing_units_total_moe",
    "occupied_units_estimate",
    "vacant_units_estimate",
    "owner_occupied_units_estimate",
    "renter_occupied_units_estimate",
    "occupancy_rate_estimate",
    "vacancy_rate_estimate",
    "owner_occupancy_rate_estimate",
    "renter_occupancy_rate_estimate",
    "single_family_share_estimate",
    "multifamily_share_estimate",
    "mobile_home_share_estimate",
    "other_structure_share_estimate",
    "median_household_income_estimate",
    "median_household_income_moe",
    "median_owner_occupied_value_estimate",
    "median_owner_occupied_value_moe",
    "median_gross_rent_estimate",
    "median_gross_rent_moe",
)

PROFILE_IDENTIFIER_COLUMNS = (
    "geoid_2020",
    "state_fips",
    "state_abbreviation",
    "state_name",
    "county_geoid",
    "county_name",
    "tract_code",
    "tract_name",
    "land_area_sqm",
    "water_area_sqm",
    "has_display_geometry",
)

PRODUCT_LINEAGE_COLUMNS = (
    "product_schema_version",
    "product_build_id",
    "product_built_at_utc",
)


@dataclass(frozen=True)
class ProductBuild:
    """Validated current-state products and their unpublished quality metrics."""

    build_id: str
    built_at_utc: str
    frames: dict[str, Any]
    metrics: list[QualityMetric]


def parse_state_fips_codes(value: str) -> tuple[str, ...]:
    """Validate a comma-separated application demo scope."""

    codes = tuple(item.strip() for item in value.split(",") if item.strip())
    if not codes:
        raise ValueError("At least one demo-state FIPS code is required")
    if len(codes) != len(set(codes)):
        raise ValueError("Demo-state FIPS codes must not contain duplicates")
    if any(len(code) != 2 or not code.isdigit() for code in codes):
        raise ValueError("Every demo-state FIPS code must contain exactly two digits")
    return codes


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


def _require_tables(spark: Any, names: tuple[str, ...]) -> None:
    missing = [name for name in names if not spark.catalog.tableExists(name)]
    if missing:
        raise ValueError(f"Required analytical tables do not exist: {', '.join(missing)}")


def _build_fhfa_summary(fhfa: Any) -> tuple[Any, int]:
    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    usable = fhfa.where(functions.col("hpi_available"))
    latest_source_year = int(usable.agg(functions.max("observation_year")).first()[0])
    history = usable.groupBy("geoid").agg(
        functions.count("hpi").alias("hpi_observation_count"),
        functions.min("observation_year").alias("hpi_first_year"),
        functions.max("observation_year").alias("hpi_last_year"),
    )
    window = Window.partitionBy("geoid").orderBy(functions.col("observation_year").desc())
    latest = (
        usable.withColumn("latest_rank", functions.row_number().over(window))
        .where(functions.col("latest_rank") == 1)
        .select(
            "geoid",
            functions.col("observation_year").alias("latest_hpi_year"),
            functions.col("hpi").alias("latest_hpi"),
            functions.col("annual_change_pct").alias("latest_hpi_annual_change_pct"),
        )
    )
    return history.join(latest, "geoid", "inner"), latest_source_year


def _build_current_profile(
    canonical: Any,
    acs: Any,
    fhfa: Any,
    connecticut_bridge: Any,
    *,
    build_id: str,
    built_at_utc: str,
) -> Any:
    from pyspark.sql import functions  # type: ignore[import-not-found]

    current_acs_year = int(acs.agg(functions.max("acs_release_year")).first()[0])
    current_acs = (
        acs.where(functions.col("acs_release_year") == current_acs_year)
        .select("geoid", *ACS_PROFILE_COLUMNS)
        .withColumnRenamed("geoid", "acs_source_geoid")
        .join(
            connecticut_bridge.select("geoid_current", "geoid_2020"),
            functions.col("acs_source_geoid") == functions.col("geoid_current"),
            "left",
        )
        .withColumn(
            "acs_join_geoid",
            functions.coalesce("geoid_2020", "acs_source_geoid"),
        )
        .drop("geoid_current", "geoid_2020")
    )
    hpi_summary, latest_source_year = _build_fhfa_summary(fhfa)
    hpi_summary = hpi_summary.withColumnRenamed("geoid", "fhfa_geoid")

    joined = (
        canonical.select(*PROFILE_IDENTIFIER_COLUMNS)
        .join(current_acs, functions.col("geoid_2020") == functions.col("acs_join_geoid"), "left")
        .drop("acs_join_geoid")
        .join(hpi_summary, functions.col("geoid_2020") == functions.col("fhfa_geoid"), "left")
        .drop("fhfa_geoid")
    )
    availability_terms = [
        functions.when(functions.col(column).isNotNull(), 1).otherwise(0)
        for column in SIMILARITY_FEATURE_COLUMNS
    ]
    feature_count = reduce(lambda left, right: left + right, availability_terms)
    has_current_acs = functions.coalesce(
        functions.col("acs_release_year") == current_acs_year,
        functions.lit(False),
    )
    has_positive_scale = (functions.col("population_total_estimate") > 0) & (
        functions.col("housing_units_total_estimate") > 0
    )

    return (
        joined.withColumn("has_current_acs_profile", has_current_acs)
        .withColumn(
            "has_fhfa_history",
            functions.coalesce(
                functions.col("hpi_observation_count") > 0,
                functions.lit(False),
            ),
        )
        .withColumn("similarity_feature_count", feature_count)
        .withColumn(
            "similarity_candidate",
            functions.coalesce(
                has_current_acs
                & has_positive_scale
                & (functions.col("similarity_feature_count") >= 8),
                functions.lit(False),
            ),
        )
        .withColumn(
            "forecast_candidate",
            functions.coalesce(
                has_current_acs
                & (functions.col("hpi_observation_count") >= 10)
                & (functions.col("hpi_last_year") >= latest_source_year - 1)
                & functions.col("latest_hpi").isNotNull(),
                functions.lit(False),
            ),
        )
        .withColumn("product_schema_version", functions.lit(PRODUCT_SCHEMA_VERSION))
        .withColumn("product_build_id", functions.lit(build_id))
        .withColumn("product_built_at_utc", functions.to_timestamp(functions.lit(built_at_utc)))
        .select(
            *PROFILE_IDENTIFIER_COLUMNS,
            "acs_source_geoid",
            *ACS_PROFILE_COLUMNS,
            "hpi_observation_count",
            "hpi_first_year",
            "hpi_last_year",
            "latest_hpi_year",
            "latest_hpi",
            "latest_hpi_annual_change_pct",
            "has_current_acs_profile",
            "has_fhfa_history",
            "similarity_feature_count",
            "similarity_candidate",
            "forecast_candidate",
            *PRODUCT_LINEAGE_COLUMNS,
        )
    )


def _profile_frame(
    frame: Any,
    *,
    build_id: str,
    built_at_utc: str,
    table_name: str,
    expect_complete_canonical: bool,
    canonical_count: int,
) -> list[QualityMetric]:
    from pyspark.sql import functions  # type: ignore[import-not-found]

    summary = frame.agg(
        functions.count(functions.lit(1)).alias("row_count"),
        functions.countDistinct("geoid_2020").alias("distinct_geoid_count"),
    ).first()
    row_count = int(summary["row_count"])
    duplicate_count = row_count - int(summary["distinct_geoid_count"])
    reconciliation_difference = row_count - canonical_count if expect_complete_canonical else 0
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
            metric_group="integrity",
            metric_name="duplicate_geoid_count",
            value=duplicate_count,
            status="pass" if duplicate_count == 0 else "fail",
            expectation="= 0",
        ),
    ]
    if expect_complete_canonical:
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=table_name,
                metric_group="reconciliation",
                metric_name="canonical_row_difference",
                value=reconciliation_difference,
                status="pass" if reconciliation_difference == 0 else "fail",
                expectation="= 0",
            )
        )
    return metrics


def prepare_product_build(
    spark: Any,
    *,
    catalog: str,
    schema: str,
    demo_state_fips: str,
    built_at: datetime | None = None,
) -> ProductBuild:
    """Build a complete current profile and small, explicit downstream cohorts."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    canonical_name = f"{catalog}.{schema}.silver_canonical_tract_2020"
    acs_name = f"{catalog}.{schema}.silver_acs_tract_year"
    fhfa_name = f"{catalog}.{schema}.silver_fhfa_tract_year"
    bridge_name = f"{catalog}.{schema}.{CONNECTICUT_BRIDGE_TABLE}"
    _require_tables(spark, (canonical_name, acs_name, fhfa_name, bridge_name))
    states = parse_state_fips_codes(demo_state_fips)
    build_id, built_at_utc = new_quality_run_id(built_at)

    canonical = spark.table(canonical_name)
    acs = spark.table(acs_name)
    profile = _build_current_profile(
        canonical,
        acs,
        spark.table(fhfa_name),
        spark.table(bridge_name),
        build_id=build_id,
        built_at_utc=built_at_utc,
    )
    frames = {
        CURRENT_PROFILE_TABLE: profile,
        SIMILARITY_CANDIDATE_TABLE: profile.where(functions.col("similarity_candidate")),
        FORECAST_CANDIDATE_TABLE: profile.where(functions.col("forecast_candidate")),
        APPLICATION_DEMO_TABLE: profile.where(
            functions.col("state_fips").isin(*states)
            & functions.col("has_current_acs_profile")
            & functions.col("has_display_geometry")
        ),
    }

    canonical_count = canonical.count()
    metrics: list[QualityMetric] = []
    for table, frame in frames.items():
        metrics.extend(
            _profile_frame(
                frame,
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=f"{catalog}.{schema}.{table}",
                expect_complete_canonical=table == CURRENT_PROFILE_TABLE,
                canonical_count=canonical_count,
            )
        )
    current_acs_year = int(acs.agg(functions.max("acs_release_year")).first()[0])
    current_acs_geoids = (
        acs.where(functions.col("acs_release_year") == current_acs_year)
        .select("geoid", "state_fips")
        .distinct()
    )
    canonical_geoids = canonical.select("geoid_2020").distinct()
    bridge_geoids = spark.table(bridge_name).select("geoid_current", "geoid_2020").distinct()
    mapped_current = (
        current_acs_geoids.join(
            bridge_geoids,
            current_acs_geoids.geoid == bridge_geoids.geoid_current,
            "left",
        )
        .withColumn("canonical_geoid", functions.coalesce("geoid_2020", "geoid"))
        .drop("geoid_current", "geoid_2020")
    )
    direct_match_count = current_acs_geoids.join(
        canonical_geoids,
        current_acs_geoids.geoid == canonical_geoids.geoid_2020,
        "inner",
    ).count()
    bridge_match_count = current_acs_geoids.join(
        bridge_geoids,
        current_acs_geoids.geoid == bridge_geoids.geoid_current,
        "inner",
    ).count()
    unmatched_current = mapped_current.join(
        canonical_geoids,
        mapped_current.canonical_geoid == canonical_geoids.geoid_2020,
        "left_anti",
    )
    source_count = current_acs_geoids.count()
    unmatched_count = unmatched_current.count()
    known_exception_count = unmatched_current.where(
        functions.col("state_fips").isin(*KNOWN_CURRENT_ACS_GEOID_EXCEPTION_STATES)
    ).count()
    unexpected_unmatched_count = unmatched_count - known_exception_count
    mapped_current_geoids = mapped_current.select("canonical_geoid").distinct()
    canonical_without_current_count = canonical_geoids.join(
        mapped_current_geoids,
        canonical_geoids.geoid_2020 == mapped_current_geoids.canonical_geoid,
        "left_anti",
    ).count()
    coverage_metrics = (
        (
            "current_acs_source_tract_count",
            source_count,
            "pass" if source_count > 0 else "fail",
            "> 0",
            f"Distinct tract GEOIDs in ACS release {current_acs_year}.",
        ),
        (
            "current_acs_direct_match_count",
            direct_match_count,
            "info",
            "reported",
            "Current ACS GEOIDs found directly in the canonical 2020 tract dimension.",
        ),
        (
            "current_acs_connecticut_bridge_match_count",
            bridge_match_count,
            "pass" if bridge_match_count > 0 else "fail",
            "> 0",
            "Current Connecticut land tracts mapped to their canonical 2020 GEOIDs.",
        ),
        (
            "current_acs_unmatched_count",
            unmatched_count,
            "warn" if unmatched_count else "pass",
            "= 0 or documented geography exception",
            "Expected remainder is limited to Connecticut water-only tracts.",
        ),
        (
            "known_geography_exception_unmatched_count",
            known_exception_count,
            "info",
            "reported after explicit bridge",
            "Connecticut water-only tracts are intentionally not assigned demographic profiles.",
        ),
        (
            "unexpected_current_acs_unmatched_count",
            unexpected_unmatched_count,
            "pass" if unexpected_unmatched_count == 0 else "fail",
            "= 0",
            "Unmatched current ACS GEOIDs outside reviewed geography exceptions.",
        ),
        (
            "canonical_without_current_acs_count",
            canonical_without_current_count,
            "info",
            "reported",
            "Includes excluded territories, source omissions, and legacy water-only tracts.",
        ),
    )
    for metric_name, value, status, expectation, notes in coverage_metrics:
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=f"{catalog}.{schema}.{CURRENT_PROFILE_TABLE}",
                metric_group="coverage",
                metric_name=metric_name,
                value=value,
                status=status,
                expectation=expectation,
                notes=notes,
            )
        )
    metrics.append(
        _metric(
            build_id=build_id,
            built_at_utc=built_at_utc,
            table_name="gold_current_product_build",
            metric_group="run_summary",
            metric_name="failure_count",
            value=len(hard_failures(metrics)),
            status="pass" if not hard_failures(metrics) else "fail",
            expectation="= 0",
        )
    )
    return ProductBuild(build_id, built_at_utc, frames, metrics)


def publish_product_build(
    build: ProductBuild,
    *,
    catalog: str,
    schema: str,
) -> tuple[str, ...]:
    """Publish every gold product only after the full build passes hard checks."""

    failures = hard_failures(build.metrics)
    if failures:
        names = ", ".join(metric.metric_name for metric in failures)
        raise ValueError(f"Gold product build has hard failures: {names}")
    published: list[str] = []
    for table, frame in build.frames.items():
        table_name = qualified_name(catalog, schema, table)
        (
            frame.write.format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(table_name)
        )
        published.append(table_name)
    return tuple(published)

"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Versioned application-serving products for current historical analogues.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from neighborhood_twin.current_analogues import (
    CURRENT_ANALOGUE_REPRESENTATION,
    LOCKED_TEMPORAL_ROLE,
    summarize_current_analogue_matches,
)

ANALOGUE_SERVING_SCHEMA_VERSION = "1.0.0"
ANALOGUE_SERVING_MATCH_TABLE = "serving_analogue_match_current"
ANALOGUE_SERVING_SUMMARY_TABLE = "serving_analogue_summary_current"
ANALOGUE_SERVING_AVAILABILITY_TABLE = "serving_analogue_availability_current"
SERVING_RELEASE_MANIFEST_TABLE = "serving_release_manifest"
ANALOGUE_SERVING_COMPONENT = "historical_analogues"
ANALOGUE_SERVING_RETRIEVAL_METHOD = "exact_kd_tree_distinct_tract"


@dataclass(frozen=True)
class AnalogueServingRelease:
    """Immutable lineage and retrieval settings shared by one serving release."""

    release_id: str
    built_at_utc: str
    as_of_year: int
    horizons: tuple[int, ...]
    top_k: int
    model_readiness_build_id: str
    source_tree_run_id: str


def new_analogue_serving_release(
    *,
    as_of_year: int,
    horizons: tuple[int, ...],
    top_k: int,
    model_readiness_build_id: str,
    source_tree_run_id: str,
    release_id: str | None = None,
    built_at_utc: str | None = None,
) -> AnalogueServingRelease:
    """Create and validate one immutable serving-release context."""

    timestamp = datetime.now(UTC)
    release = AnalogueServingRelease(
        release_id=release_id or timestamp.strftime("analogue-%Y%m%dT%H%M%S%fZ"),
        built_at_utc=built_at_utc or timestamp.isoformat(),
        as_of_year=as_of_year,
        horizons=horizons,
        top_k=top_k,
        model_readiness_build_id=model_readiness_build_id,
        source_tree_run_id=source_tree_run_id,
    )
    validate_analogue_serving_release(release)
    return release


def validate_analogue_serving_release(release: AnalogueServingRelease) -> None:
    """Reject incomplete or internally inconsistent serving-release settings."""

    if not release.release_id.strip():
        raise ValueError("release_id must not be blank")
    if not release.built_at_utc.strip():
        raise ValueError("built_at_utc must not be blank")
    if release.as_of_year < 1900:
        raise ValueError("as_of_year must be a four-digit calendar year")
    if not release.horizons or any(value <= 0 for value in release.horizons):
        raise ValueError("horizons must contain positive integers")
    if len(release.horizons) != len(set(release.horizons)):
        raise ValueError("horizons must not contain duplicates")
    if release.top_k < 3:
        raise ValueError("top_k must be at least three")
    if not release.model_readiness_build_id.strip():
        raise ValueError("model_readiness_build_id must not be blank")
    if not release.source_tree_run_id.strip():
        raise ValueError("source_tree_run_id must not be blank")


def add_serving_lineage(frame: Any, release: AnalogueServingRelease) -> Any:
    """Attach the immutable release, source-build, and contract fields to a Spark frame."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        frame.withColumn("serving_release_id", functions.lit(release.release_id))
        .withColumn(
            "serving_schema_version",
            functions.lit(ANALOGUE_SERVING_SCHEMA_VERSION),
        )
        .withColumn(
            "serving_built_at_utc",
            functions.to_timestamp(functions.lit(release.built_at_utc)),
        )
        .withColumn("serving_as_of_year", functions.lit(release.as_of_year))
        .withColumn(
            "source_model_readiness_build_id",
            functions.lit(release.model_readiness_build_id),
        )
        .withColumn(
            "source_analogue_tree_run_id",
            functions.lit(release.source_tree_run_id),
        )
    )


def build_indexed_match_frame(
    representation: Any,
    key_frame: Any,
    *,
    as_of_year: int,
    horizon_years: int,
) -> Any:
    """Enrich exact indexed keys with the governed query, candidate, and outcome contract."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    queries = representation.where(
        functions.col("forecast_origin_year") == as_of_year
    ).select(
        functions.col("geoid_2020").alias("query_geoid_2020"),
        functions.col("forecast_origin_year").alias("query_origin_year"),
        "horizon_years",
        functions.col("forecast_origin_year").alias("query_as_of_year"),
        functions.col("target_end_year").alias("query_forecast_end_year"),
        functions.col("state_abbreviation").alias("query_state_abbreviation"),
        functions.col("county_name").alias("query_county_name"),
        functions.col("region_name").alias("query_region_name"),
        functions.col("modeling_cohort").alias("query_modeling_cohort"),
        functions.col("temporal_role").alias("query_temporal_role"),
        functions.col("geographic_role").alias("query_geographic_role"),
        functions.col("model_readiness_build_id").alias(
            "query_model_readiness_build_id"
        ),
    )
    candidates = representation.where(
        functions.col("target_is_observed")
        & (functions.col("geographic_role") == "geographic_development")
        & (functions.col("temporal_role") != LOCKED_TEMPORAL_ROLE)
        & (functions.col("target_end_year") <= as_of_year)
    ).select(
        functions.col("geoid_2020").alias("candidate_geoid_2020"),
        functions.col("forecast_origin_year").alias("candidate_origin_year"),
        "horizon_years",
        functions.col("target_end_year").alias("candidate_target_end_year"),
        functions.col("target_cumulative_log_change").alias(
            "candidate_target_cumulative_log_change"
        ),
        functions.col("target_annualized_change_pct").alias(
            "candidate_target_annualized_change_pct"
        ),
        functions.col("state_abbreviation").alias("candidate_state_abbreviation"),
        functions.col("county_name").alias("candidate_county_name"),
        functions.col("region_name").alias("candidate_region_name"),
        functions.col("modeling_cohort").alias("candidate_modeling_cohort"),
        functions.col("temporal_role").alias("candidate_temporal_role"),
        functions.col("model_readiness_build_id").alias(
            "candidate_model_readiness_build_id"
        ),
    )
    return (
        key_frame.join(
            functions.broadcast(queries),
            ["query_geoid_2020", "query_origin_year", "horizon_years"],
            "inner",
        )
        .join(
            candidates,
            ["candidate_geoid_2020", "candidate_origin_year", "horizon_years"],
            "inner",
        )
        .withColumn("representation_name", functions.lit(CURRENT_ANALOGUE_REPRESENTATION))
        .withColumn(
            "candidate_age_years",
            functions.lit(as_of_year) - functions.col("candidate_origin_year"),
        )
        .withColumn("unique_candidate_tract", functions.lit(True))
        .withColumn("locked_temporal_candidates_excluded", functions.lit(True))
        .withColumn(
            "retrieval_method",
            functions.lit(ANALOGUE_SERVING_RETRIEVAL_METHOD),
        )
        .where(functions.col("horizon_years") == horizon_years)
    )


def build_serving_match_frame(
    matches: Any,
    current_profile: Any,
    release: AnalogueServingRelease,
) -> Any:
    """Select compact application fields and attach tract labels and release lineage."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    query_labels = current_profile.select(
        functions.col("geoid_2020").alias("query_geoid_2020"),
        functions.col("state_name").alias("query_state_name"),
        functions.col("tract_name").alias("query_tract_name"),
    )
    candidate_labels = current_profile.select(
        functions.col("geoid_2020").alias("candidate_geoid_2020"),
        functions.col("state_name").alias("candidate_state_name"),
        functions.col("tract_name").alias("candidate_tract_name"),
    )
    compact = (
        matches.join(functions.broadcast(query_labels), "query_geoid_2020", "left")
        .join(functions.broadcast(candidate_labels), "candidate_geoid_2020", "left")
        .select(
            "query_geoid_2020",
            "query_origin_year",
            "query_as_of_year",
            "query_forecast_end_year",
            "horizon_years",
            "query_state_abbreviation",
            "query_state_name",
            "query_county_name",
            "query_tract_name",
            "query_region_name",
            "query_modeling_cohort",
            "candidate_geoid_2020",
            "candidate_origin_year",
            "candidate_target_end_year",
            "candidate_state_abbreviation",
            "candidate_state_name",
            "candidate_county_name",
            "candidate_tract_name",
            "candidate_region_name",
            "candidate_modeling_cohort",
            "candidate_target_cumulative_log_change",
            "candidate_target_annualized_change_pct",
            "similarity_distance",
            "match_rank",
            "candidate_age_years",
            "representation_name",
            "retrieval_method",
            "unique_candidate_tract",
            "locked_temporal_candidates_excluded",
        )
    )
    return add_serving_lineage(compact, release)


def build_serving_summary_frame(
    matches: Any,
    current_profile: Any,
    release: AnalogueServingRelease,
) -> Any:
    """Build descriptive analogue outcome summaries for every eligible current tract."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    labels = current_profile.select(
        functions.col("geoid_2020").alias("query_geoid_2020"),
        functions.col("state_name").alias("query_state_name"),
        functions.col("tract_name").alias("query_tract_name"),
    )
    summary = summarize_current_analogue_matches(matches).join(
        functions.broadcast(labels), "query_geoid_2020", "left"
    )
    return add_serving_lineage(summary, release)


def build_serving_availability_frame(
    current_profile: Any,
    eligible_queries: Any,
    release: AnalogueServingRelease,
) -> Any:
    """Publish one explicit availability or unavailability state per tract and horizon."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    spark = current_profile.sparkSession
    horizons = spark.createDataFrame(
        [(int(value),) for value in release.horizons],
        "horizon_years integer",
    )
    eligible = (
        eligible_queries.select("geoid_2020", "horizon_years")
        .distinct()
        .withColumn("_analogue_available", functions.lit(True))
    )
    base = current_profile.select(
        "geoid_2020",
        "state_fips",
        "state_abbreviation",
        "state_name",
        "county_geoid",
        "county_name",
        "tract_name",
        "acs_release_year",
        "has_current_acs_profile",
        "has_fhfa_history",
        "similarity_candidate",
        "single_family_share_estimate",
        "multifamily_share_estimate",
        "mobile_home_share_estimate",
        "product_build_id",
    ).crossJoin(functions.broadcast(horizons))
    available = functions.coalesce(functions.col("_analogue_available"), functions.lit(False))
    availability_reason = (
        functions.when(available, functions.lit("available"))
        .when(~functions.col("has_current_acs_profile"), functions.lit("current_acs_unavailable"))
        .when(
            ~functions.col("similarity_candidate"),
            functions.lit("insufficient_current_similarity_features"),
        )
        .when(~functions.col("has_fhfa_history"), functions.lit("fhfa_history_unavailable"))
        .otherwise(functions.lit("model_ready_market_features_unavailable"))
    )
    representativeness_band = (
        functions.when(
            functions.col("single_family_share_estimate").isNull(),
            functions.lit("unknown"),
        )
        .when(functions.col("single_family_share_estimate") >= 0.75, functions.lit("high"))
        .when(functions.col("single_family_share_estimate") >= 0.50, functions.lit("mixed"))
        .otherwise(functions.lit("limited"))
    )
    target_scope_note = (
        functions.when(
            functions.col("single_family_share_estimate").isNull(),
            functions.lit(
                "Housing composition is unavailable; FHFA target coverage cannot be contextualized."
            ),
        )
        .when(
            functions.col("single_family_share_estimate") < 0.50,
            functions.lit(
                "Single-family structures are under half of housing units; analogue outcomes "
                "describe only the FHFA-covered single-family market."
            ),
        )
        .when(
            functions.col("single_family_share_estimate") < 0.75,
            functions.lit(
                "This is a mixed housing market; analogue outcomes do not represent multifamily "
                "or rental prices."
            ),
        )
        .otherwise(
            functions.lit(
                "Analogue outcomes describe FHFA single-family HPI, not individual property values."
            )
        )
    )
    result = (
        base.join(eligible, ["geoid_2020", "horizon_years"], "left")
        .withColumn("analogue_available", available)
        .withColumn("availability_reason", availability_reason)
        .withColumn("target_representativeness_band", representativeness_band)
        .withColumn("target_scope_note", target_scope_note)
        .drop("_analogue_available")
    )
    return add_serving_lineage(result, release)


def validate_serving_outputs(
    matches: Any,
    summary: Any,
    availability: Any,
    release: AnalogueServingRelease,
) -> dict[str, int]:
    """Reconcile release lineage, keys, safety rules, coverage, and expected table grains."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    validate_analogue_serving_release(release)
    for name, frame in (
        (ANALOGUE_SERVING_MATCH_TABLE, matches),
        (ANALOGUE_SERVING_SUMMARY_TABLE, summary),
        (ANALOGUE_SERVING_AVAILABILITY_TABLE, availability),
    ):
        release_ids = {row[0] for row in frame.select("serving_release_id").distinct().collect()}
        if release_ids != {release.release_id}:
            raise RuntimeError(f"{name} does not contain exactly the requested release ID")

    availability_keys = ["geoid_2020", "horizon_years"]
    if availability.groupBy(*availability_keys).count().where(
        functions.col("count") != 1
    ).limit(1).count():
        raise RuntimeError("Analogue availability contains duplicate tract-horizon keys")
    if {
        int(row[0]) for row in availability.select("horizon_years").distinct().collect()
    } != set(release.horizons):
        raise RuntimeError("Analogue availability does not contain every declared horizon")

    match_keys = ["query_geoid_2020", "query_origin_year", "horizon_years"]
    match_groups = matches.groupBy(*match_keys).agg(
        functions.count(functions.lit(1)).alias("match_count"),
        functions.countDistinct("candidate_geoid_2020").alias("candidate_tract_count"),
        functions.min("match_rank").alias("minimum_rank"),
        functions.max("match_rank").alias("maximum_rank"),
    )
    if match_groups.where(
        (functions.col("match_count") != release.top_k)
        | (functions.col("candidate_tract_count") != release.top_k)
        | (functions.col("minimum_rank") != 1)
        | (functions.col("maximum_rank") != release.top_k)
    ).limit(1).count():
        raise RuntimeError("Serving matches lack one complete distinct ranked top-k")
    if matches.where(
        (functions.col("candidate_geoid_2020") == functions.col("query_geoid_2020"))
        | (functions.col("candidate_target_end_year") > functions.col("query_as_of_year"))
        | ~functions.col("locked_temporal_candidates_excluded")
    ).limit(1).count():
        raise RuntimeError("Serving matches violate self, timing, or locked-test safeguards")

    available_keys = availability.where(functions.col("analogue_available")).select(
        functions.col("geoid_2020").alias("query_geoid_2020"),
        "horizon_years",
    )
    matched_keys = match_groups.select("query_geoid_2020", "horizon_years")
    if available_keys.join(
        matched_keys, ["query_geoid_2020", "horizon_years"], "left_anti"
    ).limit(1).count() or matched_keys.join(
        available_keys, ["query_geoid_2020", "horizon_years"], "left_anti"
    ).limit(1).count():
        raise RuntimeError("Serving match keys do not reconcile to declared availability")

    summary_keys = summary.select("query_geoid_2020", "horizon_years")
    if summary.groupBy("query_geoid_2020", "horizon_years").count().where(
        functions.col("count") != 1
    ).limit(1).count():
        raise RuntimeError("Analogue summaries contain duplicate tract-horizon keys")
    if available_keys.join(
        summary_keys, ["query_geoid_2020", "horizon_years"], "left_anti"
    ).limit(1).count() or summary_keys.join(
        available_keys, ["query_geoid_2020", "horizon_years"], "left_anti"
    ).limit(1).count():
        raise RuntimeError("Analogue summary keys do not reconcile to declared availability")
    if summary.where(
        (functions.col("analogue_match_count") != release.top_k)
        | (functions.col("distinct_candidate_tract_count") != release.top_k)
        | functions.col("outcome_range_is_calibrated_interval")
    ).limit(1).count():
        raise RuntimeError("Analogue summaries violate match-count or interpretation rules")

    row_counts = {
        ANALOGUE_SERVING_MATCH_TABLE: matches.count(),
        ANALOGUE_SERVING_SUMMARY_TABLE: summary.count(),
        ANALOGUE_SERVING_AVAILABILITY_TABLE: availability.count(),
    }
    if row_counts[ANALOGUE_SERVING_MATCH_TABLE] != (
        row_counts[ANALOGUE_SERVING_SUMMARY_TABLE] * release.top_k
    ):
        raise RuntimeError("Serving match and summary row counts do not reconcile")
    return row_counts


def build_release_manifest(
    spark: Any,
    release: AnalogueServingRelease,
    row_counts: dict[str, int],
) -> Any:
    """Create validated component-table records; publishing this manifest activates the release."""

    required = {
        ANALOGUE_SERVING_MATCH_TABLE,
        ANALOGUE_SERVING_SUMMARY_TABLE,
        ANALOGUE_SERVING_AVAILABILITY_TABLE,
    }
    if set(row_counts) != required or any(value <= 0 for value in row_counts.values()):
        raise ValueError("row_counts must contain every positive analogue serving table count")
    rows = [
        (
            release.release_id,
            ANALOGUE_SERVING_SCHEMA_VERSION,
            release.built_at_utc,
            ANALOGUE_SERVING_COMPONENT,
            table_name,
            int(row_counts[table_name]),
            release.as_of_year,
            ",".join(str(value) for value in release.horizons),
            release.top_k,
            release.model_readiness_build_id,
            release.source_tree_run_id,
            ANALOGUE_SERVING_RETRIEVAL_METHOD,
            "validated",
        )
        for table_name in sorted(required)
    ]
    schema = (
        "serving_release_id string, serving_schema_version string, "
        "serving_built_at_utc_text string, component_name string, table_name string, "
        "row_count long, serving_as_of_year integer, horizons_csv string, top_k integer, "
        "source_model_readiness_build_id string, source_analogue_tree_run_id string, "
        "retrieval_method string, release_status string"
    )
    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        spark.createDataFrame(rows, schema)
        .withColumn(
            "serving_built_at_utc",
            functions.to_timestamp("serving_built_at_utc_text"),
        )
        .drop("serving_built_at_utc_text")
    )

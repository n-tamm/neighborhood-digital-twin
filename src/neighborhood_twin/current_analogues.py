"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Current-neighborhood retrieval using the frozen historical analogue representation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from neighborhood_twin.historical_analogues import (
    DEFAULT_HORIZONS,
    add_weighted_analogue_vector,
    fit_analogue_preprocessing,
    validate_analogue_columns,
)

CURRENT_ANALOGUE_SCHEMA_VERSION = "1.0.0"
CURRENT_ANALOGUE_MATCH_TABLE = "current_analogue_match"
CURRENT_ANALOGUE_SUMMARY_TABLE = "current_analogue_summary"
CURRENT_ANALOGUE_REPRESENTATION = "weighted_standardized"
LOCKED_TEMPORAL_ROLE = "locked_temporal_test"


@dataclass(frozen=True)
class CurrentAnalogueRun:
    """Current-query historical matches and descriptive outcome summaries."""

    run_id: str
    built_at_utc: str
    as_of_year: int
    matches: Any
    summary: Any


def validate_current_analogue_settings(
    *,
    horizons: tuple[int, ...],
    queries_per_state: int,
    top_k: int,
    as_of_year: int | None,
) -> None:
    """Validate the bounded current-query retrieval contract."""

    if not horizons or any(horizon <= 0 for horizon in horizons):
        raise ValueError("horizons must contain positive integers")
    if len(horizons) != len(set(horizons)):
        raise ValueError("horizons must not contain duplicates")
    if queries_per_state <= 0:
        raise ValueError("queries_per_state must be positive")
    if top_k < 3:
        raise ValueError("top_k must be at least three for an analogue outcome range")
    if as_of_year is not None and as_of_year < 1900:
        raise ValueError("as_of_year must be a four-digit calendar year")


def _resolve_as_of_year(modeling_panel: Any, requested_year: int | None) -> int:
    """Use the requested year or the latest feature origin present in the panel."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    latest_year = modeling_panel.agg(functions.max("forecast_origin_year")).first()[0]
    if latest_year is None:
        raise ValueError("The modeling panel contains no forecast-origin years")
    resolved = int(requested_year) if requested_year is not None else int(latest_year)
    if resolved > int(latest_year):
        raise ValueError(
            f"as_of_year {resolved} exceeds the latest modeled origin {int(latest_year)}"
        )
    return resolved


def _select_query_geoids(
    modeling_panel: Any,
    *,
    as_of_year: int,
    reference_horizon: int,
    query_geoids: tuple[str, ...],
    query_state_fips: tuple[str, ...],
    queries_per_state: int,
) -> tuple[str, ...]:
    """Choose explicit tracts or a deterministic geographically spread development set."""

    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    current = modeling_panel.where(
        (functions.col("forecast_origin_year") == as_of_year)
        & (functions.col("horizon_years") == reference_horizon)
    )
    if query_geoids:
        selected = current.where(functions.col("geoid_2020").isin(*query_geoids))
        found = {row[0] for row in selected.select("geoid_2020").distinct().collect()}
        missing = sorted(set(query_geoids) - found)
        if missing:
            raise ValueError(
                "Current analogue queries are unavailable in the model-ready panel: "
                + ", ".join(missing)
            )
        return tuple(query_geoids)
    if not query_state_fips:
        raise ValueError("At least one fallback query state is required")
    ranked = current.where(functions.col("state_fips").isin(*query_state_fips)).withColumn(
        "_query_rank",
        functions.row_number().over(
            Window.partitionBy("state_fips").orderBy(
                functions.xxhash64("geoid_2020"), "geoid_2020"
            )
        ),
    )
    selected = ranked.where(functions.col("_query_rank") <= queries_per_state)
    rows = selected.select("state_fips", "geoid_2020").collect()
    expected = len(query_state_fips) * queries_per_state
    if len(rows) != expected:
        raise ValueError(
            f"Fallback query selection found {len(rows)} tracts but expected {expected}"
        )
    return tuple(row["geoid_2020"] for row in rows)


def _rank_current_matches(
    representation: Any,
    queries: Any,
    *,
    top_k: int,
) -> Any:
    """Return exact, distinct, time-safe historical matches for current query tracts."""

    from pyspark.ml.functions import vector_to_array  # type: ignore[import-not-found]
    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    query = queries.select(
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
        functions.col("model_readiness_build_id").alias("query_model_readiness_build_id"),
        vector_to_array("analogue_weighted_vector").alias("_query_vector"),
    )
    candidate = representation.where(
        functions.col("target_is_observed")
        & (functions.col("geographic_role") == "geographic_development")
        & (functions.col("temporal_role") != LOCKED_TEMPORAL_ROLE)
    ).select(
        functions.col("geoid_2020").alias("candidate_geoid_2020"),
        functions.col("forecast_origin_year").alias("candidate_origin_year"),
        functions.col("horizon_years").alias("candidate_horizon_years"),
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
        vector_to_array("analogue_weighted_vector").alias("_candidate_vector"),
    )
    squared_terms = functions.transform(
        functions.arrays_zip("_query_vector", "_candidate_vector"),
        lambda pair: functions.pow(pair["_query_vector"] - pair["_candidate_vector"], 2),
    )
    pairs = (
        functions.broadcast(query)
        .crossJoin(candidate)
        .where(functions.col("candidate_horizon_years") == functions.col("horizon_years"))
        .where(functions.col("candidate_geoid_2020") != functions.col("query_geoid_2020"))
        .where(functions.col("candidate_target_end_year") <= functions.col("query_as_of_year"))
        .withColumn(
            "similarity_distance",
            functions.sqrt(
                functions.aggregate(
                    squared_terms,
                    functions.lit(0.0),
                    lambda accumulated, value: accumulated + value,
                )
            ),
        )
        .withColumn("representation_name", functions.lit(CURRENT_ANALOGUE_REPRESENTATION))
        .withColumn(
            "candidate_age_years",
            functions.col("query_as_of_year") - functions.col("candidate_origin_year"),
        )
    )
    distinct_tract_ranking = Window.partitionBy(
        "query_geoid_2020",
        "query_origin_year",
        "horizon_years",
        "candidate_geoid_2020",
    ).orderBy(
        "similarity_distance",
        functions.col("candidate_origin_year").desc(),
    )
    distinct_pairs = (
        pairs.withColumn(
            "_candidate_tract_rank",
            functions.row_number().over(distinct_tract_ranking),
        )
        .where(functions.col("_candidate_tract_rank") == 1)
        .drop("_candidate_tract_rank")
    )
    match_ranking = Window.partitionBy(
        "query_geoid_2020",
        "query_origin_year",
        "horizon_years",
    ).orderBy(
        "similarity_distance",
        functions.col("candidate_origin_year").desc(),
        "candidate_geoid_2020",
    )
    return (
        distinct_pairs.withColumn("match_rank", functions.row_number().over(match_ranking))
        .where(functions.col("match_rank") <= top_k)
        .withColumn("unique_candidate_tract", functions.lit(True))
        .withColumn("locked_temporal_candidates_excluded", functions.lit(True))
        .drop("candidate_horizon_years", "_query_vector", "_candidate_vector")
    )


def _summarize_current_matches(matches: Any, *, distance_epsilon: float = 1e-9) -> Any:
    """Summarize historical outcomes without presenting them as calibrated forecasts."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    keys = [
        "query_geoid_2020",
        "query_origin_year",
        "query_as_of_year",
        "query_forecast_end_year",
        "horizon_years",
        "query_state_abbreviation",
        "query_county_name",
        "query_region_name",
        "query_modeling_cohort",
        "query_temporal_role",
        "query_geographic_role",
        "query_model_readiness_build_id",
        "representation_name",
    ]
    weighted = matches.withColumn(
        "_inverse_distance_weight",
        functions.lit(1.0)
        / functions.greatest(functions.col("similarity_distance"), functions.lit(distance_epsilon)),
    )
    summary = weighted.groupBy(*keys).agg(
        functions.count(functions.lit(1)).alias("analogue_match_count"),
        functions.countDistinct("candidate_geoid_2020").alias(
            "distinct_candidate_tract_count"
        ),
        functions.avg("similarity_distance").alias("mean_similarity_distance"),
        functions.percentile_approx("similarity_distance", 0.5, 10000).alias(
            "median_similarity_distance"
        ),
        functions.percentile_approx(
            "candidate_target_cumulative_log_change", 0.5, 10000
        ).alias("analogue_median_log_change"),
        (
            functions.sum(
                functions.col("candidate_target_cumulative_log_change")
                * functions.col("_inverse_distance_weight")
            )
            / functions.sum("_inverse_distance_weight")
        ).alias("analogue_inverse_distance_log_change"),
        functions.percentile_approx(
            "candidate_target_cumulative_log_change", 0.1, 10000
        ).alias("analogue_outcome_p10_log_change"),
        functions.percentile_approx(
            "candidate_target_cumulative_log_change", 0.9, 10000
        ).alias("analogue_outcome_p90_log_change"),
        functions.avg("candidate_age_years").alias("mean_candidate_age_years"),
        functions.min("candidate_origin_year").alias("oldest_candidate_origin_year"),
        functions.max("candidate_origin_year").alias("newest_candidate_origin_year"),
        functions.avg(
            functions.when(
                functions.col("candidate_state_abbreviation")
                != functions.col("query_state_abbreviation"),
                1.0,
            ).otherwise(0.0)
        ).alias("cross_state_match_share"),
    )
    return (
        summary.withColumn(
            "analogue_median_cumulative_change_pct",
            (functions.exp("analogue_median_log_change") - functions.lit(1.0)) * 100.0,
        )
        .withColumn(
            "analogue_inverse_distance_cumulative_change_pct",
            (functions.exp("analogue_inverse_distance_log_change") - functions.lit(1.0))
            * 100.0,
        )
        .withColumn(
            "analogue_outcome_p10_cumulative_change_pct",
            (functions.exp("analogue_outcome_p10_log_change") - functions.lit(1.0)) * 100.0,
        )
        .withColumn(
            "analogue_outcome_p90_cumulative_change_pct",
            (functions.exp("analogue_outcome_p90_log_change") - functions.lit(1.0)) * 100.0,
        )
        .withColumn("outcome_range_is_calibrated_interval", functions.lit(False))
        .withColumn(
            "analogue_role",
            functions.lit("historical_context_not_primary_forecast"),
        )
    )


def _add_current_lineage(
    frame: Any,
    *,
    run_id: str,
    built_at_utc: str,
    as_of_year: int,
) -> Any:
    """Attach the frozen current-retrieval contract and run lineage."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        frame.withColumn(
            "current_analogue_schema_version",
            functions.lit(CURRENT_ANALOGUE_SCHEMA_VERSION),
        )
        .withColumn("current_analogue_run_id", functions.lit(run_id))
        .withColumn(
            "current_analogue_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
        .withColumn("current_analogue_as_of_year", functions.lit(as_of_year))
    )


def build_current_analogue_run(
    modeling_panel: Any,
    *,
    query_geoids: tuple[str, ...] = (),
    query_state_fips: tuple[str, ...] = ("04", "26", "42"),
    queries_per_state: int = 1,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS,
    top_k: int = 10,
    as_of_year: int | None = None,
    run_id: str | None = None,
    built_at_utc: str | None = None,
) -> CurrentAnalogueRun:
    """Retrieve historical analogues for selected neighborhoods at the latest modeled year."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    validate_analogue_columns(modeling_panel.columns)
    validate_current_analogue_settings(
        horizons=horizons,
        queries_per_state=queries_per_state,
        top_k=top_k,
        as_of_year=as_of_year,
    )
    resolved_as_of_year = _resolve_as_of_year(modeling_panel, as_of_year)
    selected_geoids = _select_query_geoids(
        modeling_panel,
        as_of_year=resolved_as_of_year,
        reference_horizon=horizons[0],
        query_geoids=query_geoids,
        query_state_fips=query_state_fips,
        queries_per_state=queries_per_state,
    )
    run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    built_at_utc = built_at_utc or datetime.now(UTC).isoformat()

    horizon_matches = []
    for horizon in horizons:
        horizon_panel = modeling_panel.where(functions.col("horizon_years") == int(horizon))
        represented = add_weighted_analogue_vector(
            fit_analogue_preprocessing(horizon_panel)
        ).cache()
        queries = represented.where(
            (functions.col("forecast_origin_year") == resolved_as_of_year)
            & functions.col("geoid_2020").isin(*selected_geoids)
        )
        if queries.select("geoid_2020").distinct().count() != len(selected_geoids):
            raise ValueError(
                f"Not every selected current tract has a horizon-{horizon} model-ready row"
            )
        matches = _rank_current_matches(represented, queries, top_k=top_k).cache()
        if matches.count() != len(selected_geoids) * top_k:
            raise ValueError(
                f"Horizon {horizon} did not return {top_k} matches for every current query"
            )
        horizon_matches.append(matches)

    matches = horizon_matches[0]
    for frame in horizon_matches[1:]:
        matches = matches.unionByName(frame)
    summary = _summarize_current_matches(matches)
    return CurrentAnalogueRun(
        run_id=run_id,
        built_at_utc=built_at_utc,
        as_of_year=resolved_as_of_year,
        matches=_add_current_lineage(
            matches,
            run_id=run_id,
            built_at_utc=built_at_utc,
            as_of_year=resolved_as_of_year,
        ),
        summary=_add_current_lineage(
            summary,
            run_id=run_id,
            built_at_utc=built_at_utc,
            as_of_year=resolved_as_of_year,
        ),
    )

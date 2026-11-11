"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Scalable historical-analogue candidate generation and exact-reference evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from neighborhood_twin.analogue_selection import community_size_band
from neighborhood_twin.current_analogues import (
    CURRENT_ANALOGUE_REPRESENTATION,
    LOCKED_TEMPORAL_ROLE,
    rank_current_analogue_matches,
    summarize_current_analogue_matches,
)
from neighborhood_twin.forecasting import acs_uncertainty_band, housing_composition_band
from neighborhood_twin.historical_analogues import (
    DEFAULT_HORIZONS,
    add_weighted_analogue_vector,
    fit_analogue_preprocessing,
    validate_analogue_columns,
)

SCALABLE_ANALOGUE_SCHEMA_VERSION = "1.0.0"
SCALABLE_ANALOGUE_MATCH_TABLE = "scalable_analogue_match"
SCALABLE_ANALOGUE_QUERY_EVALUATION_TABLE = "scalable_analogue_query_evaluation"
SCALABLE_ANALOGUE_SUMMARY_TABLE = "scalable_analogue_summary"
SCALABLE_ANALOGUE_COVERAGE_TABLE = "scalable_analogue_coverage"
EXACT_REFERENCE_CONFIG = "exact_reference"
DEFAULT_BENCHMARK_QUERIES_PER_GROUP = 3
DEFAULT_TOP_K = 10


@dataclass(frozen=True)
class LSHConfiguration:
    """Deterministic random-projection LSH shortlist configuration."""

    name: str
    bucket_length: float
    num_hash_tables: int


DEFAULT_LSH_CONFIGURATIONS = (
    LSHConfiguration("lsh_narrow", bucket_length=0.75, num_hash_tables=6),
    LSHConfiguration("lsh_balanced", bucket_length=1.50, num_hash_tables=10),
    LSHConfiguration("lsh_high_recall", bucket_length=3.00, num_hash_tables=14),
)

BENCHMARK_COVERAGE_DIMENSIONS = (
    ("overall", "query_overall"),
    ("census_region", "region_name"),
    ("modeling_cohort", "modeling_cohort"),
    ("housing_composition_band", "query_housing_composition_band"),
    ("community_size_band", "query_community_size_band"),
    ("acs_uncertainty_band", "query_acs_uncertainty_band"),
)


@dataclass(frozen=True)
class ScalableAnalogueRun:
    """Exact and approximate matches plus query, summary, and coverage evidence."""

    run_id: str
    built_at_utc: str
    as_of_year: int
    matches: Any
    query_evaluation: Any
    summary: Any
    coverage: Any


def validate_lsh_configurations(configurations: tuple[LSHConfiguration, ...]) -> None:
    """Require unique, positive, non-reference approximate retrieval configurations."""

    if not configurations:
        raise ValueError("At least one LSH configuration is required")
    names = [configuration.name for configuration in configurations]
    if len(names) != len(set(names)):
        raise ValueError("LSH configuration names must be unique")
    if EXACT_REFERENCE_CONFIG in names:
        raise ValueError("The exact reference name is reserved")
    for configuration in configurations:
        if not configuration.name.strip():
            raise ValueError("LSH configuration names must not be blank")
        if configuration.bucket_length <= 0:
            raise ValueError("LSH bucket lengths must be positive")
        if configuration.num_hash_tables <= 0:
            raise ValueError("LSH hash-table counts must be positive")


def validate_scalable_settings(
    *,
    horizons: tuple[int, ...],
    queries_per_group: int,
    top_k: int,
    configurations: tuple[LSHConfiguration, ...],
) -> None:
    """Validate the benchmark sample, retrieval, and approximation contract."""

    if not horizons or any(horizon <= 0 for horizon in horizons):
        raise ValueError("horizons must contain positive integers")
    if len(horizons) != len(set(horizons)):
        raise ValueError("horizons must not contain duplicates")
    if queries_per_group <= 0:
        raise ValueError("queries_per_group must be positive")
    if top_k < 3:
        raise ValueError("top_k must be at least three")
    validate_lsh_configurations(configurations)


def _resolve_as_of_year(modeling_panel: Any, requested_year: int | None) -> int:
    """Use a requested current year or the latest model-ready feature origin."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    latest = modeling_panel.agg(functions.max("forecast_origin_year")).first()[0]
    if latest is None:
        raise ValueError("The modeling panel contains no forecast-origin years")
    resolved = int(requested_year) if requested_year is not None else int(latest)
    if resolved > int(latest):
        raise ValueError(
            f"as_of_year {resolved} exceeds the latest modeled origin {int(latest)}"
        )
    return resolved


def _add_query_dimensions(frame: Any) -> Any:
    """Attach the dimensions used for benchmark balance and coverage review."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        frame.withColumn("query_overall", functions.lit("all"))
        .withColumn(
            "query_housing_composition_band",
            housing_composition_band(
                functions.col("single_family_share_estimate"), functions
            ),
        )
        .withColumn(
            "query_community_size_band",
            community_size_band(functions.col("population_total_estimate"), functions),
        )
        .withColumn(
            "query_acs_uncertainty_band",
            acs_uncertainty_band(frame, functions),
        )
    )


def select_benchmark_queries(
    modeling_panel: Any,
    *,
    as_of_year: int,
    reference_horizon: int,
    queries_per_group: int,
) -> Any:
    """Select a deterministic balanced current-query sample with coverage supplements."""

    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    current = _add_query_dimensions(
        modeling_panel.where(
            (functions.col("forecast_origin_year") == as_of_year)
            & (functions.col("horizon_years") == reference_horizon)
        )
    )
    ranked = current.withColumn(
        "_query_rank",
        functions.row_number().over(
            Window.partitionBy("region_name", "modeling_cohort").orderBy(
                functions.xxhash64("geoid_2020"), "geoid_2020"
            )
        ),
    )
    selected = ranked.where(functions.col("_query_rank") <= queries_per_group).drop(
        "_query_rank"
    )
    for column_name in (
        "query_housing_composition_band",
        "query_community_size_band",
        "query_acs_uncertainty_band",
    ):
        supplement = (
            current.where(functions.col(column_name).isNotNull())
            .withColumn(
                "_coverage_rank",
                functions.row_number().over(
                    Window.partitionBy(column_name).orderBy(
                        functions.xxhash64("geoid_2020"), "geoid_2020"
                    )
                ),
            )
            .where(functions.col("_coverage_rank") == 1)
            .drop("_coverage_rank")
        )
        selected = selected.unionByName(supplement)
    selected = selected.dropDuplicates(["geoid_2020"])
    if selected.limit(1).count() == 0:
        raise ValueError("No current queries satisfy the scalable benchmark contract")
    return selected


def _historical_candidate_pool(representation: Any, *, as_of_year: int) -> Any:
    """Return historical candidates allowed by the frozen current retrieval contract."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return representation.where(
        functions.col("target_is_observed")
        & (functions.col("geographic_role") == "geographic_development")
        & (functions.col("temporal_role") != LOCKED_TEMPORAL_ROLE)
        & (functions.col("target_end_year") <= as_of_year)
    )


def rank_lsh_shortlist_matches(
    representation: Any,
    queries: Any,
    *,
    configuration: LSHConfiguration,
    top_k: int,
    as_of_year: int,
    seed: int = 699,
) -> tuple[Any, int, float]:
    """Generate LSH candidates, then apply exact distance and distinct-tract reranking."""

    from pyspark.ml.feature import (  # type: ignore[import-not-found]
        BucketedRandomProjectionLSH,
    )
    from pyspark.ml.functions import vector_to_array  # type: ignore[import-not-found]
    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    validate_lsh_configurations((configuration,))
    start = perf_counter()
    candidates = _historical_candidate_pool(representation, as_of_year=as_of_year)
    model = BucketedRandomProjectionLSH(
        inputCol="analogue_weighted_vector",
        outputCol="_lsh_hashes",
        bucketLength=configuration.bucket_length,
        numHashTables=configuration.num_hash_tables,
        seed=seed,
    ).fit(candidates)
    candidate_hashed = model.transform(candidates)
    query_hashed = model.transform(queries)

    candidate_buckets = (
        candidate_hashed.select(
            functions.col("geoid_2020").alias("candidate_geoid_2020"),
            functions.col("forecast_origin_year").alias("candidate_origin_year"),
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
            functions.posexplode("_lsh_hashes").alias(
                "_hash_table_index", "_candidate_hash_vector"
            ),
        )
        .withColumn(
            "_hash_bucket",
            vector_to_array("_candidate_hash_vector")[0].cast("long"),
        )
        .drop("_candidate_hash_vector")
    )
    query_buckets = (
        query_hashed.select(
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
            vector_to_array("analogue_weighted_vector").alias("_query_vector"),
            functions.posexplode("_lsh_hashes").alias(
                "_hash_table_index", "_query_hash_vector"
            ),
        )
        .withColumn(
            "_hash_bucket",
            vector_to_array("_query_hash_vector")[0].cast("long"),
        )
        .drop("_query_hash_vector")
    )
    joined = (
        functions.broadcast(query_buckets)
        .join(candidate_buckets, ["_hash_table_index", "_hash_bucket"], "inner")
        .where(functions.col("candidate_geoid_2020") != functions.col("query_geoid_2020"))
        .dropDuplicates(
            [
                "query_geoid_2020",
                "query_origin_year",
                "candidate_geoid_2020",
                "candidate_origin_year",
            ]
        )
        .cache()
    )
    shortlist_pair_count = joined.count()
    squared_terms = functions.transform(
        functions.arrays_zip("_query_vector", "_candidate_vector"),
        lambda pair: functions.pow(pair["_query_vector"] - pair["_candidate_vector"], 2),
    )
    pairs = (
        joined.withColumn(
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
        .withColumn("retrieval_config_name", functions.lit(configuration.name))
        .withColumn("retrieval_method", functions.lit("lsh_shortlist_exact_rerank"))
        .withColumn("lsh_bucket_length", functions.lit(configuration.bucket_length))
        .withColumn("lsh_num_hash_tables", functions.lit(configuration.num_hash_tables))
        .withColumn(
            "candidate_age_years",
            functions.col("query_as_of_year") - functions.col("candidate_origin_year"),
        )
    )
    distinct_window = Window.partitionBy(
        "query_geoid_2020",
        "query_origin_year",
        "horizon_years",
        "candidate_geoid_2020",
    ).orderBy("similarity_distance", functions.col("candidate_origin_year").desc())
    distinct_pairs = (
        pairs.withColumn("_candidate_tract_rank", functions.row_number().over(distinct_window))
        .where(functions.col("_candidate_tract_rank") == 1)
        .drop("_candidate_tract_rank")
    )
    ranking = Window.partitionBy(
        "query_geoid_2020", "query_origin_year", "horizon_years"
    ).orderBy(
        "similarity_distance",
        functions.col("candidate_origin_year").desc(),
        "candidate_geoid_2020",
    )
    matches = (
        distinct_pairs.withColumn("match_rank", functions.row_number().over(ranking))
        .where(functions.col("match_rank") <= top_k)
        .withColumn("unique_candidate_tract", functions.lit(True))
        .withColumn("locked_temporal_candidates_excluded", functions.lit(True))
        .drop(
            "_hash_table_index",
            "_hash_bucket",
            "_query_vector",
            "_candidate_vector",
        )
        .cache()
    )
    matches.count()
    elapsed_seconds = perf_counter() - start
    return matches, shortlist_pair_count, elapsed_seconds


def _label_exact_reference(matches: Any) -> Any:
    """Attach the benchmark retrieval fields to exact reference matches."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        matches.withColumn("retrieval_config_name", functions.lit(EXACT_REFERENCE_CONFIG))
        .withColumn("retrieval_method", functions.lit("exhaustive_exact"))
        .withColumn("lsh_bucket_length", functions.lit(None).cast("double"))
        .withColumn("lsh_num_hash_tables", functions.lit(None).cast("integer"))
    )


def build_query_evaluation(
    matches: Any,
    *,
    top_k: int,
    configuration_names: tuple[str, ...],
) -> Any:
    """Compare every approximate query result with its exact top-k reference."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    keys = ["query_geoid_2020", "query_origin_year", "horizon_years"]
    exact = matches.where(
        functions.col("retrieval_config_name") == EXACT_REFERENCE_CONFIG
    ).select(
        *keys,
        functions.col("candidate_geoid_2020").alias("exact_candidate_geoid_2020"),
        functions.col("match_rank").alias("exact_match_rank"),
    )
    approximate = matches.where(
        functions.col("retrieval_config_name") != EXACT_REFERENCE_CONFIG
    )
    spark = matches.sparkSession
    configuration_frame = spark.createDataFrame(
        [(name,) for name in configuration_names],
        ["retrieval_config_name"],
    )
    query_grid = functions.broadcast(exact.select(*keys).distinct()).crossJoin(
        functions.broadcast(configuration_frame)
    )
    approximate_groups = approximate.groupBy(*keys, "retrieval_config_name").agg(
        functions.count(functions.lit(1)).alias("approximate_match_count"),
        functions.countDistinct("candidate_geoid_2020").alias(
            "approximate_candidate_tract_count"
        ),
    )
    overlap = (
        approximate.alias("approximate")
        .join(
            exact.alias("exact"),
            [
                functions.col("approximate.query_geoid_2020")
                == functions.col("exact.query_geoid_2020"),
                functions.col("approximate.query_origin_year")
                == functions.col("exact.query_origin_year"),
                functions.col("approximate.horizon_years")
                == functions.col("exact.horizon_years"),
                functions.col("approximate.candidate_geoid_2020")
                == functions.col("exact.exact_candidate_geoid_2020"),
            ],
            "inner",
        )
        .groupBy(
            functions.col("approximate.query_geoid_2020").alias("query_geoid_2020"),
            functions.col("approximate.query_origin_year").alias("query_origin_year"),
            functions.col("approximate.horizon_years").alias("horizon_years"),
            functions.col("approximate.retrieval_config_name").alias(
                "retrieval_config_name"
            ),
        )
        .agg(
            functions.count(functions.lit(1)).alias("exact_top_k_overlap_count"),
            functions.avg(
                functions.abs(
                    functions.col("approximate.match_rank")
                    - functions.col("exact.exact_match_rank")
                )
            ).alias("mean_shared_rank_displacement"),
            functions.sum(
                functions.when(
                    functions.col("exact.exact_match_rank") <= 3,
                    1,
                ).otherwise(0)
            ).alias("exact_top_three_retention_count"),
        )
    )
    approximate_summary = summarize_current_analogue_matches(
        approximate,
        additional_group_columns=("retrieval_config_name",),
    ).select(
        *keys,
        "retrieval_config_name",
        functions.col("analogue_median_log_change").alias(
            "approximate_analogue_median_log_change"
        ),
        functions.col("analogue_inverse_distance_log_change").alias(
            "approximate_analogue_inverse_distance_log_change"
        ),
    )
    exact_summary = summarize_current_analogue_matches(
        matches.where(functions.col("retrieval_config_name") == EXACT_REFERENCE_CONFIG)
    ).select(
        *keys,
        functions.col("analogue_median_log_change").alias(
            "exact_analogue_median_log_change"
        ),
        functions.col("analogue_inverse_distance_log_change").alias(
            "exact_analogue_inverse_distance_log_change"
        ),
    )
    return (
        query_grid.join(
            approximate_groups,
            [*keys, "retrieval_config_name"],
            "left",
        )
        .fillna(
            0,
            subset=[
                "approximate_match_count",
                "approximate_candidate_tract_count",
            ],
        )
        .join(overlap, [*keys, "retrieval_config_name"], "left")
        .join(approximate_summary, [*keys, "retrieval_config_name"], "left")
        .join(exact_summary, keys, "left")
        .fillna(
            0,
            subset=[
                "exact_top_k_overlap_count",
                "exact_top_three_retention_count",
            ],
        )
        .fillna(
            float(top_k),
            subset=["mean_shared_rank_displacement"],
        )
        .withColumn(
            "complete_top_k",
            functions.col("approximate_match_count") == functions.lit(top_k),
        )
        .withColumn(
            "exact_top_k_recall",
            functions.col("exact_top_k_overlap_count") / functions.lit(float(top_k)),
        )
        .withColumn(
            "top_k_jaccard_similarity",
            functions.col("exact_top_k_overlap_count")
            / (
                functions.lit(float(top_k))
                + functions.col("approximate_match_count")
                - functions.col("exact_top_k_overlap_count")
            ),
        )
        .withColumn(
            "exact_top_three_retention_share",
            functions.col("exact_top_three_retention_count") / functions.lit(3.0),
        )
        .withColumn(
            "median_outcome_drift_log_change",
            functions.col("approximate_analogue_median_log_change")
            - functions.col("exact_analogue_median_log_change"),
        )
        .withColumn(
            "inverse_distance_outcome_drift_log_change",
            functions.col("approximate_analogue_inverse_distance_log_change")
            - functions.col("exact_analogue_inverse_distance_log_change"),
        )
    )


def build_scalable_summary(
    query_evaluation: Any,
    *,
    runtime_rows: list[dict[str, Any]],
) -> Any:
    """Aggregate fidelity and execution evidence by horizon and configuration."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    spark = query_evaluation.sparkSession
    runtimes = spark.createDataFrame(runtime_rows)
    approximate_summary = (
        query_evaluation.groupBy("horizon_years", "retrieval_config_name")
        .agg(
            functions.count(functions.lit(1)).alias("query_count"),
            functions.avg(functions.col("complete_top_k").cast("double")).alias(
                "complete_top_k_share"
            ),
            functions.avg("exact_top_k_recall").alias("mean_exact_top_k_recall"),
            functions.percentile_approx("exact_top_k_recall", 0.1, 10000).alias(
                "p10_exact_top_k_recall"
            ),
            functions.avg("top_k_jaccard_similarity").alias(
                "mean_top_k_jaccard_similarity"
            ),
            functions.avg("exact_top_three_retention_share").alias(
                "mean_exact_top_three_retention_share"
            ),
            functions.avg("mean_shared_rank_displacement").alias(
                "mean_shared_rank_displacement"
            ),
            functions.avg(
                functions.abs("median_outcome_drift_log_change")
            ).alias("mean_absolute_median_outcome_drift_log_change"),
            functions.avg(
                functions.abs("inverse_distance_outcome_drift_log_change")
            ).alias("mean_absolute_inverse_distance_outcome_drift_log_change"),
        )
        .join(runtimes, ["horizon_years", "retrieval_config_name"], "left")
    )
    exact_query_counts = query_evaluation.select(
        "query_geoid_2020", "query_origin_year", "horizon_years"
    ).distinct().groupBy("horizon_years").agg(
        functions.count(functions.lit(1)).alias("query_count")
    )
    exact_summary = (
        runtimes.where(functions.col("retrieval_config_name") == EXACT_REFERENCE_CONFIG)
        .join(exact_query_counts, "horizon_years", "inner")
        .withColumn("complete_top_k_share", functions.lit(1.0))
        .withColumn("mean_exact_top_k_recall", functions.lit(1.0))
        .withColumn("p10_exact_top_k_recall", functions.lit(1.0))
        .withColumn("mean_top_k_jaccard_similarity", functions.lit(1.0))
        .withColumn("mean_exact_top_three_retention_share", functions.lit(1.0))
        .withColumn("mean_shared_rank_displacement", functions.lit(0.0))
        .withColumn(
            "mean_absolute_median_outcome_drift_log_change",
            functions.lit(0.0),
        )
        .withColumn(
            "mean_absolute_inverse_distance_outcome_drift_log_change",
            functions.lit(0.0),
        )
    )
    return approximate_summary.unionByName(exact_summary)


def build_benchmark_coverage(eligible_queries: Any, selected_queries: Any) -> Any:
    """Compare selected current-query dimensions with all current eligible queries."""

    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    outputs = []
    for dimension_name, column_name in BENCHMARK_COVERAGE_DIMENSIONS:
        eligible = eligible_queries.groupBy(
            functions.lit(dimension_name).alias("dimension_name"),
            functions.col(column_name).cast("string").alias("dimension_value"),
        ).agg(functions.count(functions.lit(1)).alias("eligible_query_count"))
        selected = selected_queries.groupBy(
            functions.lit(dimension_name).alias("dimension_name"),
            functions.col(column_name).cast("string").alias("dimension_value"),
        ).agg(functions.count(functions.lit(1)).alias("selected_query_count"))
        outputs.append(
            eligible.join(selected, ["dimension_name", "dimension_value"], "left").fillna(
                0, subset=["selected_query_count"]
            )
        )
    coverage = outputs[0]
    for output in outputs[1:]:
        coverage = coverage.unionByName(output)
    window = Window.partitionBy("dimension_name")
    return (
        coverage.withColumn(
            "eligible_query_share",
            functions.col("eligible_query_count")
            / functions.sum("eligible_query_count").over(window),
        )
        .withColumn(
            "selected_query_share",
            functions.col("selected_query_count")
            / functions.sum("selected_query_count").over(window),
        )
        .withColumn(
            "selected_minus_eligible_share",
            functions.col("selected_query_share") - functions.col("eligible_query_share"),
        )
        .withColumn(
            "coverage_status",
            functions.when(
                functions.col("selected_query_count") > 0,
                functions.lit("covered"),
            ).otherwise(functions.lit("eligible_not_selected")),
        )
    )


def _add_lineage(
    frame: Any,
    *,
    run_id: str,
    built_at_utc: str,
    as_of_year: int,
    queries_per_group: int,
) -> Any:
    """Attach the scalable benchmark contract and run lineage."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        frame.withColumn(
            "scalable_analogue_schema_version",
            functions.lit(SCALABLE_ANALOGUE_SCHEMA_VERSION),
        )
        .withColumn("scalable_analogue_run_id", functions.lit(run_id))
        .withColumn(
            "scalable_analogue_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
        .withColumn("scalable_analogue_as_of_year", functions.lit(as_of_year))
        .withColumn("benchmark_queries_per_group", functions.lit(queries_per_group))
    )


def build_scalable_analogue_run(
    modeling_panel: Any,
    *,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS,
    queries_per_group: int = DEFAULT_BENCHMARK_QUERIES_PER_GROUP,
    top_k: int = DEFAULT_TOP_K,
    configurations: tuple[LSHConfiguration, ...] = DEFAULT_LSH_CONFIGURATIONS,
    as_of_year: int | None = None,
    run_id: str | None = None,
    built_at_utc: str | None = None,
) -> ScalableAnalogueRun:
    """Benchmark LSH shortlists against exact current-neighborhood retrieval."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    validate_analogue_columns(modeling_panel.columns)
    validate_scalable_settings(
        horizons=horizons,
        queries_per_group=queries_per_group,
        top_k=top_k,
        configurations=configurations,
    )
    resolved_as_of_year = _resolve_as_of_year(modeling_panel, as_of_year)
    selected_reference = select_benchmark_queries(
        modeling_panel,
        as_of_year=resolved_as_of_year,
        reference_horizon=horizons[0],
        queries_per_group=queries_per_group,
    ).cache()
    selected_geoids = [row[0] for row in selected_reference.select("geoid_2020").collect()]
    if not selected_geoids:
        raise ValueError("The scalable benchmark selected no query GEOIDs")
    run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    built_at_utc = built_at_utc or datetime.now(UTC).isoformat()

    all_matches = []
    runtime_rows: list[dict[str, Any]] = []
    for horizon in horizons:
        horizon_panel = modeling_panel.where(functions.col("horizon_years") == int(horizon))
        represented = add_weighted_analogue_vector(
            fit_analogue_preprocessing(horizon_panel)
        ).cache()
        queries = represented.where(
            (functions.col("forecast_origin_year") == resolved_as_of_year)
            & functions.col("geoid_2020").isin(*selected_geoids)
        ).cache()
        if queries.select("geoid_2020").distinct().count() != len(selected_geoids):
            raise ValueError(
                f"Not every benchmark query has a horizon-{horizon} model-ready row"
            )

        exact_start = perf_counter()
        exact_matches = _label_exact_reference(
            rank_current_analogue_matches(represented, queries, top_k=top_k)
        ).cache()
        exact_match_count = exact_matches.count()
        exact_elapsed = perf_counter() - exact_start
        if exact_match_count != len(selected_geoids) * top_k:
            raise ValueError(f"Horizon {horizon} exact reference is incomplete")
        all_matches.append(exact_matches)
        runtime_rows.append(
            {
                "horizon_years": int(horizon),
                "retrieval_config_name": EXACT_REFERENCE_CONFIG,
                "shortlist_pair_count": None,
                "retrieval_elapsed_seconds": exact_elapsed,
                "lsh_bucket_length": None,
                "lsh_num_hash_tables": None,
            }
        )

        for configuration in configurations:
            approximate_matches, shortlist_count, elapsed = rank_lsh_shortlist_matches(
                represented,
                queries,
                configuration=configuration,
                top_k=top_k,
                as_of_year=resolved_as_of_year,
            )
            all_matches.append(approximate_matches)
            runtime_rows.append(
                {
                    "horizon_years": int(horizon),
                    "retrieval_config_name": configuration.name,
                    "shortlist_pair_count": shortlist_count,
                    "retrieval_elapsed_seconds": elapsed,
                    "lsh_bucket_length": configuration.bucket_length,
                    "lsh_num_hash_tables": configuration.num_hash_tables,
                }
            )

    matches = all_matches[0]
    for frame in all_matches[1:]:
        matches = matches.unionByName(frame)
    query_evaluation = build_query_evaluation(
        matches,
        top_k=top_k,
        configuration_names=tuple(configuration.name for configuration in configurations),
    )
    summary = build_scalable_summary(query_evaluation, runtime_rows=runtime_rows)
    eligible_queries = _add_query_dimensions(
        modeling_panel.where(
            (functions.col("forecast_origin_year") == resolved_as_of_year)
            & (functions.col("horizon_years") == horizons[0])
        )
    )
    selected_dimensions = eligible_queries.where(
        functions.col("geoid_2020").isin(*selected_geoids)
    )
    coverage = build_benchmark_coverage(eligible_queries, selected_dimensions)
    return ScalableAnalogueRun(
        run_id=run_id,
        built_at_utc=built_at_utc,
        as_of_year=resolved_as_of_year,
        matches=_add_lineage(
            matches,
            run_id=run_id,
            built_at_utc=built_at_utc,
            as_of_year=resolved_as_of_year,
            queries_per_group=queries_per_group,
        ),
        query_evaluation=_add_lineage(
            query_evaluation,
            run_id=run_id,
            built_at_utc=built_at_utc,
            as_of_year=resolved_as_of_year,
            queries_per_group=queries_per_group,
        ),
        summary=_add_lineage(
            summary,
            run_id=run_id,
            built_at_utc=built_at_utc,
            as_of_year=resolved_as_of_year,
            queries_per_group=queries_per_group,
        ),
        coverage=_add_lineage(
            coverage,
            run_id=run_id,
            built_at_utc=built_at_utc,
            as_of_year=resolved_as_of_year,
            queries_per_group=queries_per_group,
        ),
    )

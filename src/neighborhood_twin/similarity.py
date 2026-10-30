"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Interpretable current-state neighborhood similarity baseline utilities.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from neighborhood_twin.products import SIMILARITY_FEATURE_COLUMNS

SIMILARITY_MODEL_SCHEMA_VERSION = "1.1.0"
SIMILARITY_MATCH_TABLE = "similarity_baseline_match"
SIMILARITY_SUMMARY_TABLE = "similarity_baseline_summary"
DEFAULT_PCA_COMPONENTS = 6

LOG_TRANSFORM_FEATURES = (
    "population_total_estimate",
    "housing_units_total_estimate",
    "median_household_income_estimate",
    "median_owner_occupied_value_estimate",
    "median_gross_rent_estimate",
)


@dataclass(frozen=True)
class SimilarityRun:
    """Current-state neighborhood matches and representation comparison summary."""

    run_id: str
    built_at_utc: str
    matches: Any
    summary: Any


def parse_geoid_list(value: str) -> tuple[str, ...]:
    """Parse an optional comma-separated list of eleven-character tract GEOIDs."""

    geoids = tuple(item.strip() for item in value.split(",") if item.strip())
    if len(geoids) != len(set(geoids)):
        raise ValueError("Query GEOIDs must not contain duplicates")
    if any(len(geoid) != 11 or not geoid.isdigit() for geoid in geoids):
        raise ValueError("Every query GEOID must contain exactly eleven digits")
    return geoids


def validate_similarity_features(available_columns: Iterable[str]) -> None:
    """Validate the current similarity feature contract before fitting transforms."""

    missing = sorted(set(SIMILARITY_FEATURE_COLUMNS) - set(available_columns))
    if missing:
        raise ValueError(f"Similarity candidates are missing: {', '.join(missing)}")


def transformed_feature_name(feature: str) -> str:
    """Return the stable name used after a feature's modeling transform."""

    suffix = "log1p" if feature in LOG_TRANSFORM_FEATURES else "identity"
    return f"{feature}__{suffix}"


def _prepare_features(frame: Any) -> tuple[Any, tuple[str, ...]]:
    """Apply documented scale transforms while keeping source fields intact."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    validate_similarity_features(frame.columns)
    prepared = frame
    output_columns = []
    for feature in SIMILARITY_FEATURE_COLUMNS:
        output = transformed_feature_name(feature)
        output_columns.append(output)
        expression = functions.col(feature).cast("double")
        if feature in LOG_TRANSFORM_FEATURES:
            expression = functions.when(
                expression >= 0, functions.log1p(expression)
            )
        prepared = prepared.withColumn(output, expression)
    return prepared, tuple(output_columns)


def _select_queries(
    frame: Any,
    *,
    query_geoids: tuple[str, ...],
    query_state_fips: tuple[str, ...],
    queries_per_state: int,
) -> Any:
    """Select explicit queries or a deterministic, geographically spread demo set."""

    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    if query_geoids:
        queries = frame.where(functions.col("geoid_2020").isin(*query_geoids))
        found = {row[0] for row in queries.select("geoid_2020").collect()}
        missing = sorted(set(query_geoids) - found)
        if missing:
            raise ValueError(f"Query GEOIDs are not similarity candidates: {', '.join(missing)}")
        return queries
    if queries_per_state <= 0:
        raise ValueError("queries_per_state must be positive")
    if not query_state_fips:
        raise ValueError("At least one fallback query state is required")
    ranked = frame.where(functions.col("state_fips").isin(*query_state_fips)).withColumn(
        "_query_rank",
        functions.row_number().over(
            Window.partitionBy("state_fips").orderBy(
                functions.xxhash64("geoid_2020"), "geoid_2020"
            )
        ),
    )
    queries = ranked.where(functions.col("_query_rank") <= queries_per_state).drop(
        "_query_rank"
    )
    if queries.count() != len(query_state_fips) * queries_per_state:
        raise ValueError("Fallback query selection did not find the expected state coverage")
    return queries


def _rank_matches(
    representation: Any,
    queries: Any,
    *,
    representation_name: str,
    vector_column: str,
    top_k: int,
) -> Any:
    """Compute exact Euclidean neighbors for a deliberately small query set."""

    from pyspark.ml.functions import vector_to_array  # type: ignore[import-not-found]
    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    if top_k <= 0:
        raise ValueError("top_k must be positive")
    candidate = representation.select(
        functions.col("geoid_2020").alias("match_geoid_2020"),
        functions.col("state_abbreviation").alias("match_state_abbreviation"),
        functions.col("county_name").alias("match_county_name"),
        functions.col("tract_name").alias("match_tract_name"),
        vector_to_array(vector_column).alias("_match_vector"),
    )
    query = queries.select(
        functions.col("geoid_2020").alias("query_geoid_2020"),
        functions.col("state_abbreviation").alias("query_state_abbreviation"),
        functions.col("county_name").alias("query_county_name"),
        functions.col("tract_name").alias("query_tract_name"),
        vector_to_array(vector_column).alias("_query_vector"),
    )
    squared_terms = functions.transform(
        functions.arrays_zip("_query_vector", "_match_vector"),
        lambda pair: functions.pow(pair["_query_vector"] - pair["_match_vector"], 2),
    )
    pairs = (
        query.crossJoin(candidate)
        .where(functions.col("query_geoid_2020") != functions.col("match_geoid_2020"))
        .withColumn(
            "similarity_distance",
            functions.sqrt(
                functions.aggregate(squared_terms, functions.lit(0.0), lambda x, y: x + y)
            ),
        )
        .withColumn("representation_name", functions.lit(representation_name))
    )
    ranking = Window.partitionBy("query_geoid_2020", "representation_name").orderBy(
        "similarity_distance", "match_geoid_2020"
    )
    return (
        pairs.withColumn("match_rank", functions.row_number().over(ranking))
        .where(functions.col("match_rank") <= top_k)
        .drop("_query_vector", "_match_vector")
    )


def _representation_summary(matches: Any, *, feature_count: int, pca_variance: float) -> Any:
    """Summarize separation, geography, and raw-versus-PCA neighbor overlap."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    summary = matches.groupBy("representation_name").agg(
        functions.countDistinct("query_geoid_2020").alias("query_count"),
        functions.count(functions.lit(1)).alias("match_count"),
        functions.avg("similarity_distance").alias("mean_similarity_distance"),
        functions.percentile_approx("similarity_distance", 0.5, 10000).alias(
            "median_similarity_distance"
        ),
        functions.percentile_approx("similarity_distance", 0.1, 10000).alias(
            "p10_similarity_distance"
        ),
        functions.percentile_approx("similarity_distance", 0.25, 10000).alias(
            "p25_similarity_distance"
        ),
        functions.percentile_approx("similarity_distance", 0.75, 10000).alias(
            "p75_similarity_distance"
        ),
        functions.percentile_approx("similarity_distance", 0.9, 10000).alias(
            "p90_similarity_distance"
        ),
        functions.avg(
            functions.when(
                functions.col("query_state_abbreviation")
                != functions.col("match_state_abbreviation"),
                1.0,
            ).otherwise(0.0)
        ).alias("cross_state_match_share"),
        functions.avg(
            functions.when(
                (
                    functions.col("query_state_abbreviation")
                    == functions.col("match_state_abbreviation")
                )
                & (functions.col("query_county_name") == functions.col("match_county_name")),
                1.0,
            ).otherwise(0.0)
        ).alias("same_county_match_share"),
    )
    raw = matches.where(functions.col("representation_name") == "standardized_raw").select(
        "query_geoid_2020", "match_geoid_2020"
    )
    pca = matches.where(functions.col("representation_name") == "pca").select(
        "query_geoid_2020", "match_geoid_2020"
    )
    overlap = (
        raw.join(pca, ["query_geoid_2020", "match_geoid_2020"], "inner")
        .groupBy("query_geoid_2020")
        .agg(functions.count(functions.lit(1)).alias("overlap_count"))
        .agg(functions.avg("overlap_count").alias("mean_top_k_overlap"))
        .first()["mean_top_k_overlap"]
    )
    return (
        summary.withColumn("feature_count", functions.lit(feature_count))
        .withColumn("pca_explained_variance", functions.lit(float(pca_variance)))
        .withColumn("mean_raw_pca_top_k_overlap", functions.lit(float(overlap or 0.0)))
        .withColumn(
            "mean_raw_pca_top_k_overlap_share",
            functions.lit(float(overlap or 0.0))
            / functions.greatest(
                functions.col("match_count") / functions.col("query_count"),
                functions.lit(1.0),
            ),
        )
        .withColumn(
            "similarity_distance_iqr",
            functions.col("p75_similarity_distance") - functions.col("p25_similarity_distance"),
        )
    )


def build_similarity_baseline_run(
    frame: Any,
    *,
    query_geoids: tuple[str, ...] = (),
    query_state_fips: tuple[str, ...] = ("04", "26", "42"),
    queries_per_state: int = 2,
    top_k: int = 10,
    pca_components: int = DEFAULT_PCA_COMPONENTS,
    run_id: str | None = None,
    built_at_utc: str | None = None,
) -> SimilarityRun:
    """Fit current-state raw and PCA representations and retrieve exact neighbors."""

    from pyspark.ml import Pipeline  # type: ignore[import-not-found]
    from pyspark.ml.feature import (  # type: ignore[import-not-found]
        PCA,
        Imputer,
        StandardScaler,
        VectorAssembler,
    )
    from pyspark.sql import functions  # type: ignore[import-not-found]

    if pca_components <= 0 or pca_components > len(SIMILARITY_FEATURE_COLUMNS):
        raise ValueError("pca_components must be between one and the feature count")
    prepared, transformed_columns = _prepare_features(frame)
    imputed_columns = tuple(f"{column}__imputed" for column in transformed_columns)
    pipeline = Pipeline(
        stages=[
            Imputer(
                strategy="median",
                inputCols=list(transformed_columns),
                outputCols=list(imputed_columns),
            ),
            VectorAssembler(inputCols=list(imputed_columns), outputCol="_raw_vector"),
            StandardScaler(
                inputCol="_raw_vector",
                outputCol="standardized_vector",
                withMean=True,
                withStd=True,
            ),
            PCA(
                k=pca_components,
                inputCol="standardized_vector",
                outputCol="pca_vector",
            ),
        ]
    )
    model = pipeline.fit(prepared)
    representation = model.transform(prepared).cache()
    queries = _select_queries(
        representation,
        query_geoids=query_geoids,
        query_state_fips=query_state_fips,
        queries_per_state=queries_per_state,
    )
    raw_matches = _rank_matches(
        representation,
        queries,
        representation_name="standardized_raw",
        vector_column="standardized_vector",
        top_k=top_k,
    )
    pca_matches = _rank_matches(
        representation,
        queries,
        representation_name="pca",
        vector_column="pca_vector",
        top_k=top_k,
    )
    run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    built_at_utc = built_at_utc or datetime.now(UTC).isoformat()
    matches = (
        raw_matches.unionByName(pca_matches)
        .withColumn(
            "similarity_model_schema_version",
            functions.lit(SIMILARITY_MODEL_SCHEMA_VERSION),
        )
        .withColumn("similarity_run_id", functions.lit(run_id))
        .withColumn(
            "similarity_built_at_utc", functions.to_timestamp(functions.lit(built_at_utc))
        )
    )
    pca_model = model.stages[-1]
    explained_variance = sum(float(value) for value in pca_model.explainedVariance)
    summary = (
        _representation_summary(
            matches,
            feature_count=len(SIMILARITY_FEATURE_COLUMNS),
            pca_variance=explained_variance,
        )
        .withColumn(
            "similarity_model_schema_version",
            functions.lit(SIMILARITY_MODEL_SCHEMA_VERSION),
        )
        .withColumn("similarity_run_id", functions.lit(run_id))
        .withColumn(
            "similarity_built_at_utc", functions.to_timestamp(functions.lit(built_at_utc))
        )
    )
    return SimilarityRun(run_id, built_at_utc, matches, summary)

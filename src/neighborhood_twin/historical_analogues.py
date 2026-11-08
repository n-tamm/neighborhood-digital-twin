"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Leakage-safe historical analogue retrieval and development evaluation utilities.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from math import sqrt
from typing import Any

HISTORICAL_ANALOGUE_SCHEMA_VERSION = "1.0.0"
HISTORICAL_ANALOGUE_MATCH_TABLE = "historical_analogue_match"
HISTORICAL_ANALOGUE_PREDICTION_TABLE = "historical_analogue_prediction"
HISTORICAL_ANALOGUE_SCORECARD_TABLE = "historical_analogue_scorecard"
HISTORICAL_ANALOGUE_SUMMARY_TABLE = "historical_analogue_summary"

DEFAULT_HORIZONS = (1, 3)
DEFAULT_PCA_COMPONENTS = 6
DEFAULT_COMPARATOR_MODELS = (
    "zero_change",
    "state_current_trend",
    "regularized_linear",
)

ANALOGUE_FEATURE_FAMILIES: dict[str, tuple[str, ...]] = {
    "community_scale": (
        "analogue_log_population",
        "analogue_log_housing_units",
    ),
    "occupancy_tenure": (
        "analogue_occupancy_rate",
        "analogue_owner_occupancy_rate",
    ),
    "housing_structure": (
        "analogue_single_family_share",
        "analogue_multifamily_share",
        "analogue_mobile_home_share",
    ),
    "affordability": (
        "analogue_home_value_to_income",
        "analogue_annual_rent_to_income",
    ),
    "market_trajectory": (
        "analogue_recent_three_year_hpi_change",
        "analogue_recent_five_year_hpi_volatility",
        "analogue_tract_minus_state_change",
    ),
}

ANALOGUE_FEATURE_COLUMNS = tuple(
    feature
    for family_features in ANALOGUE_FEATURE_FAMILIES.values()
    for feature in family_features
)

ANALOGUE_SOURCE_COLUMNS = (
    "population_total_estimate",
    "housing_units_total_estimate",
    "occupancy_rate_estimate",
    "owner_occupancy_rate_estimate",
    "single_family_share_estimate",
    "multifamily_share_estimate",
    "mobile_home_share_estimate",
    "median_household_income_estimate",
    "median_owner_occupied_value_estimate",
    "median_gross_rent_estimate",
    "hpi_recent_3_year_mean_change_pct",
    "hpi_recent_5_year_change_stddev_pct",
    "origin_annual_change_pct",
    "state_origin_mean_annual_change_pct",
)

ANALOGUE_REQUIRED_COLUMNS = (
    "geoid_2020",
    "state_abbreviation",
    "county_name",
    "region_name",
    "forecast_origin_year",
    "horizon_years",
    "target_end_year",
    "target_cumulative_log_change",
    "target_annualized_change_pct",
    "target_is_observed",
    "temporal_role",
    "geographic_role",
    "modeling_cohort",
    "eligible_for_point_model_fit",
    *ANALOGUE_SOURCE_COLUMNS,
)


@dataclass(frozen=True)
class HistoricalAnalogueRun:
    """Published historical matches, predictions, diagnostics, and scorecards."""

    run_id: str
    built_at_utc: str
    matches: Any
    predictions: Any
    summary: Any
    scorecard: Any


def latest_candidate_origin_year(query_origin_year: int, horizon_years: int) -> int:
    """Return the latest candidate origin whose outcome is known by the query year."""

    if horizon_years <= 0:
        raise ValueError("horizon_years must be positive")
    return query_origin_year - horizon_years


def analogue_feature_weights() -> tuple[float, ...]:
    """Return per-feature weights with equal total squared weight per feature family."""

    weights: dict[str, float] = {}
    for family_features in ANALOGUE_FEATURE_FAMILIES.values():
        feature_weight = 1.0 / len(family_features)
        weights.update({feature: feature_weight for feature in family_features})
    return tuple(weights[feature] for feature in ANALOGUE_FEATURE_COLUMNS)


def analogue_feature_multipliers() -> tuple[float, ...]:
    """Return vector multipliers that implement the declared squared-distance weights."""

    return tuple(sqrt(weight) for weight in analogue_feature_weights())


def validate_analogue_columns(available_columns: Iterable[str]) -> None:
    """Fail clearly when the modeling panel does not satisfy the analogue contract."""

    missing = sorted(set(ANALOGUE_REQUIRED_COLUMNS) - set(available_columns))
    if missing:
        raise ValueError(f"Historical analogue input is missing: {', '.join(missing)}")


def validate_analogue_settings(
    *,
    horizons: tuple[int, ...],
    queries_per_group: int,
    top_k: int,
    pca_components: int,
) -> None:
    """Validate deterministic query, retrieval, and representation settings."""

    if not horizons or any(horizon <= 0 for horizon in horizons):
        raise ValueError("horizons must contain positive integers")
    if len(horizons) != len(set(horizons)):
        raise ValueError("horizons must not contain duplicates")
    if queries_per_group <= 0:
        raise ValueError("queries_per_group must be positive")
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    if pca_components <= 0 or pca_components > len(ANALOGUE_FEATURE_COLUMNS):
        raise ValueError("pca_components must be between one and the feature count")


def prepare_analogue_features(frame: Any) -> Any:
    """Derive time-comparable analogue inputs without discarding their source columns."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    validate_analogue_columns(frame.columns)
    positive_income = functions.col("median_household_income_estimate") > 0
    return (
        frame.withColumn(
            "analogue_log_population",
            functions.when(
                functions.col("population_total_estimate") >= 0,
                functions.log1p(functions.col("population_total_estimate").cast("double")),
            ),
        )
        .withColumn(
            "analogue_log_housing_units",
            functions.when(
                functions.col("housing_units_total_estimate") >= 0,
                functions.log1p(functions.col("housing_units_total_estimate").cast("double")),
            ),
        )
        .withColumn(
            "analogue_occupancy_rate",
            functions.col("occupancy_rate_estimate").cast("double"),
        )
        .withColumn(
            "analogue_owner_occupancy_rate",
            functions.col("owner_occupancy_rate_estimate").cast("double"),
        )
        .withColumn(
            "analogue_single_family_share",
            functions.col("single_family_share_estimate").cast("double"),
        )
        .withColumn(
            "analogue_multifamily_share",
            functions.col("multifamily_share_estimate").cast("double"),
        )
        .withColumn(
            "analogue_mobile_home_share",
            functions.col("mobile_home_share_estimate").cast("double"),
        )
        .withColumn(
            "analogue_home_value_to_income",
            functions.when(
                positive_income,
                functions.col("median_owner_occupied_value_estimate")
                / functions.col("median_household_income_estimate"),
            ).cast("double"),
        )
        .withColumn(
            "analogue_annual_rent_to_income",
            functions.when(
                positive_income,
                functions.col("median_gross_rent_estimate")
                * functions.lit(12.0)
                / functions.col("median_household_income_estimate"),
            ).cast("double"),
        )
        .withColumn(
            "analogue_recent_three_year_hpi_change",
            functions.col("hpi_recent_3_year_mean_change_pct").cast("double"),
        )
        .withColumn(
            "analogue_recent_five_year_hpi_volatility",
            functions.col("hpi_recent_5_year_change_stddev_pct").cast("double"),
        )
        .withColumn(
            "analogue_tract_minus_state_change",
            (
                functions.col("origin_annual_change_pct")
                - functions.col("state_origin_mean_annual_change_pct")
            ).cast("double"),
        )
    )


def fit_analogue_preprocessing(frame: Any) -> Any:
    """Fit training-only imputation and standardization and transform the full horizon frame."""

    from pyspark.ml import Pipeline  # type: ignore[import-not-found]
    from pyspark.ml.feature import (  # type: ignore[import-not-found]
        Imputer,
        StandardScaler,
        VectorAssembler,
    )
    from pyspark.sql import functions  # type: ignore[import-not-found]

    prepared = prepare_analogue_features(frame)
    training = prepared.where(
        functions.col("eligible_for_point_model_fit") & functions.col("target_is_observed")
    )
    if training.limit(1).count() == 0:
        raise ValueError("No eligible training rows were available for analogue preprocessing")
    imputed_columns = tuple(f"{column}__imputed" for column in ANALOGUE_FEATURE_COLUMNS)
    pipeline = Pipeline(
        stages=[
            Imputer(
                strategy="median",
                inputCols=list(ANALOGUE_FEATURE_COLUMNS),
                outputCols=list(imputed_columns),
            ),
            VectorAssembler(
                inputCols=list(imputed_columns),
                outputCol="_analogue_unscaled_vector",
                handleInvalid="error",
            ),
            StandardScaler(
                inputCol="_analogue_unscaled_vector",
                outputCol="_analogue_standardized_vector",
                withMean=True,
                withStd=True,
            ),
        ]
    )
    return pipeline.fit(training).transform(prepared)


def add_weighted_analogue_vector(
    frame: Any,
    *,
    multipliers: tuple[float, ...] | None = None,
    output_column: str = "analogue_weighted_vector",
) -> Any:
    """Apply declared feature multipliers to a standardized analogue feature vector."""

    resolved_multipliers = multipliers or analogue_feature_multipliers()
    if len(resolved_multipliers) != len(ANALOGUE_FEATURE_COLUMNS):
        raise ValueError("Analogue multipliers must match the governed feature count")

    from pyspark.ml.feature import ElementwiseProduct  # type: ignore[import-not-found]
    from pyspark.ml.linalg import Vectors  # type: ignore[import-not-found]

    return ElementwiseProduct(
        scalingVec=Vectors.dense(resolved_multipliers),
        inputCol="_analogue_standardized_vector",
        outputCol=output_column,
    ).transform(frame)


def fit_analogue_pca(
    frame: Any,
    *,
    pca_components: int,
    input_column: str = "analogue_weighted_vector",
    output_column: str = "analogue_pca_vector",
) -> tuple[Any, float]:
    """Fit PCA on eligible training vectors and transform the full horizon frame."""

    if pca_components <= 0 or pca_components > len(ANALOGUE_FEATURE_COLUMNS):
        raise ValueError("pca_components must be between one and the feature count")

    from pyspark.ml.feature import PCA  # type: ignore[import-not-found]
    from pyspark.sql import functions  # type: ignore[import-not-found]

    training = frame.where(
        functions.col("eligible_for_point_model_fit") & functions.col("target_is_observed")
    )
    pca_model = PCA(
        k=pca_components,
        inputCol=input_column,
        outputCol=output_column,
    ).fit(training)
    transformed = pca_model.transform(frame)
    explained_variance = sum(float(value) for value in pca_model.explainedVariance)
    return transformed, explained_variance


def _fit_representation(frame: Any, *, pca_components: int) -> tuple[Any, float]:
    """Fit horizon-specific imputation, scaling, family weighting, and PCA on training rows."""

    standardized = fit_analogue_preprocessing(frame)
    weighted = add_weighted_analogue_vector(standardized)
    return fit_analogue_pca(weighted, pca_components=pca_components)


def _comparator_complete_keys(
    forecast_predictions: Any,
    *,
    comparator_models: tuple[str, ...],
) -> Any:
    """Return query keys covered by every declared supervised or fixed comparator."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        forecast_predictions.where(functions.col("model_name").isin(*comparator_models))
        .groupBy("geoid_2020", "forecast_origin_year", "horizon_years")
        .agg(functions.countDistinct("model_name").alias("_comparator_count"))
        .where(functions.col("_comparator_count") == len(comparator_models))
        .drop("_comparator_count")
    )


def _select_queries(
    frame: Any,
    *,
    queries_per_group: int,
    comparator_keys: Any,
) -> Any:
    """Choose a deterministic validation sample across time, region, and transfer role."""

    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    eligible = (
        frame.where(
            (functions.col("temporal_role") == "validation")
            & functions.col("target_is_observed")
        )
        .join(
            comparator_keys,
            ["geoid_2020", "forecast_origin_year", "horizon_years"],
            "inner",
        )
        .withColumn(
            "_query_rank",
            functions.row_number().over(
                Window.partitionBy(
                    "horizon_years",
                    "forecast_origin_year",
                    "region_name",
                    "geographic_role",
                ).orderBy(functions.xxhash64("geoid_2020"), "geoid_2020")
            ),
        )
    )
    queries = eligible.where(functions.col("_query_rank") <= queries_per_group).drop(
        "_query_rank"
    )
    if queries.limit(1).count() == 0:
        raise ValueError("No validation queries satisfied the analogue and comparator contract")
    return queries


def rank_analogue_matches(
    representation: Any,
    queries: Any,
    *,
    representation_name: str,
    vector_column: str,
    top_k: int,
    unique_candidate_tract: bool = False,
) -> Any:
    """Retrieve exact time-safe neighbors with an optional unique-candidate-tract rule."""

    from pyspark.ml.functions import vector_to_array  # type: ignore[import-not-found]
    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    query = queries.select(
        functions.col("geoid_2020").alias("query_geoid_2020"),
        functions.col("forecast_origin_year").alias("query_origin_year"),
        "horizon_years",
        functions.col("target_end_year").alias("query_target_end_year"),
        functions.col("target_cumulative_log_change").alias(
            "query_target_cumulative_log_change"
        ),
        functions.col("target_annualized_change_pct").alias(
            "query_target_annualized_change_pct"
        ),
        functions.col("state_abbreviation").alias("query_state_abbreviation"),
        functions.col("county_name").alias("query_county_name"),
        functions.col("region_name").alias("query_region_name"),
        functions.col("modeling_cohort").alias("query_modeling_cohort"),
        functions.col("temporal_role").alias("query_temporal_role"),
        functions.col("geographic_role").alias("query_geographic_role"),
        vector_to_array(vector_column).alias("_query_vector"),
    )
    candidate = representation.where(
        functions.col("target_is_observed")
        & (functions.col("geographic_role") == "geographic_development")
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
        vector_to_array(vector_column).alias("_candidate_vector"),
    )
    squared_terms = functions.transform(
        functions.arrays_zip("_query_vector", "_candidate_vector"),
        lambda pair: functions.pow(pair["_query_vector"] - pair["_candidate_vector"], 2),
    )
    pairs = (
        functions.broadcast(query)
        .crossJoin(candidate)
        .where(functions.col("candidate_horizon_years") == functions.col("horizon_years"))
        .where(functions.col("query_geoid_2020") != functions.col("candidate_geoid_2020"))
        .where(functions.col("candidate_target_end_year") <= functions.col("query_origin_year"))
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
        .withColumn("representation_name", functions.lit(representation_name))
        .withColumn(
            "candidate_age_years",
            functions.col("query_origin_year") - functions.col("candidate_origin_year"),
        )
    )
    if unique_candidate_tract:
        candidate_ranking = Window.partitionBy(
            "query_geoid_2020",
            "query_origin_year",
            "horizon_years",
            "representation_name",
            "candidate_geoid_2020",
        ).orderBy(
            "similarity_distance",
            functions.col("candidate_origin_year").desc(),
        )
        pairs = (
            pairs.withColumn(
                "_candidate_tract_rank",
                functions.row_number().over(candidate_ranking),
            )
            .where(functions.col("_candidate_tract_rank") == 1)
            .drop("_candidate_tract_rank")
        )
    ranking = Window.partitionBy(
        "query_geoid_2020",
        "query_origin_year",
        "horizon_years",
        "representation_name",
    ).orderBy(
        "similarity_distance",
        functions.col("candidate_origin_year").desc(),
        "candidate_geoid_2020",
    )
    return (
        pairs.withColumn("match_rank", functions.row_number().over(ranking))
        .where(functions.col("match_rank") <= top_k)
        .withColumn(
            "unique_candidate_tract",
            functions.lit(unique_candidate_tract),
        )
        .drop("candidate_horizon_years", "_query_vector", "_candidate_vector")
    )


def _analogue_predictions(matches: Any, *, distance_epsilon: float = 1e-9) -> Any:
    """Create median and inverse-distance analogue outcome estimates from ranked matches."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    query_columns = (
        "query_geoid_2020",
        "query_origin_year",
        "horizon_years",
        "query_target_end_year",
        "query_target_cumulative_log_change",
        "query_target_annualized_change_pct",
        "query_state_abbreviation",
        "query_county_name",
        "query_region_name",
        "query_modeling_cohort",
        "query_temporal_role",
        "query_geographic_role",
        "representation_name",
    )
    weight = 1.0 / (functions.col("similarity_distance") + functions.lit(distance_epsilon))
    aggregated = matches.groupBy(*query_columns).agg(
        functions.count(functions.lit(1)).alias("analogue_match_count"),
        functions.avg("similarity_distance").alias("mean_similarity_distance"),
        functions.percentile_approx(
            "candidate_target_cumulative_log_change", 0.1, 10000
        ).alias("analogue_outcome_p10_log_change"),
        functions.percentile_approx(
            "candidate_target_cumulative_log_change", 0.5, 10000
        ).alias("analogue_outcome_median_log_change"),
        functions.percentile_approx(
            "candidate_target_cumulative_log_change", 0.9, 10000
        ).alias("analogue_outcome_p90_log_change"),
        (
            functions.sum(
                functions.col("candidate_target_cumulative_log_change") * weight
            )
            / functions.sum(weight)
        ).alias("analogue_outcome_inverse_distance_log_change"),
    )
    common_columns = [
        *query_columns,
        "analogue_match_count",
        "mean_similarity_distance",
        "analogue_outcome_p10_log_change",
        "analogue_outcome_p90_log_change",
    ]
    median = aggregated.select(
        *common_columns,
        functions.concat(
            functions.lit("analogue_median_"), functions.col("representation_name")
        ).alias("prediction_method"),
        functions.col("analogue_outcome_median_log_change").alias(
            "prediction_cumulative_log_change"
        ),
    )
    weighted = aggregated.select(
        *common_columns,
        functions.concat(
            functions.lit("analogue_inverse_distance_"),
            functions.col("representation_name"),
        ).alias("prediction_method"),
        functions.col("analogue_outcome_inverse_distance_log_change").alias(
            "prediction_cumulative_log_change"
        ),
    )
    return median.unionByName(weighted).withColumn(
        "prediction_source", functions.lit("historical_analogue")
    )


def _comparator_predictions(
    queries: Any,
    forecast_predictions: Any,
    *,
    comparator_models: tuple[str, ...],
) -> Any:
    """Select declared forecast comparators on exactly the sampled analogue query rows."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    query_columns = queries.select(
        functions.col("geoid_2020").alias("query_geoid_2020"),
        functions.col("forecast_origin_year").alias("query_origin_year"),
        "horizon_years",
        functions.col("target_end_year").alias("query_target_end_year"),
        functions.col("target_cumulative_log_change").alias(
            "query_target_cumulative_log_change"
        ),
        functions.col("target_annualized_change_pct").alias(
            "query_target_annualized_change_pct"
        ),
        functions.col("state_abbreviation").alias("query_state_abbreviation"),
        functions.col("county_name").alias("query_county_name"),
        functions.col("region_name").alias("query_region_name"),
        functions.col("modeling_cohort").alias("query_modeling_cohort"),
        functions.col("temporal_role").alias("query_temporal_role"),
        functions.col("geographic_role").alias("query_geographic_role"),
    )
    forecasts = forecast_predictions.where(
        functions.col("model_name").isin(*comparator_models)
    ).select(
        functions.col("geoid_2020").alias("query_geoid_2020"),
        functions.col("forecast_origin_year").alias("query_origin_year"),
        "horizon_years",
        functions.col("model_name").alias("prediction_method"),
        "prediction_cumulative_log_change",
    )
    return (
        query_columns.join(
            forecasts,
            ["query_geoid_2020", "query_origin_year", "horizon_years"],
            "inner",
        )
        .withColumn("representation_name", functions.lit(None).cast("string"))
        .withColumn("analogue_match_count", functions.lit(None).cast("long"))
        .withColumn("mean_similarity_distance", functions.lit(None).cast("double"))
        .withColumn(
            "analogue_outcome_p10_log_change", functions.lit(None).cast("double")
        )
        .withColumn(
            "analogue_outcome_p90_log_change", functions.lit(None).cast("double")
        )
        .withColumn("prediction_source", functions.lit("forecast_comparator"))
    )


def _add_prediction_fields(
    predictions: Any,
    *,
    run_id: str,
    built_at_utc: str,
) -> Any:
    """Attach readable predictions, errors, and versioned run lineage."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        predictions.withColumn(
            "prediction_annualized_change_pct",
            (
                functions.exp(
                    functions.col("prediction_cumulative_log_change")
                    / functions.col("horizon_years")
                )
                - 1
            )
            * 100,
        )
        .withColumn(
            "residual_cumulative_log_change",
            functions.col("query_target_cumulative_log_change")
            - functions.col("prediction_cumulative_log_change"),
        )
        .withColumn(
            "absolute_error_cumulative_log_change",
            functions.abs(functions.col("residual_cumulative_log_change")),
        )
        .withColumn(
            "evaluation_geography",
            functions.when(
                functions.col("query_geographic_role") == "geographic_holdout",
                functions.lit("held_out_state"),
            ).otherwise(functions.lit("development_states")),
        )
        .withColumn(
            "historical_analogue_schema_version",
            functions.lit(HISTORICAL_ANALOGUE_SCHEMA_VERSION),
        )
        .withColumn("historical_analogue_run_id", functions.lit(run_id))
        .withColumn(
            "historical_analogue_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
    )


def build_historical_analogue_scorecard(
    predictions: Any,
    *,
    additional_slices: tuple[tuple[str, str], ...] = (),
) -> Any:
    """Summarize analogue and forecast-comparator errors on identical sampled queries."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    base_columns = (
        "prediction_method",
        "prediction_source",
        "horizon_years",
        "historical_analogue_schema_version",
        "historical_analogue_run_id",
        "historical_analogue_built_at_utc",
    )
    slices = [
        predictions.withColumn("slice_name", functions.lit("overall")).withColumn(
            "slice_value", functions.lit("all")
        ),
        predictions.withColumn("slice_name", functions.lit("query_origin_year")).withColumn(
            "slice_value", functions.col("query_origin_year").cast("string")
        ),
        predictions.withColumn("slice_name", functions.lit("evaluation_geography")).withColumn(
            "slice_value", functions.col("evaluation_geography")
        ),
        predictions.withColumn("slice_name", functions.lit("census_region")).withColumn(
            "slice_value", functions.col("query_region_name")
        ),
        predictions.withColumn("slice_name", functions.lit("modeling_cohort")).withColumn(
            "slice_value", functions.col("query_modeling_cohort")
        ),
    ]
    for slice_name, column_name in additional_slices:
        if column_name not in predictions.columns:
            raise ValueError(
                f"Scorecard slice {slice_name!r} requires missing column {column_name!r}"
            )
        slices.append(
            predictions.withColumn("slice_name", functions.lit(slice_name)).withColumn(
                "slice_value", functions.col(column_name).cast("string")
            )
        )
    sliced = slices[0]
    for current in slices[1:]:
        sliced = sliced.unionByName(current)
    squared_error = functions.pow(functions.col("residual_cumulative_log_change"), 2)
    direction_correct = functions.when(
        functions.signum(functions.col("prediction_cumulative_log_change"))
        == functions.signum(functions.col("query_target_cumulative_log_change")),
        1.0,
    ).otherwise(0.0)
    target_positive = functions.when(
        functions.col("query_target_cumulative_log_change") > 0, 1.0
    ).otherwise(0.0)
    summary = (
        sliced.groupBy(*base_columns, "slice_name", "slice_value")
        .agg(
            functions.count(functions.lit(1)).alias("query_count"),
            functions.countDistinct("query_geoid_2020").alias("query_tract_count"),
            functions.avg("absolute_error_cumulative_log_change").alias("mae_log_change"),
            functions.sqrt(functions.avg(squared_error)).alias("rmse_log_change"),
            functions.percentile_approx(
                "absolute_error_cumulative_log_change", 0.5, 10000
            ).alias("median_absolute_error_log_change"),
            functions.percentile_approx(
                "absolute_error_cumulative_log_change", 0.9, 10000
            ).alias("p90_absolute_error_log_change"),
            functions.avg("residual_cumulative_log_change").alias("mean_error_log_change"),
            functions.avg(squared_error).alias("mean_squared_error_log_change"),
            functions.var_pop("query_target_cumulative_log_change").alias(
                "target_variance_log_change"
            ),
            functions.avg(direction_correct).alias("directional_accuracy"),
            functions.avg(target_positive).alias("target_positive_share"),
            functions.avg("analogue_match_count").alias("mean_analogue_match_count"),
        )
        .withColumn(
            "r_squared",
            functions.when(
                functions.col("target_variance_log_change") > 0,
                1
                - functions.col("mean_squared_error_log_change")
                / functions.col("target_variance_log_change"),
            ),
        )
        .withColumn(
            "majority_direction_accuracy",
            functions.greatest(
                functions.col("target_positive_share"),
                1 - functions.col("target_positive_share"),
            ),
        )
        .withColumn(
            "directional_accuracy_lift",
            functions.col("directional_accuracy")
            - functions.col("majority_direction_accuracy"),
        )
        .drop("mean_squared_error_log_change", "target_variance_log_change")
    )
    reference_keys = [
        "horizon_years",
        "historical_analogue_schema_version",
        "historical_analogue_run_id",
        "historical_analogue_built_at_utc",
        "slice_name",
        "slice_value",
    ]
    zero = summary.where(functions.col("prediction_method") == "zero_change").select(
        *reference_keys,
        functions.col("mae_log_change").alias("zero_change_mae_log_change"),
        functions.col("rmse_log_change").alias("zero_change_rmse_log_change"),
    )
    return (
        summary.join(zero, reference_keys, "left")
        .withColumn(
            "mae_skill_vs_zero_change",
            functions.when(
                functions.col("zero_change_mae_log_change") > 0,
                1
                - functions.col("mae_log_change")
                / functions.col("zero_change_mae_log_change"),
            ),
        )
        .withColumn(
            "rmse_skill_vs_zero_change",
            functions.when(
                functions.col("zero_change_rmse_log_change") > 0,
                1
                - functions.col("rmse_log_change")
                / functions.col("zero_change_rmse_log_change"),
            ),
        )
        .drop("zero_change_mae_log_change", "zero_change_rmse_log_change")
    )


def _retrieval_summary(matches: Any, *, pca_explained_variance: float) -> Any:
    """Summarize separation, geography, age, and representation overlap by horizon."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    summary = matches.groupBy("horizon_years", "representation_name").agg(
        functions.countDistinct(
            "query_geoid_2020", "query_origin_year"
        ).alias("query_count"),
        functions.count(functions.lit(1)).alias("match_count"),
        functions.avg("similarity_distance").alias("mean_similarity_distance"),
        functions.percentile_approx("similarity_distance", 0.1, 10000).alias(
            "p10_similarity_distance"
        ),
        functions.percentile_approx("similarity_distance", 0.5, 10000).alias(
            "median_similarity_distance"
        ),
        functions.percentile_approx("similarity_distance", 0.9, 10000).alias(
            "p90_similarity_distance"
        ),
        functions.avg("candidate_age_years").alias("mean_candidate_age_years"),
        functions.avg(
            functions.when(
                functions.col("query_state_abbreviation")
                != functions.col("candidate_state_abbreviation"),
                1.0,
            ).otherwise(0.0)
        ).alias("cross_state_match_share"),
        functions.avg(
            functions.when(
                (
                    functions.col("query_state_abbreviation")
                    == functions.col("candidate_state_abbreviation")
                )
                & (functions.col("query_county_name") == functions.col("candidate_county_name")),
                1.0,
            ).otherwise(0.0)
        ).alias("same_county_match_share"),
    )
    raw = matches.where(functions.col("representation_name") == "weighted_standardized").select(
        "query_geoid_2020",
        "query_origin_year",
        "horizon_years",
        "candidate_geoid_2020",
        "candidate_origin_year",
    )
    pca = matches.where(functions.col("representation_name") == "pca").select(
        "query_geoid_2020",
        "query_origin_year",
        "horizon_years",
        "candidate_geoid_2020",
        "candidate_origin_year",
    )
    overlap = (
        raw.join(
            pca,
            [
                "query_geoid_2020",
                "query_origin_year",
                "horizon_years",
                "candidate_geoid_2020",
                "candidate_origin_year",
            ],
            "inner",
        )
        .groupBy("query_geoid_2020", "query_origin_year", "horizon_years")
        .agg(functions.count(functions.lit(1)).alias("top_k_overlap_count"))
        .groupBy("horizon_years")
        .agg(functions.avg("top_k_overlap_count").alias("mean_raw_pca_top_k_overlap"))
    )
    return (
        summary.join(overlap, "horizon_years", "left")
        .withColumn("pca_explained_variance", functions.lit(pca_explained_variance))
        .withColumn(
            "mean_raw_pca_top_k_overlap_share",
            functions.col("mean_raw_pca_top_k_overlap")
            / functions.greatest(
                functions.col("match_count") / functions.col("query_count"),
                functions.lit(1.0),
            ),
        )
    )


def _add_run_lineage(
    frame: Any,
    *,
    run_id: str,
    built_at_utc: str,
) -> Any:
    """Attach the shared historical analogue version and run identifiers."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        frame.withColumn(
            "historical_analogue_schema_version",
            functions.lit(HISTORICAL_ANALOGUE_SCHEMA_VERSION),
        )
        .withColumn("historical_analogue_run_id", functions.lit(run_id))
        .withColumn(
            "historical_analogue_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
    )


def build_historical_analogue_run(
    modeling_panel: Any,
    forecast_predictions: Any,
    *,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS,
    queries_per_group: int = 1,
    top_k: int = 10,
    pca_components: int = DEFAULT_PCA_COMPONENTS,
    unique_candidate_tract: bool = False,
    comparator_models: tuple[str, ...] = DEFAULT_COMPARATOR_MODELS,
    run_id: str | None = None,
    built_at_utc: str | None = None,
) -> HistoricalAnalogueRun:
    """Build time-safe validation analogues and compare their outcomes with forecast baselines."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    validate_analogue_columns(modeling_panel.columns)
    validate_analogue_settings(
        horizons=horizons,
        queries_per_group=queries_per_group,
        top_k=top_k,
        pca_components=pca_components,
    )
    if not comparator_models:
        raise ValueError("At least one forecast comparator is required")
    run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    built_at_utc = built_at_utc or datetime.now(UTC).isoformat()
    comparator_keys = _comparator_complete_keys(
        forecast_predictions,
        comparator_models=comparator_models,
    )

    all_matches = []
    all_analogue_predictions = []
    all_comparator_predictions = []
    all_summaries = []
    for horizon in horizons:
        horizon_frame = modeling_panel.where(functions.col("horizon_years") == int(horizon))
        if horizon_frame.limit(1).count() == 0:
            raise ValueError(f"No modeling rows were available for horizon {horizon}")
        representation, pca_variance = _fit_representation(
            horizon_frame,
            pca_components=pca_components,
        )
        representation = representation.cache()
        horizon_comparator_keys = comparator_keys.where(
            functions.col("horizon_years") == int(horizon)
        )
        queries = _select_queries(
            representation,
            queries_per_group=queries_per_group,
            comparator_keys=horizon_comparator_keys,
        )
        raw_matches = rank_analogue_matches(
            representation,
            queries,
            representation_name="weighted_standardized",
            vector_column="analogue_weighted_vector",
            top_k=top_k,
            unique_candidate_tract=unique_candidate_tract,
        )
        pca_matches = rank_analogue_matches(
            representation,
            queries,
            representation_name="pca",
            vector_column="analogue_pca_vector",
            top_k=top_k,
            unique_candidate_tract=unique_candidate_tract,
        )
        matches = raw_matches.unionByName(pca_matches).cache()
        match_count = matches.count()
        if match_count == 0:
            earliest_query = queries.agg(functions.min("forecast_origin_year")).first()[0]
            raise ValueError(
                "No time-safe analogue candidates were available for "
                f"horizon {horizon} and earliest query origin {earliest_query}"
            )
        all_matches.append(matches)
        all_analogue_predictions.append(_analogue_predictions(matches))
        all_comparator_predictions.append(
            _comparator_predictions(
                queries,
                forecast_predictions,
                comparator_models=comparator_models,
            )
        )
        all_summaries.append(
            _retrieval_summary(matches, pca_explained_variance=pca_variance)
        )

    matches = all_matches[0]
    analogue_predictions = all_analogue_predictions[0]
    comparator_predictions = all_comparator_predictions[0]
    summary = all_summaries[0]
    for frame in all_matches[1:]:
        matches = matches.unionByName(frame)
    for frame in all_analogue_predictions[1:]:
        analogue_predictions = analogue_predictions.unionByName(frame)
    for frame in all_comparator_predictions[1:]:
        comparator_predictions = comparator_predictions.unionByName(frame)
    for frame in all_summaries[1:]:
        summary = summary.unionByName(frame)

    versioned_matches = _add_run_lineage(
        matches,
        run_id=run_id,
        built_at_utc=built_at_utc,
    )
    predictions = _add_prediction_fields(
        analogue_predictions.unionByName(comparator_predictions),
        run_id=run_id,
        built_at_utc=built_at_utc,
    )
    versioned_summary = _add_run_lineage(
        summary,
        run_id=run_id,
        built_at_utc=built_at_utc,
    )
    scorecard = build_historical_analogue_scorecard(predictions)
    return HistoricalAnalogueRun(
        run_id,
        built_at_utc,
        versioned_matches,
        predictions,
        versioned_summary,
        scorecard,
    )

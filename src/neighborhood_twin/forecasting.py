"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Leakage-safe baseline forecasting and validation scorecard utilities.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp, log1p
from typing import Any

FORECAST_MODEL_SCHEMA_VERSION = "1.0.0"
FORECAST_PREDICTION_TABLE = "gold_forecast_baseline_prediction"
FORECAST_SCORECARD_TABLE = "gold_forecast_baseline_scorecard"

BASELINE_MODELS = (
    "zero_change",
    "latest_change_persistence",
    "recent_three_year_mean",
    "county_current_trend",
    "state_current_trend",
)

LINEAR_FEATURE_COLUMNS = (
    "origin_annual_change_pct",
    "hpi_change_1_year_pct",
    "hpi_change_3_year_pct",
    "hpi_change_5_year_pct",
    "hpi_recent_3_year_mean_change_pct",
    "hpi_recent_5_year_change_stddev_pct",
    "hpi_history_observation_count",
    "hpi_history_gap_count",
    "county_origin_mean_annual_change_pct",
    "state_origin_mean_annual_change_pct",
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
    "acs_measurement_age_years",
    "median_household_income_relative_moe",
    "median_owner_occupied_value_relative_moe",
    "median_gross_rent_relative_moe",
)


@dataclass(frozen=True)
class ForecastRun:
    """Published prediction and scorecard frames for one baseline run."""

    run_id: str
    built_at_utc: str
    predictions: Any
    scorecard: Any


def cumulative_log_from_annual_rate(rate_pct: float, horizon_years: int) -> float:
    """Convert an annual percentage rate to a cumulative log change."""

    if horizon_years <= 0:
        raise ValueError("horizon_years must be positive")
    if rate_pct <= -100:
        raise ValueError("rate_pct must be greater than -100")
    return log1p(rate_pct / 100.0) * horizon_years


def annualized_rate_from_cumulative_log(
    cumulative_log_change: float, horizon_years: int
) -> float:
    """Convert a cumulative log change into an annualized percentage rate."""

    if horizon_years <= 0:
        raise ValueError("horizon_years must be positive")
    return (exp(cumulative_log_change / horizon_years) - 1.0) * 100.0


def validate_feature_registry(
    available_columns: Iterable[str],
    feature_columns: tuple[str, ...] = LINEAR_FEATURE_COLUMNS,
) -> None:
    """Fail clearly when a model input table does not satisfy the feature contract."""

    available = set(available_columns)
    missing = sorted(set(feature_columns) - available)
    if missing:
        raise ValueError(f"Modeling panel is missing required features: {', '.join(missing)}")


def housing_composition_band(column: Any, functions: Any) -> Any:
    """Return the shared interpretable single-family housing-share band expression."""

    return (
        functions.when(column.isNull(), functions.lit("Missing"))
        .when(column < 0.25, functions.lit("Under 25%"))
        .when(column < 0.50, functions.lit("25% to under 50%"))
        .when(column < 0.75, functions.lit("50% to under 75%"))
        .otherwise(functions.lit("75% or more"))
    )


def _annual_rate_to_log(column: Any, horizon: Any, functions: Any) -> Any:
    """Create a null-safe Spark expression for annual-rate persistence."""

    return functions.when(
        column.isNotNull() & (column > -100),
        functions.log1p(column / 100.0) * horizon,
    )


def baseline_predictions(frame: Any) -> Any:
    """Create the five fixed no-fit baseline predictions on eligible validation rows."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    eligible = frame.where(
        (functions.col("temporal_role") == "validation")
        & functions.col("target_is_observed")
    )
    horizon = functions.col("horizon_years")
    model_expressions = {
        "zero_change": functions.lit(0.0),
        "latest_change_persistence": _annual_rate_to_log(
            functions.col("hpi_change_1_year_pct"), horizon, functions
        ),
        "recent_three_year_mean": _annual_rate_to_log(
            functions.col("hpi_recent_3_year_mean_change_pct"), horizon, functions
        ),
        "county_current_trend": _annual_rate_to_log(
            functions.col("county_origin_mean_annual_change_pct"), horizon, functions
        ),
        "state_current_trend": _annual_rate_to_log(
            functions.col("state_origin_mean_annual_change_pct"), horizon, functions
        ),
    }
    prediction_structs = [
        functions.struct(
            functions.lit(model_name).alias("model_name"),
            expression.cast("double").alias("prediction_cumulative_log_change"),
        )
        for model_name, expression in model_expressions.items()
    ]
    return (
        eligible.withColumn("_prediction", functions.explode(functions.array(*prediction_structs)))
        .select("*", "_prediction.*")
        .drop("_prediction")
        .where(functions.col("prediction_cumulative_log_change").isNotNull())
    )


def _linear_model_predictions(frame: Any, *, reg_param: float) -> Any:
    """Fit one regularized linear Spark pipeline per horizon and score validation rows."""

    from pyspark.ml import Pipeline  # type: ignore[import-not-found]
    from pyspark.ml.feature import (  # type: ignore[import-not-found]
        Imputer,
        StandardScaler,
        VectorAssembler,
    )
    from pyspark.ml.regression import LinearRegression  # type: ignore[import-not-found]
    from pyspark.sql import functions  # type: ignore[import-not-found]

    if reg_param < 0:
        raise ValueError("reg_param must be nonnegative")
    validate_feature_registry(frame.columns)
    outputs = []
    for horizon in sorted(row[0] for row in frame.select("horizon_years").distinct().collect()):
        horizon_frame = frame.where(functions.col("horizon_years") == int(horizon))
        training = horizon_frame.where(
            functions.col("eligible_for_point_model_fit")
            & functions.col("target_is_observed")
        )
        validation = horizon_frame.where(
            (functions.col("temporal_role") == "validation")
            & functions.col("target_is_observed")
        )
        imputed = tuple(f"{column}__imputed" for column in LINEAR_FEATURE_COLUMNS)
        pipeline = Pipeline(
            stages=[
                Imputer(
                    strategy="median",
                    inputCols=list(LINEAR_FEATURE_COLUMNS),
                    outputCols=list(imputed),
                ),
                VectorAssembler(
                    inputCols=list(imputed),
                    outputCol="_unscaled_features",
                    handleInvalid="error",
                ),
                StandardScaler(
                    inputCol="_unscaled_features",
                    outputCol="_scaled_features",
                    withMean=True,
                    withStd=True,
                ),
                LinearRegression(
                    featuresCol="_scaled_features",
                    labelCol="target_cumulative_log_change",
                    predictionCol="prediction_cumulative_log_change",
                    regParam=reg_param,
                    elasticNetParam=0.0,
                    maxIter=100,
                    standardization=False,
                ),
            ]
        )
        output = pipeline.fit(training).transform(validation).select(
            *frame.columns,
            "prediction_cumulative_log_change",
        )
        outputs.append(output.withColumn("model_name", functions.lit("regularized_linear")))
    if not outputs:
        raise ValueError("No forecast horizons were available to fit")
    combined = outputs[0]
    for output in outputs[1:]:
        combined = combined.unionByName(output)
    return combined


def _add_prediction_fields(frame: Any, *, run_id: str, built_at_utc: str) -> Any:
    """Attach readable predictions, residuals, evaluation cohorts, and lineage."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        frame.withColumn(
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
            functions.col("target_cumulative_log_change")
            - functions.col("prediction_cumulative_log_change"),
        )
        .withColumn(
            "absolute_error_cumulative_log_change",
            functions.abs(functions.col("residual_cumulative_log_change")),
        )
        .withColumn(
            "housing_composition_band",
            housing_composition_band(functions.col("single_family_share_estimate"), functions),
        )
        .withColumn(
            "evaluation_geography",
            functions.when(
                functions.col("geographic_role") == "geographic_holdout",
                functions.lit("held_out_state"),
            ).otherwise(functions.lit("development_states")),
        )
        .withColumn("forecast_model_schema_version", functions.lit(FORECAST_MODEL_SCHEMA_VERSION))
        .withColumn("forecast_run_id", functions.lit(run_id))
        .withColumn(
            "forecast_built_at_utc", functions.to_timestamp(functions.lit(built_at_utc))
        )
    )


def build_forecast_scorecard(predictions: Any) -> Any:
    """Summarize model error across overall, cohort, geography, and housing slices."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    base_columns = (
        "model_name",
        "horizon_years",
        "forecast_model_schema_version",
        "forecast_run_id",
        "forecast_built_at_utc",
    )
    slices = [
        predictions.withColumn("slice_name", functions.lit("overall")).withColumn(
            "slice_value", functions.lit("all")
        ),
        predictions.withColumn("slice_name", functions.lit("modeling_cohort")).withColumn(
            "slice_value", functions.col("modeling_cohort")
        ),
        predictions.withColumn("slice_name", functions.lit("evaluation_geography")).withColumn(
            "slice_value", functions.col("evaluation_geography")
        ),
        predictions.withColumn("slice_name", functions.lit("housing_composition_band")).withColumn(
            "slice_value", functions.col("housing_composition_band")
        ),
        predictions.withColumn("slice_name", functions.lit("state")).withColumn(
            "slice_value", functions.col("state_abbreviation")
        ),
    ]
    sliced = slices[0]
    for current in slices[1:]:
        sliced = sliced.unionByName(current)
    squared_error = functions.pow(functions.col("residual_cumulative_log_change"), 2)
    direction_correct = functions.when(
        functions.signum(functions.col("prediction_cumulative_log_change"))
        == functions.signum(functions.col("target_cumulative_log_change")),
        1.0,
    ).otherwise(0.0)
    return (
        sliced.groupBy(*base_columns, "slice_name", "slice_value")
        .agg(
            functions.count(functions.lit(1)).alias("observation_count"),
            functions.countDistinct("geoid_2020").alias("tract_count"),
            functions.avg("absolute_error_cumulative_log_change").alias("mae_log_change"),
            functions.sqrt(functions.avg(squared_error)).alias("rmse_log_change"),
            functions.percentile_approx(
                "absolute_error_cumulative_log_change", 0.5, 10000
            ).alias("median_absolute_error_log_change"),
            functions.avg(direction_correct).alias("directional_accuracy"),
            functions.avg("target_annualized_change_pct").alias(
                "mean_target_annualized_change_pct"
            ),
            functions.avg("prediction_annualized_change_pct").alias(
                "mean_prediction_annualized_change_pct"
            ),
        )
    )


def build_forecast_baseline_run(
    frame: Any,
    *,
    run_id: str | None = None,
    built_at_utc: str | None = None,
    reg_param: float = 0.05,
) -> ForecastRun:
    """Build fixed and regularized-linear predictions without opening locked tests."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    validate_feature_registry(frame.columns)
    forbidden = frame.where(
        functions.col("eligible_for_locked_temporal_evaluation")
        & (functions.col("temporal_role") != "locked_temporal_test")
    ).limit(1)
    if forbidden.count():
        raise ValueError("Locked temporal evaluation flags do not match the split contract")
    run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    built_at_utc = built_at_utc or datetime.now(UTC).isoformat()
    fixed = baseline_predictions(frame)
    linear = _linear_model_predictions(frame, reg_param=reg_param)
    predictions = _add_prediction_fields(
        fixed.unionByName(linear, allowMissingColumns=True),
        run_id=run_id,
        built_at_utc=built_at_utc,
    )
    if predictions.where(functions.col("temporal_role") != "validation").limit(1).count():
        raise ValueError("Baseline prediction output contains a non-validation row")
    scorecard = build_forecast_scorecard(predictions)
    return ForecastRun(run_id, built_at_utc, predictions, scorecard)

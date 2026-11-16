"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Leakage-safe forecasting candidates and validation scorecard utilities.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp, log1p
from typing import Any

FORECAST_MODEL_SCHEMA_VERSION = "1.4.0"
FORECAST_PREDICTION_TABLE = "forecast_baseline_prediction"
FORECAST_SCORECARD_TABLE = "forecast_baseline_scorecard"
FORECAST_MODEL_HORIZONS = (1, 3)
GBT_MAX_DEPTH = 4
GBT_MAX_ITER = 50
GBT_STEP_SIZE = 0.05
GBT_SUBSAMPLING_RATE = 0.8
GBT_SEED = 699
GBT_TUNING_CANDIDATES = ((2, 30), (2, 50), (4, 30), (4, 50), (6, 30), (6, 50))
GBT_CV_MAX_FOLDS = 3
GBT_CV_MIN_FOLDS = 2

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
class GBTModelSelection:
    """Selected GBT parameters and the training-only temporal CV evidence."""

    horizon_years: int
    max_depth: int
    max_iter: int
    step_size: float
    subsampling_rate: float
    tuning_status: str
    cv_mae: float | None
    cv_fold_origin_years: tuple[int, ...]
    candidate_cv_mae: tuple[tuple[int, int, float], ...]


@dataclass(frozen=True)
class ForecastRun:
    """Published prediction and scorecard frames for one forecast-development run."""

    run_id: str
    built_at_utc: str
    predictions: Any
    scorecard: Any
    tree_model_selections: tuple[GBTModelSelection, ...]


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


def validate_gradient_boosted_tree_parameters(
    *,
    max_depth: int,
    max_iter: int,
    step_size: float,
    subsampling_rate: float,
) -> None:
    """Validate the fixed-parameter gradient-boosted-tree candidate configuration."""

    if max_depth <= 0:
        raise ValueError("max_depth must be positive")
    if max_iter <= 0:
        raise ValueError("max_iter must be positive")
    if not 0 < step_size <= 1:
        raise ValueError("step_size must be greater than 0 and at most 1")
    if not 0 < subsampling_rate <= 1:
        raise ValueError("subsampling_rate must be greater than 0 and at most 1")


def active_forecast_model_horizons(available_horizons: Iterable[int]) -> tuple[int, ...]:
    """Keep the one- and three-year horizons from an input panel for model scoring."""

    available = set(available_horizons)
    return tuple(horizon for horizon in FORECAST_MODEL_HORIZONS if horizon in available)


def gbt_temporal_cv_origin_years(
    training_origin_years: Iterable[int],
    *,
    horizon_years: int,
    max_folds: int = GBT_CV_MAX_FOLDS,
) -> tuple[int, ...]:
    """Choose recent training origins with at least one fully purged earlier origin."""

    if horizon_years <= 0:
        raise ValueError("horizon_years must be positive")
    if max_folds <= 0:
        raise ValueError("max_folds must be positive")
    origins = sorted(set(training_origin_years))
    if len(origins) < 2:
        return ()
    first_purge_safe_origin = origins[0] + horizon_years + 1
    eligible = [year for year in origins if year >= first_purge_safe_origin]
    return tuple(eligible[-max_folds:])


def housing_composition_band(column: Any, functions: Any) -> Any:
    """Return the shared interpretable single-family housing-share band expression."""

    return (
        functions.when(column.isNull(), functions.lit("Missing"))
        .when(column < 0.25, functions.lit("Under 25%"))
        .when(column < 0.50, functions.lit("25% to under 50%"))
        .when(column < 0.75, functions.lit("50% to under 75%"))
        .otherwise(functions.lit("75% or more"))
    )


def acs_uncertainty_band(frame: Any, functions: Any) -> Any:
    """Return a readable band for the largest available core ACS relative margin of error."""

    maximum_relative_moe = functions.greatest(
        functions.col("median_household_income_relative_moe"),
        functions.col("median_owner_occupied_value_relative_moe"),
        functions.col("median_gross_rent_relative_moe"),
    )
    return (
        functions.when(maximum_relative_moe.isNull(), functions.lit("Missing"))
        .when(maximum_relative_moe < 0.10, functions.lit("Under 10%"))
        .when(maximum_relative_moe < 0.30, functions.lit("10% to under 30%"))
        .when(maximum_relative_moe < 0.50, functions.lit("30% to under 50%"))
        .otherwise(functions.lit("50% or more"))
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


def _gradient_boosted_tree_predictions(
    frame: Any,
    *,
    seed: int = GBT_SEED,
) -> tuple[Any, tuple[GBTModelSelection, ...]]:
    """Tune on purged training-origin folds, then fit one GBT per horizon."""

    from pyspark.ml import Pipeline  # type: ignore[import-not-found]
    from pyspark.ml.evaluation import RegressionEvaluator  # type: ignore[import-not-found]
    from pyspark.ml.feature import Imputer, VectorAssembler  # type: ignore[import-not-found]
    from pyspark.ml.regression import GBTRegressor  # type: ignore[import-not-found]
    from pyspark.sql import functions  # type: ignore[import-not-found]

    validate_feature_registry(frame.columns)
    outputs = []
    selections = []
    imputed = tuple(f"{column}__tree_imputed" for column in LINEAR_FEATURE_COLUMNS)
    evaluator = RegressionEvaluator(
        labelCol="target_cumulative_log_change",
        predictionCol="prediction_cumulative_log_change",
        metricName="mae",
    )

    def fit_tree(training: Any, *, max_depth: int, max_iter: int) -> Any:
        """Fit one imputation-and-GBT pipeline with the requested tree settings."""

        validate_gradient_boosted_tree_parameters(
            max_depth=max_depth,
            max_iter=max_iter,
            step_size=GBT_STEP_SIZE,
            subsampling_rate=GBT_SUBSAMPLING_RATE,
        )
        pipeline = Pipeline(
            stages=[
                Imputer(
                    strategy="median",
                    inputCols=list(LINEAR_FEATURE_COLUMNS),
                    outputCols=list(imputed),
                ),
                VectorAssembler(
                    inputCols=list(imputed),
                    outputCol="_tree_features",
                    handleInvalid="error",
                ),
                GBTRegressor(
                    featuresCol="_tree_features",
                    labelCol="target_cumulative_log_change",
                    predictionCol="prediction_cumulative_log_change",
                    maxDepth=max_depth,
                    maxIter=max_iter,
                    stepSize=GBT_STEP_SIZE,
                    subsamplingRate=GBT_SUBSAMPLING_RATE,
                    seed=seed,
                ),
            ]
        )
        return pipeline.fit(training)

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
        if not training.limit(1).count():
            raise ValueError(f"No eligible training observations for {horizon}-year horizon")
        if not validation.limit(1).count():
            raise ValueError(f"No observed validation targets for {horizon}-year horizon")
        training_origins = [
            int(row[0])
            for row in training.select("forecast_origin_year").distinct().collect()
        ]
        candidate_fold_years = gbt_temporal_cv_origin_years(
            training_origins,
            horizon_years=int(horizon),
        )
        folds = []
        for fold_year in candidate_fold_years:
            fold_training = training.where(
                (functions.col("forecast_origin_year") < fold_year)
                & (functions.col("target_end_year") < fold_year)
            )
            fold_validation = training.where(
                functions.col("forecast_origin_year") == fold_year
            )
            if fold_training.limit(1).count() and fold_validation.limit(1).count():
                folds.append((fold_year, fold_training, fold_validation))

        selected_depth = GBT_MAX_DEPTH
        selected_iter = GBT_MAX_ITER
        selected_cv_mae = None
        tuning_status = "fixed_default_insufficient_purged_folds"
        candidate_cv_mae: tuple[tuple[int, int, float], ...] = ()
        if len(folds) >= GBT_CV_MIN_FOLDS:
            candidate_scores = []
            for max_depth, max_iter in GBT_TUNING_CANDIDATES:
                fold_maes = []
                for _, fold_training, fold_validation in folds:
                    model = fit_tree(
                        fold_training,
                        max_depth=max_depth,
                        max_iter=max_iter,
                    )
                    scored_fold = model.transform(fold_validation)
                    fold_maes.append(evaluator.evaluate(scored_fold))
                candidate_scores.append(
                    (sum(fold_maes) / len(fold_maes), max_depth, max_iter)
                )
            selected_cv_mae, selected_depth, selected_iter = min(candidate_scores)
            candidate_cv_mae = tuple(
                (depth, iteration, mae)
                for mae, depth, iteration in candidate_scores
            )
            tuning_status = "selected_by_expanding_origin_cv"

        selection = GBTModelSelection(
            horizon_years=int(horizon),
            max_depth=selected_depth,
            max_iter=selected_iter,
            step_size=GBT_STEP_SIZE,
            subsampling_rate=GBT_SUBSAMPLING_RATE,
            tuning_status=tuning_status,
            cv_mae=selected_cv_mae,
            cv_fold_origin_years=tuple(year for year, _, _ in folds),
            candidate_cv_mae=candidate_cv_mae,
        )
        selections.append(selection)
        fitted_model = fit_tree(
            training,
            max_depth=selected_depth,
            max_iter=selected_iter,
        )
        output = fitted_model.transform(validation).select(
            *frame.columns,
            "prediction_cumulative_log_change",
        )
        outputs.append(
            output.withColumn("model_name", functions.lit("gradient_boosted_trees"))
        )
    if not outputs:
        raise ValueError("No forecast horizons were available to fit")
    combined = outputs[0]
    for output in outputs[1:]:
        combined = combined.unionByName(output)
    return combined, tuple(selections)


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
            "residual_annualized_change_pct",
            functions.col("target_annualized_change_pct")
            - functions.col("prediction_annualized_change_pct"),
        )
        .withColumn(
            "absolute_error_annualized_change_pct",
            functions.abs(functions.col("residual_annualized_change_pct")),
        )
        .withColumn(
            "housing_composition_band",
            housing_composition_band(functions.col("single_family_share_estimate"), functions),
        )
        .withColumn("acs_uncertainty_band", acs_uncertainty_band(frame, functions))
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
        predictions.withColumn("slice_name", functions.lit("census_region")).withColumn(
            "slice_value", functions.col("region_name")
        ),
        predictions.withColumn("slice_name", functions.lit("forecast_origin_year")).withColumn(
            "slice_value", functions.col("forecast_origin_year").cast("string")
        ),
        predictions.withColumn("slice_name", functions.lit("acs_uncertainty_band")).withColumn(
            "slice_value", functions.col("acs_uncertainty_band")
        ),
    ]
    sliced = slices[0]
    for current in slices[1:]:
        sliced = sliced.unionByName(current)
    squared_error = functions.pow(functions.col("residual_cumulative_log_change"), 2)
    squared_annualized_error = functions.pow(
        functions.col("residual_annualized_change_pct"), 2
    )
    direction_correct = functions.when(
        functions.signum(functions.col("prediction_cumulative_log_change"))
        == functions.signum(functions.col("target_cumulative_log_change")),
        1.0,
    ).otherwise(0.0)
    target_positive = functions.when(
        functions.col("target_cumulative_log_change") > 0,
        1.0,
    ).otherwise(0.0)
    summary = (
        sliced.groupBy(*base_columns, "slice_name", "slice_value")
        .agg(
            functions.count(functions.lit(1)).alias("observation_count"),
            functions.countDistinct("geoid_2020").alias("tract_count"),
            functions.avg("absolute_error_cumulative_log_change").alias("mae_log_change"),
            functions.sqrt(functions.avg(squared_error)).alias("rmse_log_change"),
            functions.percentile_approx(
                "absolute_error_cumulative_log_change", 0.5, 10000
            ).alias("median_absolute_error_log_change"),
            functions.percentile_approx(
                "absolute_error_cumulative_log_change", 0.9, 10000
            ).alias("p90_absolute_error_log_change"),
            functions.avg("residual_cumulative_log_change").alias("mean_error_log_change"),
            functions.stddev_samp("residual_cumulative_log_change").alias(
                "error_standard_deviation_log_change"
            ),
            functions.avg(squared_error).alias("mean_squared_error_log_change"),
            functions.var_pop("target_cumulative_log_change").alias(
                "target_variance_log_change"
            ),
            functions.avg("absolute_error_annualized_change_pct").alias(
                "mae_annualized_change_pct"
            ),
            functions.sqrt(functions.avg(squared_annualized_error)).alias(
                "rmse_annualized_change_pct"
            ),
            functions.avg("residual_annualized_change_pct").alias(
                "mean_error_annualized_change_pct"
            ),
            functions.avg(direction_correct).alias("directional_accuracy"),
            functions.avg(target_positive).alias("target_positive_share"),
            functions.avg("target_annualized_change_pct").alias(
                "mean_target_annualized_change_pct"
            ),
            functions.avg("prediction_annualized_change_pct").alias(
                "mean_prediction_annualized_change_pct"
            ),
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
        "forecast_model_schema_version",
        "forecast_run_id",
        "forecast_built_at_utc",
        "slice_name",
        "slice_value",
    ]
    zero_reference = summary.where(functions.col("model_name") == "zero_change").select(
        *reference_keys,
        functions.col("mae_log_change").alias("zero_change_mae_log_change"),
        functions.col("rmse_log_change").alias("zero_change_rmse_log_change"),
    )
    return (
        summary.join(zero_reference, reference_keys, "left")
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


def build_forecast_baseline_run(
    frame: Any,
    *,
    run_id: str | None = None,
    built_at_utc: str | None = None,
    reg_param: float = 0.05,
) -> ForecastRun:
    """Build one- and three-year validation predictions without opening locked tests."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    validate_feature_registry(frame.columns)
    available_horizons = (
        int(row[0]) for row in frame.select("horizon_years").distinct().collect()
    )
    active_horizons = active_forecast_model_horizons(available_horizons)
    if not active_horizons:
        raise ValueError(
            "No modeling-panel rows are available for the active one- and three-year horizons"
        )
    frame = frame.where(functions.col("horizon_years").isin(*active_horizons))
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
    tree, tree_model_selections = _gradient_boosted_tree_predictions(frame)
    predictions = _add_prediction_fields(
        fixed.unionByName(linear, allowMissingColumns=True).unionByName(
            tree, allowMissingColumns=True
        ),
        run_id=run_id,
        built_at_utc=built_at_utc,
    )
    if predictions.where(functions.col("temporal_role") != "validation").limit(1).count():
        raise ValueError("Baseline prediction output contains a non-validation row")
    scorecard = build_forecast_scorecard(predictions)
    return ForecastRun(
        run_id,
        built_at_utc,
        predictions,
        scorecard,
        tree_model_selections,
    )

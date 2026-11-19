"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Frozen forecast selection, calibration, locked-test, and current-scoring utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from neighborhood_twin.forecasting import (
    GBT_SEED,
    GBT_STEP_SIZE,
    GBT_SUBSAMPLING_RATE,
    LINEAR_FEATURE_COLUMNS,
    acs_uncertainty_band,
    housing_composition_band,
    validate_feature_registry,
    validate_gradient_boosted_tree_parameters,
)

FORECAST_FINAL_SCHEMA_VERSION = "1.0.0"
FORECAST_SELECTION_TABLE = "forecast_model_selection"
FORECAST_CALIBRATION_PREDICTION_TABLE = "forecast_calibration_prediction"
FORECAST_INTERVAL_TABLE = "forecast_interval_calibration"
FORECAST_LOCKED_TEST_PREDICTION_TABLE = "forecast_locked_test_prediction"
FORECAST_LOCKED_TEST_SCORECARD_TABLE = "forecast_locked_test_scorecard"
FORECAST_CURRENT_PREDICTION_TABLE = "forecast_current_prediction"
SUPPORTED_CHAMPIONS = (
    "state_current_trend",
    "regularized_linear",
    "gradient_boosted_trees",
)


@dataclass(frozen=True)
class ChampionSpecification:
    """Frozen model family and parameters for one forecast horizon."""

    horizon_years: int
    model_name: str
    reg_param: float = 0.05
    gbt_max_depth: int = 4
    gbt_max_iter: int = 50

    def validate(self) -> None:
        """Reject unsupported model names and invalid estimator settings."""

        if self.horizon_years <= 0:
            raise ValueError("horizon_years must be positive")
        if self.model_name not in SUPPORTED_CHAMPIONS:
            raise ValueError(f"Unsupported champion model: {self.model_name}")
        if self.reg_param < 0:
            raise ValueError("reg_param must be nonnegative")
        validate_gradient_boosted_tree_parameters(
            max_depth=self.gbt_max_depth,
            max_iter=self.gbt_max_iter,
            step_size=GBT_STEP_SIZE,
            subsampling_rate=GBT_SUBSAMPLING_RATE,
        )


@dataclass(frozen=True)
class ForecastFinalizationRun:
    """Frames created after model choices are frozen and the locked test is opened."""

    run_id: str
    built_at_utc: str
    selection: Any
    calibration_predictions: Any
    intervals: Any
    locked_test_predictions: Any
    locked_test_scorecard: Any
    current_predictions: Any


def validate_champion_specifications(
    specifications: tuple[ChampionSpecification, ...],
) -> None:
    """Require one valid champion specification for every distinct horizon."""

    if not specifications:
        raise ValueError("At least one champion specification is required")
    for specification in specifications:
        specification.validate()
    horizons = [item.horizon_years for item in specifications]
    if len(horizons) != len(set(horizons)):
        raise ValueError("Champion specifications must not repeat a horizon")


def interval_quantile_probability(sample_count: int, coverage: float) -> float:
    """Return the finite-sample split-conformal absolute-residual quantile level."""

    if sample_count <= 0:
        raise ValueError("sample_count must be positive")
    if not 0 < coverage < 1:
        raise ValueError("coverage must be between zero and one")
    rank = min(sample_count, int((sample_count + 1) * coverage + 0.999999999))
    return rank / sample_count


def _fit_model(training: Any, specification: ChampionSpecification) -> Any:
    """Fit one frozen Spark model pipeline using training data only."""

    from pyspark.ml import Pipeline  # type: ignore[import-not-found]
    from pyspark.ml.feature import (  # type: ignore[import-not-found]
        Imputer,
        StandardScaler,
        VectorAssembler,
    )
    from pyspark.ml.regression import (  # type: ignore[import-not-found]
        GBTRegressor,
        LinearRegression,
    )

    specification.validate()
    imputed = [f"_{column}_final_imputed" for column in LINEAR_FEATURE_COLUMNS]
    stages: list[Any] = [
        Imputer(
            strategy="median",
            inputCols=list(LINEAR_FEATURE_COLUMNS),
            outputCols=imputed,
        )
    ]
    if specification.model_name == "regularized_linear":
        stages.extend(
            [
                VectorAssembler(
                    inputCols=imputed,
                    outputCol="_final_unscaled_features",
                    handleInvalid="error",
                ),
                StandardScaler(
                    inputCol="_final_unscaled_features",
                    outputCol="_final_features",
                    withMean=True,
                    withStd=True,
                ),
                LinearRegression(
                    featuresCol="_final_features",
                    labelCol="target_cumulative_log_change",
                    predictionCol="prediction_cumulative_log_change",
                    regParam=specification.reg_param,
                    elasticNetParam=0.0,
                    maxIter=100,
                    standardization=False,
                ),
            ]
        )
    else:
        stages.extend(
            [
                VectorAssembler(
                    inputCols=imputed,
                    outputCol="_final_features",
                    handleInvalid="error",
                ),
                GBTRegressor(
                    featuresCol="_final_features",
                    labelCol="target_cumulative_log_change",
                    predictionCol="prediction_cumulative_log_change",
                    maxDepth=specification.gbt_max_depth,
                    maxIter=specification.gbt_max_iter,
                    stepSize=GBT_STEP_SIZE,
                    subsamplingRate=GBT_SUBSAMPLING_RATE,
                    seed=GBT_SEED,
                ),
            ]
        )
    return Pipeline(stages=stages).fit(training)


def _score_role(
    panel: Any,
    specifications: tuple[ChampionSpecification, ...],
    *,
    temporal_role: str,
    require_observed_target: bool,
) -> Any:
    """Fit from labels known before each role origin and score one origin per horizon."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    outputs = []
    for specification in specifications:
        horizon_frame = panel.where(
            functions.col("horizon_years") == specification.horizon_years
        )
        scoring = horizon_frame.where(functions.col("temporal_role") == temporal_role)
        if require_observed_target:
            scoring = scoring.where(functions.col("target_is_observed"))
        origins = [
            int(row[0])
            for row in scoring.select("forecast_origin_year").distinct().collect()
        ]
        if len(origins) != 1:
            raise ValueError(
                f"Expected one {temporal_role} origin for horizon "
                f"{specification.horizon_years}; found {sorted(origins)}"
            )
        prediction_origin = origins[0]
        if not scoring.limit(1).count():
            raise ValueError(
                f"Empty scoring frame for horizon {specification.horizon_years}"
            )
        if specification.model_name == "state_current_trend":
            output = scoring.withColumn(
                "prediction_cumulative_log_change",
                functions.log1p(
                    functions.col("state_origin_mean_annual_change_pct") / 100.0
                )
                * functions.col("horizon_years"),
            ).withColumn("model_training_cutoff_year", functions.lit(None).cast("int"))
        else:
            training = horizon_frame.where(
                functions.col("target_is_observed")
                & (functions.col("geographic_role") == "geographic_development")
                & (functions.col("target_end_year") < prediction_origin)
            )
            if not training.limit(1).count():
                raise ValueError(
                    f"Empty training frame for horizon {specification.horizon_years}"
                )
            output = (
                _fit_model(training, specification)
                .transform(scoring)
                .select(*panel.columns, "prediction_cumulative_log_change")
                .withColumn("model_training_cutoff_year", functions.lit(prediction_origin - 1))
            )
        output = output.withColumn("model_name", functions.lit(specification.model_name))
        outputs.append(output)
    combined = outputs[0]
    for output in outputs[1:]:
        combined = combined.unionByName(output)
    return combined


def _score_current(
    panel: Any,
    specifications: tuple[ChampionSpecification, ...],
) -> Any:
    """Refit frozen models on all prior known labels and score the latest origin."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    outputs = []
    for specification in specifications:
        horizon_frame = panel.where(
            functions.col("horizon_years") == specification.horizon_years
        )
        current_origin = horizon_frame.agg(functions.max("forecast_origin_year")).first()[0]
        if current_origin is None:
            raise ValueError(f"No current origin for horizon {specification.horizon_years}")
        current_origin = int(current_origin)
        scoring = horizon_frame.where(
            (functions.col("forecast_origin_year") == current_origin)
            & (functions.col("temporal_role") == "future_scoring")
        )
        if not scoring.limit(1).count():
            raise ValueError(
                f"Empty production scoring frame for horizon {specification.horizon_years}"
            )
        if specification.model_name == "state_current_trend":
            output = scoring.withColumn(
                "prediction_cumulative_log_change",
                functions.log1p(
                    functions.col("state_origin_mean_annual_change_pct") / 100.0
                )
                * functions.col("horizon_years"),
            ).withColumn("model_training_cutoff_year", functions.lit(None).cast("int"))
        else:
            training = horizon_frame.where(
                functions.col("target_is_observed")
                & (functions.col("geographic_role") == "geographic_development")
                & (functions.col("target_end_year") < current_origin)
            )
            if not training.limit(1).count():
                raise ValueError(
                    f"Empty production training frame for horizon "
                    f"{specification.horizon_years}"
                )
            output = (
                _fit_model(training, specification)
                .transform(scoring)
                .select(*panel.columns, "prediction_cumulative_log_change")
                .withColumn("model_training_cutoff_year", functions.lit(current_origin - 1))
            )
        output = output.withColumn("model_name", functions.lit(specification.model_name))
        outputs.append(output)
    combined = outputs[0]
    for output in outputs[1:]:
        combined = combined.unionByName(output)
    return combined


def _add_prediction_context(frame: Any, *, run_id: str, built_at_utc: str) -> Any:
    """Attach residuals, readable rates, baseline context, slices, and lineage."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    target_present = functions.col("target_is_observed") & functions.col(
        "target_cumulative_log_change"
    ).isNotNull()
    baseline_log = (
        functions.log1p(functions.col("state_origin_mean_annual_change_pct") / 100.0)
        * functions.col("horizon_years")
    )
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
        .withColumn("baseline_model_name", functions.lit("state_current_trend"))
        .withColumn("baseline_prediction_cumulative_log_change", baseline_log)
        .withColumn(
            "baseline_prediction_annualized_change_pct",
            functions.col("state_origin_mean_annual_change_pct"),
        )
        .withColumn(
            "residual_cumulative_log_change",
            functions.when(
                target_present,
                functions.col("target_cumulative_log_change")
                - functions.col("prediction_cumulative_log_change"),
            ),
        )
        .withColumn(
            "absolute_error_cumulative_log_change",
            functions.abs(functions.col("residual_cumulative_log_change")),
        )
        .withColumn(
            "evaluation_geography",
            functions.when(
                functions.col("geographic_role") == "geographic_holdout",
                functions.lit("held_out_state"),
            ).otherwise(functions.lit("development_states")),
        )
        .withColumn(
            "housing_composition_band",
            housing_composition_band(functions.col("single_family_share_estimate"), functions),
        )
        .withColumn("acs_uncertainty_band", acs_uncertainty_band(frame, functions))
        .withColumn("forecast_final_schema_version", functions.lit(FORECAST_FINAL_SCHEMA_VERSION))
        .withColumn("forecast_final_run_id", functions.lit(run_id))
        .withColumn(
            "forecast_final_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
    )


def build_interval_calibration(
    calibration_predictions: Any,
    *,
    coverage: float,
) -> Any:
    """Estimate one finite-sample absolute-residual interval radius per horizon."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    development = calibration_predictions.where(
        functions.col("geographic_role") == "geographic_development"
    )
    counts = {
        int(row["horizon_years"]): int(row["sample_count"])
        for row in development.groupBy("horizon_years")
        .agg(functions.count("*").alias("sample_count"))
        .collect()
    }
    if not counts:
        raise ValueError("No development-state calibration residuals are available")
    spark = calibration_predictions.sparkSession
    probability_rows = [
        (
            horizon,
            sample_count,
            float(coverage),
            interval_quantile_probability(sample_count, coverage),
        )
        for horizon, sample_count in sorted(counts.items())
    ]
    probabilities = spark.createDataFrame(
        probability_rows,
        "horizon_years int, calibration_observation_count long, "
        "nominal_coverage double, quantile_probability double",
    )
    summaries = []
    for row in probability_rows:
        horizon, _, _, probability = row
        summary = (
            development.where(functions.col("horizon_years") == horizon)
            .agg(
                functions.percentile_approx(
                    "absolute_error_cumulative_log_change",
                    probability,
                    10000,
                ).alias("interval_radius_cumulative_log_change"),
                functions.avg("residual_cumulative_log_change").alias(
                    "calibration_mean_error_cumulative_log_change"
                ),
            )
            .withColumn("horizon_years", functions.lit(horizon))
        )
        summaries.append(summary)
    combined = summaries[0]
    for summary in summaries[1:]:
        combined = combined.unionByName(summary)
    lineage = calibration_predictions.select(
        "forecast_final_schema_version",
        "forecast_final_run_id",
        "forecast_final_built_at_utc",
    ).distinct()
    return probabilities.join(combined, "horizon_years", "inner").crossJoin(lineage)


def apply_prediction_intervals(predictions: Any, intervals: Any) -> Any:
    """Attach cumulative-log and annualized lower and upper bounds."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    joined = predictions.join(
        intervals.select(
            "horizon_years",
            "nominal_coverage",
            "calibration_observation_count",
            "interval_radius_cumulative_log_change",
        ),
        "horizon_years",
        "inner",
    )
    lower = (
        functions.col("prediction_cumulative_log_change")
        - functions.col("interval_radius_cumulative_log_change")
    )
    upper = (
        functions.col("prediction_cumulative_log_change")
        + functions.col("interval_radius_cumulative_log_change")
    )
    return (
        joined.withColumn("prediction_lower_cumulative_log_change", lower)
        .withColumn("prediction_upper_cumulative_log_change", upper)
        .withColumn(
            "prediction_lower_annualized_change_pct",
            (functions.exp(lower / functions.col("horizon_years")) - 1) * 100,
        )
        .withColumn(
            "prediction_upper_annualized_change_pct",
            (functions.exp(upper / functions.col("horizon_years")) - 1) * 100,
        )
        .withColumn(
            "interval_contains_target",
            functions.when(
                functions.col("target_is_observed"),
                functions.col("target_cumulative_log_change").between(lower, upper),
            ),
        )
    )


def build_locked_test_scorecard(predictions: Any) -> Any:
    """Summarize final point and interval performance without model reselection."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    slices = [
        predictions.withColumn("slice_name", functions.lit("overall")).withColumn(
            "slice_value", functions.lit("all")
        ),
        predictions.withColumn("slice_name", functions.lit("evaluation_geography")).withColumn(
            "slice_value", functions.col("evaluation_geography")
        ),
        predictions.withColumn("slice_name", functions.lit("modeling_cohort")).withColumn(
            "slice_value", functions.col("modeling_cohort")
        ),
        predictions.withColumn("slice_name", functions.lit("housing_composition_band")).withColumn(
            "slice_value", functions.col("housing_composition_band")
        ),
        predictions.withColumn("slice_name", functions.lit("acs_uncertainty_band")).withColumn(
            "slice_value", functions.col("acs_uncertainty_band")
        ),
        predictions.withColumn("slice_name", functions.lit("census_region")).withColumn(
            "slice_value", functions.col("region_name")
        ),
    ]
    combined = slices[0]
    for item in slices[1:]:
        combined = combined.unionByName(item)
    squared_error = functions.pow(functions.col("residual_cumulative_log_change"), 2)
    return combined.groupBy(
        "model_name",
        "horizon_years",
        "nominal_coverage",
        "forecast_final_schema_version",
        "forecast_final_run_id",
        "forecast_final_built_at_utc",
        "slice_name",
        "slice_value",
    ).agg(
        functions.count("*").alias("observation_count"),
        functions.countDistinct("geoid_2020").alias("tract_count"),
        functions.avg("absolute_error_cumulative_log_change").alias("mae_log_change"),
        functions.sqrt(functions.avg(squared_error)).alias("rmse_log_change"),
        functions.avg("residual_cumulative_log_change").alias("mean_error_log_change"),
        functions.percentile_approx(
            "absolute_error_cumulative_log_change", 0.9, 10000
        ).alias("p90_absolute_error_log_change"),
        functions.avg(functions.col("interval_contains_target").cast("double")).alias(
            "empirical_interval_coverage"
        ),
        functions.avg(
            functions.col("prediction_upper_annualized_change_pct")
            - functions.col("prediction_lower_annualized_change_pct")
        ).alias("mean_interval_width_annualized_pct_points"),
    )


def build_selection_frame(
    spark: Any,
    specifications: tuple[ChampionSpecification, ...],
    validation_scorecard: Any,
    *,
    run_id: str,
    built_at_utc: str,
) -> Any:
    """Record frozen choices with their published overall validation evidence."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    rows = [
        (
            item.horizon_years,
            item.model_name,
            item.reg_param,
            item.gbt_max_depth,
            item.gbt_max_iter,
        )
        for item in specifications
    ]
    configured = spark.createDataFrame(
        rows,
        "horizon_years int, selected_model_name string, reg_param double, "
        "gbt_max_depth int, gbt_max_iter int",
    )
    evidence = validation_scorecard.where(functions.col("slice_name") == "overall").select(
        "horizon_years",
        functions.col("model_name").alias("selected_model_name"),
        functions.col("forecast_run_id").alias("source_validation_run_id"),
        functions.col("mae_log_change").alias("validation_mae_log_change"),
        functions.col("rmse_log_change").alias("validation_rmse_log_change"),
        functions.col("mean_error_log_change").alias("validation_mean_error_log_change"),
        functions.col("p90_absolute_error_log_change").alias(
            "validation_p90_absolute_error_log_change"
        ),
        functions.col("r_squared").alias("validation_r_squared"),
    )
    selection = configured.join(
        evidence,
        ["horizon_years", "selected_model_name"],
        "inner",
    )
    if selection.count() != len(specifications):
        raise ValueError("A configured champion is missing published validation evidence")
    return (
        selection.withColumn(
            "selection_rule",
            functions.lit(
                "prefer_simpler_if_within_one_percent_mae_and_no_material_rmse_bias_or_tail_loss"
            ),
        )
        .withColumn("forecast_final_schema_version", functions.lit(FORECAST_FINAL_SCHEMA_VERSION))
        .withColumn("forecast_final_run_id", functions.lit(run_id))
        .withColumn(
            "forecast_final_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
    )


def validate_finalization_outputs(run: ForecastFinalizationRun) -> None:
    """Fail publication when roles, intervals, keys, or leakage boundaries are invalid."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    expected_roles = (
        (run.calibration_predictions, "calibration", True),
        (run.locked_test_predictions, "locked_temporal_test", True),
        (run.current_predictions, "future_scoring", False),
    )
    for frame, role, target_required in expected_roles:
        if frame.where(functions.col("temporal_role") != role).limit(1).count():
            raise RuntimeError(f"{role} output contains another temporal role")
        if target_required and frame.where(~functions.col("target_is_observed")).limit(1).count():
            raise RuntimeError(f"{role} output contains an unobserved target")
        if frame.where(
            functions.col("model_training_cutoff_year").isNotNull()
            &
            functions.col("model_training_cutoff_year")
            >= functions.col("forecast_origin_year")
        ).limit(1).count():
            raise RuntimeError(f"{role} output violates the training cutoff")
        if frame.groupBy("geoid_2020", "horizon_years").count().where(
            functions.col("count") != 1
        ).limit(1).count():
            raise RuntimeError(f"{role} output is not unique by tract and horizon")
    for frame in (run.locked_test_predictions, run.current_predictions):
        if frame.where(
            (functions.col("prediction_lower_cumulative_log_change")
             > functions.col("prediction_cumulative_log_change"))
            | (functions.col("prediction_upper_cumulative_log_change")
               < functions.col("prediction_cumulative_log_change"))
        ).limit(1).count():
            raise RuntimeError("A prediction interval does not contain its point estimate")


def build_forecast_finalization_run(
    panel: Any,
    validation_scorecard: Any,
    specifications: tuple[ChampionSpecification, ...],
    *,
    coverage: float = 0.90,
    run_id: str | None = None,
    built_at_utc: str | None = None,
) -> ForecastFinalizationRun:
    """Calibrate frozen models, evaluate locked tests once, and score current tracts."""

    validate_feature_registry(panel.columns)
    validate_champion_specifications(specifications)
    run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    built_at_utc = built_at_utc or datetime.now(UTC).isoformat()
    selection = build_selection_frame(
        panel.sparkSession,
        specifications,
        validation_scorecard,
        run_id=run_id,
        built_at_utc=built_at_utc,
    )
    calibration = _add_prediction_context(
        _score_role(
            panel,
            specifications,
            temporal_role="calibration",
            require_observed_target=True,
        ),
        run_id=run_id,
        built_at_utc=built_at_utc,
    )
    intervals = build_interval_calibration(calibration, coverage=coverage)
    locked = apply_prediction_intervals(
        _add_prediction_context(
            _score_role(
                panel,
                specifications,
                temporal_role="locked_temporal_test",
                require_observed_target=True,
            ),
            run_id=run_id,
            built_at_utc=built_at_utc,
        ),
        intervals,
    )
    current = apply_prediction_intervals(
        _add_prediction_context(
            _score_current(panel, specifications),
            run_id=run_id,
            built_at_utc=built_at_utc,
        ),
        intervals,
    )
    result = ForecastFinalizationRun(
        run_id=run_id,
        built_at_utc=built_at_utc,
        selection=selection,
        calibration_predictions=calibration,
        intervals=intervals,
        locked_test_predictions=locked,
        locked_test_scorecard=build_locked_test_scorecard(locked),
        current_predictions=current,
    )
    validate_finalization_outputs(result)
    return result

"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Evaluation thresholds for finalized neighborhood forecast models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

FORECAST_EVALUATION_THRESHOLD_TABLE = "forecast_evaluation_threshold"
FORECAST_EVALUATION_THRESHOLD_SCHEMA_VERSION = "2.0.0"


@dataclass(frozen=True)
class ForecastEvaluationPolicy:
    """Fixed thresholds used to flag weak model-horizon evaluation evidence."""

    minimum_observation_count: int = 1_000
    interval_coverage_tolerance: float = 0.10


def validate_evaluation_policy(policy: ForecastEvaluationPolicy) -> None:
    """Reject evaluation policies with implausible sample or coverage requirements."""

    if policy.minimum_observation_count <= 0:
        raise ValueError("minimum_observation_count must be positive")
    if not 0 <= policy.interval_coverage_tolerance < 1:
        raise ValueError("interval_coverage_tolerance must be in [0, 1)")


def evaluate_threshold_values(
    *,
    observation_count: int,
    model_mae: float,
    zero_change_mae: float,
    empirical_interval_coverage: float,
    nominal_coverage: float,
    policy: ForecastEvaluationPolicy,
) -> tuple[bool, tuple[str, ...]]:
    """Evaluate one model and horizon without replacing it with a baseline."""

    validate_evaluation_policy(policy)
    reasons = []
    if observation_count < policy.minimum_observation_count:
        reasons.append("insufficient_later_period_observations")
    if model_mae > zero_change_mae:
        reasons.append("worse_than_zero_change_mae")
    if empirical_interval_coverage < (nominal_coverage - policy.interval_coverage_tolerance):
        reasons.append("interval_coverage_below_threshold")
    return not reasons, tuple(reasons)


def build_forecast_evaluation_thresholds(
    locked_predictions: Any,
    locked_scorecard: Any,
    *,
    policy: ForecastEvaluationPolicy | None = None,
) -> Any:
    """Build auditable evaluation status for each supervised model and horizon."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    policy = policy or ForecastEvaluationPolicy()
    validate_evaluation_policy(policy)
    benchmark_inputs = locked_predictions.select(
        "geoid_2020",
        "horizon_years",
        "target_cumulative_log_change",
        "baseline_prediction_cumulative_log_change",
    ).dropDuplicates(["geoid_2020", "horizon_years"])
    benchmarks = benchmark_inputs.groupBy("horizon_years").agg(
        functions.count("*").alias("locked_observation_count"),
        functions.avg(functions.abs(functions.col("target_cumulative_log_change"))).alias(
            "zero_change_mae_log_change"
        ),
        functions.avg(
            functions.abs(
                functions.col("target_cumulative_log_change")
                - functions.col("baseline_prediction_cumulative_log_change")
            )
        ).alias("state_trend_mae_log_change"),
        functions.sqrt(
            functions.avg(functions.pow(functions.col("target_cumulative_log_change"), 2))
        ).alias("zero_change_rmse_log_change"),
        functions.sqrt(
            functions.avg(
                functions.pow(
                    functions.col("target_cumulative_log_change")
                    - functions.col("baseline_prediction_cumulative_log_change"),
                    2,
                )
            )
        ).alias("state_trend_rmse_log_change"),
    )
    overall = locked_scorecard.where(functions.col("slice_name") == "overall").select(
        "horizon_years",
        "model_name",
        functions.col("observation_count").alias("scorecard_observation_count"),
        functions.col("mae_log_change").alias("model_mae_log_change"),
        functions.col("rmse_log_change").alias("model_rmse_log_change"),
        functions.col("mean_error_log_change").alias("model_mean_error_log_change"),
        "empirical_interval_coverage",
        "nominal_coverage",
        "forecast_final_run_id",
        "forecast_final_built_at_utc",
    )
    minimum_coverage = functions.greatest(
        functions.lit(0.0),
        functions.col("nominal_coverage") - functions.lit(policy.interval_coverage_tolerance),
    )
    result = (
        overall.join(benchmarks, "horizon_years", "inner")
        .withColumn(
            "minimum_required_interval_coverage",
            minimum_coverage,
        )
        .withColumn(
            "meets_minimum_observation_count",
            functions.col("locked_observation_count")
            >= functions.lit(policy.minimum_observation_count),
        )
        .withColumn(
            "beats_zero_change_mae",
            functions.col("model_mae_log_change") <= functions.col("zero_change_mae_log_change"),
        )
        .withColumn(
            "meets_interval_coverage",
            functions.col("empirical_interval_coverage")
            >= functions.col("minimum_required_interval_coverage"),
        )
        .withColumn(
            "meets_evaluation_thresholds",
            functions.col("meets_minimum_observation_count")
            & functions.col("beats_zero_change_mae")
            & functions.col("meets_interval_coverage"),
        )
        .withColumn(
            "evaluation_warning_reason",
            functions.when(
                functions.col("meets_evaluation_thresholds"), functions.lit("meets_thresholds")
            ).otherwise(
                functions.concat_ws(
                    ";",
                    functions.when(
                        ~functions.col("meets_minimum_observation_count"),
                        functions.lit("insufficient_later_period_observations"),
                    ),
                    functions.when(
                        ~functions.col("beats_zero_change_mae"),
                        functions.lit("worse_than_zero_change_mae"),
                    ),
                    functions.when(
                        ~functions.col("meets_interval_coverage"),
                        functions.lit("interval_coverage_below_threshold"),
                    ),
                )
            ),
        )
        .withColumn(
            "minimum_observation_count",
            functions.lit(policy.minimum_observation_count),
        )
        .withColumn(
            "interval_coverage_tolerance",
            functions.lit(policy.interval_coverage_tolerance),
        )
        .withColumn(
            "forecast_evaluation_threshold_schema_version",
            functions.lit(FORECAST_EVALUATION_THRESHOLD_SCHEMA_VERSION),
        )
    )
    return result


def validate_forecast_evaluation_thresholds(
    thresholds: Any, expected_horizons: tuple[int, ...]
) -> None:
    """Reject incomplete or inconsistent two-model evaluation thresholds."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    rows = thresholds.select(
        "model_name",
        "horizon_years",
        "locked_observation_count",
        "scorecard_observation_count",
        "meets_evaluation_thresholds",
        "evaluation_warning_reason",
    ).collect()
    actual_horizons = tuple(sorted({int(row["horizon_years"]) for row in rows}))
    if actual_horizons != tuple(sorted(expected_horizons)):
        raise RuntimeError("Evaluation status does not contain exactly the expected horizons")
    expected_models = {"regularized_linear", "gradient_boosted_trees"}
    expected_keys = {
        (model_name, horizon)
        for model_name in expected_models
        for horizon in expected_horizons
    }
    actual_keys = {(str(row["model_name"]), int(row["horizon_years"])) for row in rows}
    if actual_keys != expected_keys:
        raise RuntimeError("Evaluation status does not cover both models at every horizon")
    if any(row["locked_observation_count"] != row["scorecard_observation_count"] for row in rows):
        raise RuntimeError("Locked prediction and scorecard counts do not reconcile")
    if thresholds.groupBy("model_name", "horizon_years").count().where(
        functions.col("count") != 1
    ).limit(1).count():
        raise RuntimeError("Evaluation status is not unique by model and horizon")
    if any(not str(row["evaluation_warning_reason"]).strip() for row in rows):
        raise RuntimeError("Evaluation threshold contains an empty warning reason")

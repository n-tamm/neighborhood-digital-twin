"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Locked-test release gates for finalized neighborhood forecasts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

FORECAST_RELEASE_GATE_TABLE = "forecast_release_gate"
FORECAST_RELEASE_GATE_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class ForecastReleaseGatePolicy:
    """Fixed minimum evidence required before a horizon can reach the application."""

    minimum_observation_count: int = 1_000
    interval_coverage_tolerance: float = 0.10


def validate_release_gate_policy(policy: ForecastReleaseGatePolicy) -> None:
    """Reject release policies with implausible sample or coverage requirements."""

    if policy.minimum_observation_count <= 0:
        raise ValueError("minimum_observation_count must be positive")
    if not 0 <= policy.interval_coverage_tolerance < 1:
        raise ValueError("interval_coverage_tolerance must be in [0, 1)")


def evaluate_release_gate_values(
    *,
    observation_count: int,
    champion_mae: float,
    zero_change_mae: float,
    empirical_interval_coverage: float,
    nominal_coverage: float,
    policy: ForecastReleaseGatePolicy,
) -> tuple[bool, tuple[str, ...]]:
    """Evaluate one horizon using locked evidence without selecting another model."""

    validate_release_gate_policy(policy)
    reasons = []
    if observation_count < policy.minimum_observation_count:
        reasons.append("insufficient_locked_observations")
    if champion_mae > zero_change_mae:
        reasons.append("worse_than_zero_change_mae")
    if empirical_interval_coverage < (nominal_coverage - policy.interval_coverage_tolerance):
        reasons.append("interval_coverage_below_threshold")
    return not reasons, tuple(reasons)


def build_forecast_release_gate(
    locked_predictions: Any,
    locked_scorecard: Any,
    *,
    policy: ForecastReleaseGatePolicy | None = None,
) -> Any:
    """Build one auditable locked-test release decision per forecast horizon."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    policy = policy or ForecastReleaseGatePolicy()
    validate_release_gate_policy(policy)
    benchmarks = locked_predictions.groupBy("horizon_years").agg(
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
        functions.col("mae_log_change").alias("champion_mae_log_change"),
        functions.col("rmse_log_change").alias("champion_rmse_log_change"),
        functions.col("mean_error_log_change").alias("champion_mean_error_log_change"),
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
            functions.col("champion_mae_log_change") <= functions.col("zero_change_mae_log_change"),
        )
        .withColumn(
            "meets_interval_coverage",
            functions.col("empirical_interval_coverage")
            >= functions.col("minimum_required_interval_coverage"),
        )
        .withColumn(
            "release_eligible",
            functions.col("meets_minimum_observation_count")
            & functions.col("beats_zero_change_mae")
            & functions.col("meets_interval_coverage"),
        )
        .withColumn(
            "release_gate_reason",
            functions.when(functions.col("release_eligible"), functions.lit("eligible")).otherwise(
                functions.concat_ws(
                    ";",
                    functions.when(
                        ~functions.col("meets_minimum_observation_count"),
                        functions.lit("insufficient_locked_observations"),
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
            "forecast_release_gate_schema_version",
            functions.lit(FORECAST_RELEASE_GATE_SCHEMA_VERSION),
        )
    )
    return result


def validate_forecast_release_gate(gate: Any, expected_horizons: tuple[int, ...]) -> None:
    """Reject incomplete, inconsistent, or wholly unavailable release decisions."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    rows = gate.select(
        "horizon_years",
        "locked_observation_count",
        "scorecard_observation_count",
        "release_eligible",
        "release_gate_reason",
    ).collect()
    actual_horizons = tuple(sorted(int(row["horizon_years"]) for row in rows))
    if actual_horizons != tuple(sorted(expected_horizons)):
        raise RuntimeError("Release gate does not contain exactly the expected horizons")
    if any(row["locked_observation_count"] != row["scorecard_observation_count"] for row in rows):
        raise RuntimeError("Locked prediction and scorecard counts do not reconcile")
    if gate.groupBy("horizon_years").count().where(functions.col("count") != 1).limit(1).count():
        raise RuntimeError("Release gate is not unique by horizon")
    if any(not str(row["release_gate_reason"]).strip() for row in rows):
        raise RuntimeError("Release gate contains an empty decision reason")
    if not any(bool(row["release_eligible"]) for row in rows):
        raise RuntimeError("No forecast horizon passed the locked release gate")

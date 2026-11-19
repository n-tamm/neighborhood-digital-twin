"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Versioned application-serving products for current tract forecasts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

FORECAST_SERVING_SCHEMA_VERSION = "1.0.0"
FORECAST_SERVING_CURRENT_TABLE = "serving_forecast_current"
FORECAST_SERVING_AVAILABILITY_TABLE = "serving_forecast_availability_current"
SERVING_RELEASE_MANIFEST_TABLE = "serving_release_manifest"
FORECAST_SERVING_COMPONENT = "forecasts"
FORECAST_SERVING_METHOD = "frozen_supervised_model_with_split_conformal_interval"


@dataclass(frozen=True)
class ForecastServingRelease:
    """Immutable lineage shared by one current-forecast serving release."""

    release_id: str
    built_at_utc: str
    as_of_year: int
    horizons: tuple[int, ...]
    model_readiness_build_id: str
    forecast_final_run_id: str


def new_forecast_serving_release(
    *,
    as_of_year: int,
    horizons: tuple[int, ...],
    model_readiness_build_id: str,
    forecast_final_run_id: str,
    release_id: str | None = None,
    built_at_utc: str | None = None,
) -> ForecastServingRelease:
    """Create and validate one immutable forecast release."""

    timestamp = datetime.now(UTC)
    release = ForecastServingRelease(
        release_id=release_id or timestamp.strftime("forecast-%Y%m%dT%H%M%S%fZ"),
        built_at_utc=built_at_utc or timestamp.isoformat(),
        as_of_year=as_of_year,
        horizons=tuple(sorted(horizons)),
        model_readiness_build_id=model_readiness_build_id,
        forecast_final_run_id=forecast_final_run_id,
    )
    validate_forecast_serving_release(release)
    return release


def validate_forecast_serving_release(release: ForecastServingRelease) -> None:
    """Reject blank, duplicate, or implausible release settings."""

    if not release.release_id.strip() or not release.built_at_utc.strip():
        raise ValueError("release_id and built_at_utc must not be blank")
    if release.as_of_year < 1900:
        raise ValueError("as_of_year must be a four-digit year")
    if not release.horizons or any(value <= 0 for value in release.horizons):
        raise ValueError("horizons must contain positive integers")
    if len(release.horizons) != len(set(release.horizons)):
        raise ValueError("horizons must not contain duplicates")
    if not release.model_readiness_build_id.strip():
        raise ValueError("model_readiness_build_id must not be blank")
    if not release.forecast_final_run_id.strip():
        raise ValueError("forecast_final_run_id must not be blank")


def _add_lineage(frame: Any, release: ForecastServingRelease) -> Any:
    """Attach release identity and source lineage."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        frame.withColumn("serving_release_id", functions.lit(release.release_id))
        .withColumn("serving_schema_version", functions.lit(FORECAST_SERVING_SCHEMA_VERSION))
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
            "source_forecast_final_run_id",
            functions.lit(release.forecast_final_run_id),
        )
    )


def build_serving_forecasts(
    current_predictions: Any,
    current_profile: Any,
    release_gate: Any,
    release: ForecastServingRelease,
) -> Any:
    """Publish compact forecasts only for horizons that passed the locked release gate."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    labels = current_profile.select(
        "geoid_2020",
        "state_fips",
        "state_abbreviation",
        "state_name",
        "county_geoid",
        "county_name",
        "tract_name",
    )
    approved_gate = release_gate.where(functions.col("release_eligible")).select(
        "horizon_years",
        "release_eligible",
        "release_gate_reason",
        "locked_observation_count",
        "champion_mae_log_change",
        "zero_change_mae_log_change",
        "state_trend_mae_log_change",
        "empirical_interval_coverage",
        "minimum_required_interval_coverage",
        "forecast_release_gate_schema_version",
    )
    compact = (
        current_predictions.join(approved_gate, "horizon_years", "inner")
        .join(labels, "geoid_2020", "left")
        .select(
            "geoid_2020",
            "state_fips",
            "state_abbreviation",
            "state_name",
            "county_geoid",
            "county_name",
            "tract_name",
            "forecast_origin_year",
            "horizon_years",
            "target_end_year",
            "model_name",
            "prediction_cumulative_log_change",
            "prediction_annualized_change_pct",
            "prediction_lower_cumulative_log_change",
            "prediction_upper_cumulative_log_change",
            "prediction_lower_annualized_change_pct",
            "prediction_upper_annualized_change_pct",
            "nominal_coverage",
            "calibration_observation_count",
            "interval_radius_cumulative_log_change",
            "baseline_model_name",
            "baseline_prediction_cumulative_log_change",
            "baseline_prediction_annualized_change_pct",
            "modeling_cohort",
            "housing_composition_band",
            "acs_uncertainty_band",
            "model_training_cutoff_year",
            "forecast_final_schema_version",
            "release_eligible",
            "release_gate_reason",
            "locked_observation_count",
            "champion_mae_log_change",
            "zero_change_mae_log_change",
            "state_trend_mae_log_change",
            "empirical_interval_coverage",
            "minimum_required_interval_coverage",
            "forecast_release_gate_schema_version",
        )
        .withColumn(
            "forecast_difference_from_baseline_annualized_pct_points",
            functions.col("prediction_annualized_change_pct")
            - functions.col("baseline_prediction_annualized_change_pct"),
        )
        .withColumn(
            "driver_explanation_method",
            functions.lit("global_feature_family_ablation_and_registered_inputs"),
        )
        .withColumn(
            "driver_summary",
            functions.lit(
                "Historical HPI movement and regional market context were the clearest "
                "predictive feature families in training-fold ablation. This is a global "
                "finding, not a tract-level causal explanation."
            ),
        )
        .withColumn(
            "target_scope_note",
            functions.lit(
                "Forecasts cumulative change in FHFA single-family tract HPI, not an "
                "individual home price or the value of all housing."
            ),
        )
        .withColumn(
            "uncertainty_scope_note",
            functions.lit(
                "The interval is calibrated from one reserved historical origin per horizon. "
                "It reflects model error under that period and may not capture every future shock."
            ),
        )
    )
    return _add_lineage(compact, release)


def build_forecast_availability(
    current_profile: Any,
    forecasts: Any,
    release_gate: Any,
    release: ForecastServingRelease,
) -> Any:
    """Create one explicit availability row for every current tract and horizon."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    spark = current_profile.sparkSession
    horizons = spark.createDataFrame([(value,) for value in release.horizons], "horizon_years int")
    gate = release_gate.select(
        "horizon_years",
        "release_eligible",
        "release_gate_reason",
        "champion_mae_log_change",
        "zero_change_mae_log_change",
        "empirical_interval_coverage",
        "minimum_required_interval_coverage",
    )
    universe = (
        current_profile.select(
            "geoid_2020",
            "state_fips",
            "state_abbreviation",
            "state_name",
            "county_geoid",
            "county_name",
            "tract_name",
            "forecast_candidate",
        )
        .crossJoin(horizons)
        .join(gate, "horizon_years", "left")
    )
    available = forecasts.select(
        "geoid_2020",
        "horizon_years",
        "forecast_origin_year",
        "target_end_year",
        "model_name",
    ).withColumn("_forecast_available", functions.lit(True))
    result = (
        universe.join(available, ["geoid_2020", "horizon_years"], "left")
        .withColumn(
            "forecast_available",
            functions.coalesce(functions.col("_forecast_available"), functions.lit(False)),
        )
        .withColumn(
            "availability_reason",
            functions.when(functions.col("_forecast_available"), functions.lit("available"))
            .when(
                ~functions.coalesce(functions.col("release_eligible"), functions.lit(False)),
                functions.lit("horizon_failed_locked_release_gate"),
            )
            .when(
                ~functions.coalesce(functions.col("forecast_candidate"), functions.lit(False)),
                functions.lit("not_in_model_ready_cohort"),
            )
            .otherwise(functions.lit("current_prediction_not_published")),
        )
        .drop("_forecast_available")
    )
    return _add_lineage(result, release)


def validate_forecast_serving_outputs(
    forecasts: Any,
    availability: Any,
    release_gate: Any,
    release: ForecastServingRelease,
) -> dict[str, int]:
    """Validate lineage, key uniqueness, interval ordering, and coverage reconciliation."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    validate_forecast_serving_release(release)
    gate_rows = release_gate.select("horizon_years", "release_eligible").collect()
    gate_horizons = tuple(sorted(int(row["horizon_years"]) for row in gate_rows))
    if gate_horizons != release.horizons:
        raise RuntimeError("Forecast release gate does not cover every configured horizon")
    eligible_horizons = {
        int(row["horizon_years"]) for row in gate_rows if bool(row["release_eligible"])
    }
    published_horizons = {
        int(row[0]) for row in forecasts.select("horizon_years").distinct().collect()
    }
    if published_horizons != eligible_horizons:
        raise RuntimeError("Published forecast horizons do not match the release gate")
    for name, frame in (
        (FORECAST_SERVING_CURRENT_TABLE, forecasts),
        (FORECAST_SERVING_AVAILABILITY_TABLE, availability),
    ):
        release_ids = {row[0] for row in frame.select("serving_release_id").distinct().collect()}
        if release_ids != {release.release_id}:
            raise RuntimeError(f"{name} does not contain exactly the requested release")
        if (
            frame.groupBy("geoid_2020", "horizon_years")
            .count()
            .where(functions.col("count") != 1)
            .limit(1)
            .count()
        ):
            raise RuntimeError(f"{name} contains duplicate tract-horizon keys")
    if (
        forecasts.where(
            (
                functions.col("prediction_lower_cumulative_log_change")
                > functions.col("prediction_cumulative_log_change")
            )
            | (
                functions.col("prediction_upper_cumulative_log_change")
                < functions.col("prediction_cumulative_log_change")
            )
            | ~functions.col("horizon_years").isin(*release.horizons)
            | (functions.col("forecast_origin_year") != release.as_of_year)
        )
        .limit(1)
        .count()
    ):
        raise RuntimeError("Forecast serving rows violate interval, horizon, or as-of rules")
    available_keys = availability.where(functions.col("forecast_available")).select(
        "geoid_2020", "horizon_years"
    )
    forecast_keys = forecasts.select("geoid_2020", "horizon_years")
    if (
        available_keys.join(forecast_keys, ["geoid_2020", "horizon_years"], "left_anti")
        .limit(1)
        .count()
        or forecast_keys.join(available_keys, ["geoid_2020", "horizon_years"], "left_anti")
        .limit(1)
        .count()
    ):
        raise RuntimeError("Forecast rows do not reconcile to declared availability")
    return {
        FORECAST_SERVING_CURRENT_TABLE: forecasts.count(),
        FORECAST_SERVING_AVAILABILITY_TABLE: availability.count(),
    }


def build_forecast_release_manifest(
    spark: Any,
    release: ForecastServingRelease,
    row_counts: dict[str, int],
) -> Any:
    """Build activation rows compatible with the shared serving manifest."""

    required = {FORECAST_SERVING_CURRENT_TABLE, FORECAST_SERVING_AVAILABILITY_TABLE}
    if set(row_counts) != required or any(value <= 0 for value in row_counts.values()):
        raise ValueError("row_counts must contain both positive forecast serving counts")
    rows = [
        (
            release.release_id,
            FORECAST_SERVING_SCHEMA_VERSION,
            release.built_at_utc,
            FORECAST_SERVING_COMPONENT,
            table_name,
            int(row_counts[table_name]),
            release.as_of_year,
            ",".join(str(value) for value in release.horizons),
            None,
            release.model_readiness_build_id,
            None,
            FORECAST_SERVING_METHOD,
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

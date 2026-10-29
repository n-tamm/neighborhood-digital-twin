"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Leakage-safe historical feature, split, modeling-panel, and readiness products.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.historical import (
    DEFAULT_FORECAST_HORIZONS,
    HISTORICAL_STATE_TABLE,
    HISTORICAL_TARGET_TABLE,
    validate_forecast_horizons,
)
from neighborhood_twin.validate import QualityMetric, hard_failures, new_quality_run_id

MODEL_READINESS_SCHEMA_VERSION = "1.0.0"
MODEL_FEATURE_TABLE = "gold_model_feature_historical"
MODEL_SPLIT_TABLE = "gold_model_split_assignment"
MODELING_PANEL_TABLE = "gold_modeling_panel"
MODEL_READINESS_SUMMARY_TABLE = "gold_model_readiness_summary"
MODEL_READINESS_QUALITY_TABLE = "gold_quality_metrics"
DEFAULT_LOCKED_TEST_ORIGINS = {1: 2024, 3: 2022, 5: 2020}
DEFAULT_VALIDATION_ORIGIN_COUNTS = {1: 2, 3: 2, 5: 1}
DEFAULT_GEOGRAPHIC_HOLDOUT_SEED = 699

MODEL_ACS_FEATURE_COLUMNS = (
    "population_total_estimate",
    "population_total_moe",
    "housing_units_total_estimate",
    "housing_units_total_moe",
    "occupied_units_estimate",
    "vacant_units_estimate",
    "owner_occupied_units_estimate",
    "renter_occupied_units_estimate",
    "occupancy_rate_estimate",
    "vacancy_rate_estimate",
    "owner_occupancy_rate_estimate",
    "renter_occupancy_rate_estimate",
    "single_family_share_estimate",
    "multifamily_share_estimate",
    "mobile_home_share_estimate",
    "other_structure_share_estimate",
    "median_household_income_estimate",
    "median_household_income_moe",
    "median_owner_occupied_value_estimate",
    "median_owner_occupied_value_moe",
    "median_gross_rent_estimate",
    "median_gross_rent_moe",
)

TEMPORAL_ROLES = (
    "training",
    "validation",
    "calibration",
    "purged_pretest",
    "locked_temporal_test",
    "future_scoring",
    "ineligible_target",
)


@dataclass(frozen=True)
class SplitRule:
    """One horizon's frozen final-development and evaluation-year contract."""

    horizon_years: int
    locked_test_origin_year: int
    calibration_origin_year: int
    validation_start_origin_year: int
    validation_end_origin_year: int

    def to_record(self) -> dict[str, int]:
        """Return a Spark-compatible representation of the rule."""

        return {
            "horizon_years": self.horizon_years,
            "locked_test_origin_year": self.locked_test_origin_year,
            "calibration_origin_year": self.calibration_origin_year,
            "validation_start_origin_year": self.validation_start_origin_year,
            "validation_end_origin_year": self.validation_end_origin_year,
        }


@dataclass(frozen=True)
class ModelReadinessBuild:
    """Validated model-readiness frames and their unpublished quality metrics."""

    build_id: str
    built_at_utc: str
    frames: dict[str, Any]
    metrics: list[QualityMetric]


def parse_horizon_mapping(value: str, *, label: str) -> dict[int, int]:
    """Parse and validate a comma-separated `horizon:value` mapping."""

    mapping: dict[int, int] = {}
    for raw_item in value.split(","):
        item = raw_item.strip()
        if not item:
            continue
        parts = item.split(":")
        if len(parts) != 2:
            raise ValueError(f"{label} entries must use horizon:value syntax")
        try:
            horizon, mapped_value = (int(part.strip()) for part in parts)
        except ValueError as exc:
            raise ValueError(f"{label} entries must contain integers") from exc
        if horizon <= 0 or mapped_value <= 0:
            raise ValueError(f"{label} horizons and values must be positive")
        if horizon in mapping:
            raise ValueError(f"{label} must not repeat a horizon")
        mapping[horizon] = mapped_value
    if not mapping:
        raise ValueError(f"{label} must contain at least one mapping")
    return mapping


def build_split_rules(
    *,
    horizons: tuple[int, ...],
    locked_test_origins: Mapping[int, int],
    validation_origin_counts: Mapping[int, int],
) -> tuple[SplitRule, ...]:
    """Validate split inputs and derive calibration and validation years by horizon."""

    horizons = validate_forecast_horizons(horizons)
    if set(locked_test_origins) != set(horizons):
        raise ValueError("Locked test origins must define every configured horizon exactly once")
    if set(validation_origin_counts) != set(horizons):
        raise ValueError(
            "Validation origin counts must define every configured horizon exactly once"
        )
    rules = []
    for horizon in horizons:
        locked_origin = int(locked_test_origins[horizon])
        validation_count = int(validation_origin_counts[horizon])
        if locked_origin <= horizon:
            raise ValueError("Locked test origins must be later than their horizons")
        if validation_count <= 0:
            raise ValueError("Every horizon needs at least one validation origin")
        calibration_origin = locked_origin - horizon
        validation_end = calibration_origin - 1
        validation_start = validation_end - validation_count + 1
        rules.append(
            SplitRule(
                horizon_years=horizon,
                locked_test_origin_year=locked_origin,
                calibration_origin_year=calibration_origin,
                validation_start_origin_year=validation_start,
                validation_end_origin_year=validation_end,
            )
        )
    return tuple(rules)


def temporal_split_role(
    *,
    forecast_origin_year: int,
    target_end_year: int,
    target_is_observed: bool,
    rule: SplitRule,
) -> str:
    """Classify one target row under a frozen horizon-specific temporal contract."""

    if forecast_origin_year == rule.locked_test_origin_year and target_is_observed:
        return "locked_temporal_test"
    if forecast_origin_year > rule.locked_test_origin_year:
        return "future_scoring"
    if not target_is_observed:
        return "ineligible_target"
    if target_end_year > rule.locked_test_origin_year:
        return "purged_pretest"
    if forecast_origin_year == rule.calibration_origin_year:
        return "calibration"
    if (
        rule.validation_start_origin_year
        <= forecast_origin_year
        <= rule.validation_end_origin_year
    ):
        return "validation"
    if forecast_origin_year < rule.validation_start_origin_year:
        return "training"
    raise ValueError("Target row did not match the split contract")


def _metric(
    *,
    build_id: str,
    built_at_utc: str,
    table_name: str,
    metric_group: str,
    metric_name: str,
    value: int | float,
    status: str,
    expectation: str,
    dimension: str = "all",
    notes: str = "",
) -> QualityMetric:
    """Create one consistently shaped model-readiness quality metric."""

    return QualityMetric(
        quality_run_id=build_id,
        profiled_at_utc=built_at_utc,
        table_name=table_name,
        metric_group=metric_group,
        metric_name=metric_name,
        dimension=dimension,
        metric_value=float(value),
        status=status,
        expectation=expectation,
        notes=notes,
    )


def _lineage(frame: Any, *, build_id: str, built_at_utc: str) -> Any:
    """Attach the model-readiness contract and build lineage to a Spark frame."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        frame.withColumn(
            "model_readiness_schema_version",
            functions.lit(MODEL_READINESS_SCHEMA_VERSION),
        )
        .withColumn("model_readiness_build_id", functions.lit(build_id))
        .withColumn(
            "model_readiness_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
    )


def _relative_moe(functions: Any, estimate: str, moe: str) -> Any:
    """Return a null-safe relative margin-of-error expression."""

    return functions.when(
        functions.col(estimate).isNotNull()
        & (functions.abs(functions.col(estimate)) > 0)
        & functions.col(moe).isNotNull(),
        functions.col(moe) / functions.abs(functions.col(estimate)),
    )


def _build_model_features(
    state: Any,
    targets: Any,
    *,
    build_id: str,
    built_at_utc: str,
) -> Any:
    """Build one raw, interpretable, point-in-time feature row per tract and origin."""

    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    origins = targets.select(
        "geoid_2020",
        "state_fips",
        "state_abbreviation",
        "state_name",
        "county_geoid",
        "county_name",
        "region_code",
        "region_name",
        "division_code",
        "division_name",
        "forecast_origin_year",
        "origin_hpi",
        "origin_annual_change_pct",
        "origin_source_snapshot_id",
    ).dropDuplicates(["geoid_2020", "forecast_origin_year"])

    history_window = Window.partitionBy("geoid_2020").orderBy("forecast_origin_year")
    history_to_origin = history_window.rowsBetween(Window.unboundedPreceding, Window.currentRow)
    recent_three_years = history_window.rangeBetween(-2, 0)
    recent_five_years = history_window.rangeBetween(-4, 0)
    hpi = (
        origins.withColumn(
            "hpi_lag_1_year",
            functions.lag("forecast_origin_year", 1).over(history_window),
        )
        .withColumn("hpi_lag_1", functions.lag("origin_hpi", 1).over(history_window))
        .withColumn("hpi_lag_3_year", functions.lag("forecast_origin_year", 3).over(history_window))
        .withColumn("hpi_lag_3", functions.lag("origin_hpi", 3).over(history_window))
        .withColumn("hpi_lag_5_year", functions.lag("forecast_origin_year", 5).over(history_window))
        .withColumn("hpi_lag_5", functions.lag("origin_hpi", 5).over(history_window))
        .withColumn(
            "hpi_lag_1",
            functions.when(
                functions.col("hpi_lag_1_year") == functions.col("forecast_origin_year") - 1,
                functions.col("hpi_lag_1"),
            ),
        )
        .withColumn(
            "hpi_lag_3",
            functions.when(
                functions.col("hpi_lag_3_year") == functions.col("forecast_origin_year") - 3,
                functions.col("hpi_lag_3"),
            ),
        )
        .withColumn(
            "hpi_lag_5",
            functions.when(
                functions.col("hpi_lag_5_year") == functions.col("forecast_origin_year") - 5,
                functions.col("hpi_lag_5"),
            ),
        )
        .withColumn(
            "hpi_change_1_year_pct",
            functions.when(
                functions.col("hpi_lag_1").isNotNull() & (functions.col("hpi_lag_1") > 0),
                (functions.col("origin_hpi") / functions.col("hpi_lag_1") - 1) * 100,
            ),
        )
        .withColumn(
            "hpi_change_3_year_pct",
            functions.when(
                functions.col("hpi_lag_3").isNotNull() & (functions.col("hpi_lag_3") > 0),
                (functions.col("origin_hpi") / functions.col("hpi_lag_3") - 1) * 100,
            ),
        )
        .withColumn(
            "hpi_change_5_year_pct",
            functions.when(
                functions.col("hpi_lag_5").isNotNull() & (functions.col("hpi_lag_5") > 0),
                (functions.col("origin_hpi") / functions.col("hpi_lag_5") - 1) * 100,
            ),
        )
        .withColumn(
            "hpi_recent_3_year_mean_change_pct",
            functions.avg("origin_annual_change_pct").over(recent_three_years),
        )
        .withColumn(
            "hpi_recent_5_year_change_stddev_pct",
            functions.stddev_samp("origin_annual_change_pct").over(recent_five_years),
        )
        .withColumn(
            "hpi_history_first_year",
            functions.min("forecast_origin_year").over(history_to_origin),
        )
        .withColumn(
            "hpi_history_observation_count",
            functions.count("origin_hpi").over(history_to_origin),
        )
        .withColumn(
            "hpi_history_year_span",
            functions.col("forecast_origin_year")
            - functions.col("hpi_history_first_year")
            + 1,
        )
        .withColumn(
            "hpi_history_gap_count",
            functions.col("hpi_history_year_span")
            - functions.col("hpi_history_observation_count"),
        )
    )

    county_context = origins.groupBy("county_geoid", "forecast_origin_year").agg(
        functions.avg("origin_annual_change_pct").alias(
            "county_origin_mean_annual_change_pct"
        ),
        functions.percentile_approx("origin_annual_change_pct", 0.5, 10000).alias(
            "county_origin_median_annual_change_pct"
        ),
        functions.count("origin_annual_change_pct").alias("county_origin_tract_count"),
    )
    state_context = origins.groupBy("state_fips", "forecast_origin_year").agg(
        functions.avg("origin_annual_change_pct").alias(
            "state_origin_mean_annual_change_pct"
        ),
        functions.percentile_approx("origin_annual_change_pct", 0.5, 10000).alias(
            "state_origin_median_annual_change_pct"
        ),
        functions.count("origin_annual_change_pct").alias("state_origin_tract_count"),
    )
    hpi = hpi.join(
        county_context,
        ["county_geoid", "forecast_origin_year"],
        "left",
    ).join(
        state_context,
        ["state_fips", "forecast_origin_year"],
        "left",
    )

    as_of = hpi.alias("origin").join(
        state.alias("state"),
        (functions.col("origin.geoid_2020") == functions.col("state.geoid_2020"))
        & (
            functions.col("state.acs_available_year")
            <= functions.col("origin.forecast_origin_year")
        ),
        "inner",
    )
    as_of_window = Window.partitionBy(
        functions.col("origin.geoid_2020"),
        functions.col("origin.forecast_origin_year"),
    ).orderBy(
        functions.col("state.acs_available_year").desc(),
        functions.col("state.acs_release_year").desc(),
    )
    selected = as_of.withColumn("_as_of_rank", functions.row_number().over(as_of_window)).where(
        functions.col("_as_of_rank") == 1
    )
    stable_tracts = (
        state.where(functions.col("acs_release_year") < 2020)
        .select("geoid_2020")
        .distinct()
        .withColumn("is_stable_longitudinal_cohort", functions.lit(True))
    )

    origin_columns = (
        "geoid_2020",
        "state_fips",
        "state_abbreviation",
        "state_name",
        "county_geoid",
        "county_name",
        "region_code",
        "region_name",
        "division_code",
        "division_name",
        "forecast_origin_year",
        "origin_hpi",
        "origin_annual_change_pct",
        "hpi_lag_1_year",
        "hpi_lag_1",
        "hpi_lag_3_year",
        "hpi_lag_3",
        "hpi_lag_5_year",
        "hpi_lag_5",
        "hpi_change_1_year_pct",
        "hpi_change_3_year_pct",
        "hpi_change_5_year_pct",
        "hpi_recent_3_year_mean_change_pct",
        "hpi_recent_5_year_change_stddev_pct",
        "hpi_history_first_year",
        "hpi_history_observation_count",
        "hpi_history_year_span",
        "hpi_history_gap_count",
        "county_origin_mean_annual_change_pct",
        "county_origin_median_annual_change_pct",
        "county_origin_tract_count",
        "state_origin_mean_annual_change_pct",
        "state_origin_median_annual_change_pct",
        "state_origin_tract_count",
        "origin_source_snapshot_id",
    )
    feature = selected.select(
        *tuple(functions.col(f"origin.{column}").alias(column) for column in origin_columns),
        functions.col("state.acs_source_geoid").alias("acs_source_geoid"),
        functions.col("state.acs_release_year").alias("acs_release_year"),
        functions.col("state.acs_available_year").alias("acs_available_year"),
        functions.col("state.acs_survey_start_year").alias("acs_survey_start_year"),
        functions.col("state.acs_survey_end_year").alias("acs_survey_end_year"),
        functions.col("state.acs_reference_period").alias("acs_reference_period"),
        functions.col("state.source_geography_vintage").alias(
            "source_geography_vintage"
        ),
        functions.col("state.geography_alignment_method").alias(
            "geography_alignment_method"
        ),
        *tuple(
            functions.col(f"state.{column}").alias(column)
            for column in MODEL_ACS_FEATURE_COLUMNS
        ),
        functions.col("state.source_snapshot_id").alias("acs_source_snapshot_id"),
        functions.col("state.source_retrieval_timestamp_utc").alias(
            "acs_source_retrieval_timestamp_utc"
        ),
    ).join(stable_tracts, "geoid_2020", "left")

    feature = (
        feature.fillna({"is_stable_longitudinal_cohort": False})
        .withColumn(
            "acs_measurement_age_years",
            functions.col("forecast_origin_year") - functions.col("acs_available_year"),
        )
        .withColumn(
            "uses_post_2020_broad_coverage",
            functions.col("acs_release_year") >= 2020,
        )
        .withColumn(
            "modeling_cohort",
            functions.when(
                functions.col("is_stable_longitudinal_cohort"),
                functions.lit("stable_longitudinal"),
            ).otherwise(functions.lit("post_2020_broad_only")),
        )
        .withColumn(
            "has_minimum_hpi_history",
            functions.col("hpi_history_observation_count") >= 10,
        )
        .withColumn(
            "population_total_relative_moe",
            _relative_moe(
                functions,
                "population_total_estimate",
                "population_total_moe",
            ),
        )
        .withColumn(
            "housing_units_total_relative_moe",
            _relative_moe(
                functions,
                "housing_units_total_estimate",
                "housing_units_total_moe",
            ),
        )
        .withColumn(
            "median_household_income_relative_moe",
            _relative_moe(
                functions,
                "median_household_income_estimate",
                "median_household_income_moe",
            ),
        )
        .withColumn(
            "median_owner_occupied_value_relative_moe",
            _relative_moe(
                functions,
                "median_owner_occupied_value_estimate",
                "median_owner_occupied_value_moe",
            ),
        )
        .withColumn(
            "median_gross_rent_relative_moe",
            _relative_moe(
                functions,
                "median_gross_rent_estimate",
                "median_gross_rent_moe",
            ),
        )
    )
    return _lineage(feature, build_id=build_id, built_at_utc=built_at_utc)


def _holdout_states(features: Any, *, seed: int) -> Any:
    """Choose one reproducible non-DC state per represented Census region."""

    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    states = features.where(functions.col("state_fips") != "11").select(
        "region_code",
        "region_name",
        "state_fips",
        "state_abbreviation",
        "state_name",
    ).distinct()
    ranking = Window.partitionBy("region_code").orderBy(
        functions.xxhash64(functions.lit(seed), functions.col("state_fips")),
        functions.col("state_fips"),
    )
    return states.withColumn("_holdout_rank", functions.row_number().over(ranking)).where(
        functions.col("_holdout_rank") == 1
    ).drop("_holdout_rank")


def _build_split_assignments(
    features: Any,
    targets: Any,
    *,
    rules: tuple[SplitRule, ...],
    geographic_holdout_seed: int,
    build_id: str,
    built_at_utc: str,
) -> Any:
    """Assign frozen temporal roles and deterministic geographic holdouts."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    spark = features.sparkSession
    rule_frame = spark.createDataFrame([rule.to_record() for rule in rules])
    feature_keys = features.select(
        "geoid_2020",
        "forecast_origin_year",
        "state_fips",
        "region_code",
        "modeling_cohort",
        "is_stable_longitudinal_cohort",
        "has_minimum_hpi_history",
    )
    holdouts = _holdout_states(features, seed=geographic_holdout_seed).select(
        functions.col("state_fips").alias("holdout_state_fips")
    )
    base = (
        targets.join(
            feature_keys,
            ["geoid_2020", "forecast_origin_year", "state_fips", "region_code"],
            "inner",
        )
        .join(rule_frame, "horizon_years", "inner")
        .join(
            holdouts,
            functions.col("state_fips") == functions.col("holdout_state_fips"),
            "left",
        )
    )
    temporal_role = (
        functions.when(
            (functions.col("forecast_origin_year") == functions.col("locked_test_origin_year"))
            & functions.col("target_is_observed"),
            functions.lit("locked_temporal_test"),
        )
        .when(
            functions.col("forecast_origin_year") > functions.col("locked_test_origin_year"),
            functions.lit("future_scoring"),
        )
        .when(~functions.col("target_is_observed"), functions.lit("ineligible_target"))
        .when(
            functions.col("target_end_year") > functions.col("locked_test_origin_year"),
            functions.lit("purged_pretest"),
        )
        .when(
            functions.col("forecast_origin_year") == functions.col("calibration_origin_year"),
            functions.lit("calibration"),
        )
        .when(
            functions.col("forecast_origin_year").between(
                functions.col("validation_start_origin_year"),
                functions.col("validation_end_origin_year"),
            ),
            functions.lit("validation"),
        )
        .when(
            functions.col("forecast_origin_year")
            < functions.col("validation_start_origin_year"),
            functions.lit("training"),
        )
        .otherwise(functions.lit("unassigned"))
    )
    split = (
        base.withColumn("temporal_role", temporal_role)
        .withColumn(
            "geographic_role",
            functions.when(
                functions.col("holdout_state_fips").isNotNull(),
                functions.lit("geographic_holdout"),
            ).otherwise(functions.lit("geographic_development")),
        )
        .withColumn(
            "target_known_by_locked_test_origin",
            functions.col("target_is_observed")
            & (
                functions.col("target_end_year")
                <= functions.col("locked_test_origin_year")
            ),
        )
        .withColumn(
            "eligible_for_point_model_fit",
            (functions.col("temporal_role") == "training")
            & (functions.col("geographic_role") == "geographic_development"),
        )
        .withColumn(
            "eligible_for_hyperparameter_selection",
            functions.col("temporal_role").isin("training", "validation")
            & (functions.col("geographic_role") == "geographic_development"),
        )
        .withColumn(
            "eligible_for_interval_calibration",
            (functions.col("temporal_role") == "calibration")
            & (functions.col("geographic_role") == "geographic_development"),
        )
        .withColumn(
            "eligible_for_locked_temporal_evaluation",
            functions.col("temporal_role") == "locked_temporal_test",
        )
        .withColumn(
            "eligible_for_geographic_evaluation",
            (functions.col("geographic_role") == "geographic_holdout")
            & functions.col("temporal_role").isin("validation", "locked_temporal_test"),
        )
        .withColumn("geographic_holdout_seed", functions.lit(geographic_holdout_seed))
        .withColumn(
            "geographic_holdout_method",
            functions.lit("one_non_dc_state_per_census_region_xxhash64"),
        )
        .select(
            "geoid_2020",
            "state_fips",
            "region_code",
            "forecast_origin_year",
            "horizon_years",
            "target_end_year",
            "target_is_observed",
            "target_censor_reason",
            "modeling_cohort",
            "is_stable_longitudinal_cohort",
            "has_minimum_hpi_history",
            "locked_test_origin_year",
            "calibration_origin_year",
            "validation_start_origin_year",
            "validation_end_origin_year",
            "temporal_role",
            "geographic_role",
            "target_known_by_locked_test_origin",
            "eligible_for_point_model_fit",
            "eligible_for_hyperparameter_selection",
            "eligible_for_interval_calibration",
            "eligible_for_locked_temporal_evaluation",
            "eligible_for_geographic_evaluation",
            "geographic_holdout_seed",
            "geographic_holdout_method",
        )
    )
    return _lineage(split, build_id=build_id, built_at_utc=built_at_utc)


def _build_modeling_panel(
    features: Any,
    targets: Any,
    splits: Any,
    *,
    build_id: str,
    built_at_utc: str,
) -> Any:
    """Join raw point-in-time features, direct targets, and frozen assignments."""

    key = ["geoid_2020", "forecast_origin_year", "horizon_years"]
    split_columns = (
        "geoid_2020",
        "forecast_origin_year",
        "horizon_years",
        "locked_test_origin_year",
        "calibration_origin_year",
        "validation_start_origin_year",
        "validation_end_origin_year",
        "temporal_role",
        "geographic_role",
        "target_known_by_locked_test_origin",
        "eligible_for_point_model_fit",
        "eligible_for_hyperparameter_selection",
        "eligible_for_interval_calibration",
        "eligible_for_locked_temporal_evaluation",
        "eligible_for_geographic_evaluation",
        "geographic_holdout_seed",
        "geographic_holdout_method",
    )
    target_columns = (
        "geoid_2020",
        "forecast_origin_year",
        "horizon_years",
        "target_end_year",
        "target_end_hpi",
        "target_cumulative_log_change",
        "target_annualized_change_pct",
        "target_is_observed",
        "target_censor_reason",
        "target_end_source_snapshot_id",
    )
    panel = features.join(
        splits.select(*split_columns),
        ["geoid_2020", "forecast_origin_year"],
    ).join(targets.select(*target_columns), key, "inner")
    return _lineage(
        panel.drop(
            "model_readiness_schema_version",
            "model_readiness_build_id",
            "model_readiness_built_at_utc",
        ),
        build_id=build_id,
        built_at_utc=built_at_utc,
    )


def _build_readiness_summary(
    features: Any,
    panel: Any,
    *,
    build_id: str,
    built_at_utc: str,
) -> Any:
    """Summarize feature coverage and panel roles for review before model fitting."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    feature_summary = features.groupBy("modeling_cohort").agg(
        functions.count(functions.lit(1)).alias("row_count"),
        functions.countDistinct("geoid_2020").alias("distinct_tract_count"),
        functions.countDistinct("forecast_origin_year").alias("origin_year_count"),
        functions.min("forecast_origin_year").alias("minimum_origin_year"),
        functions.max("forecast_origin_year").alias("maximum_origin_year"),
    ).select(
        functions.lit("feature_cohort").alias("summary_group"),
        functions.lit(None).cast("int").alias("horizon_years"),
        functions.lit("modeling_cohort").alias("dimension_name"),
        functions.col("modeling_cohort").alias("dimension_value"),
        "row_count",
        "distinct_tract_count",
        "origin_year_count",
        "minimum_origin_year",
        "maximum_origin_year",
        functions.lit(None).cast("long").alias("observed_target_count"),
        functions.lit(None).cast("long").alias("eligible_evaluation_count"),
    )

    def panel_summary(group: str, dimension: str) -> Any:
        """Aggregate the modeling panel by one governed review dimension."""

        return panel.groupBy("horizon_years", dimension).agg(
            functions.count(functions.lit(1)).alias("row_count"),
            functions.countDistinct("geoid_2020").alias("distinct_tract_count"),
            functions.countDistinct("forecast_origin_year").alias("origin_year_count"),
            functions.min("forecast_origin_year").alias("minimum_origin_year"),
            functions.max("forecast_origin_year").alias("maximum_origin_year"),
            functions.sum(functions.col("target_is_observed").cast("long")).alias(
                "observed_target_count"
            ),
            functions.sum(
                functions.col("eligible_for_locked_temporal_evaluation").cast("long")
            ).alias("eligible_evaluation_count"),
        ).select(
            functions.lit(group).alias("summary_group"),
            "horizon_years",
            functions.lit(dimension).alias("dimension_name"),
            functions.col(dimension).alias("dimension_value"),
            "row_count",
            "distinct_tract_count",
            "origin_year_count",
            "minimum_origin_year",
            "maximum_origin_year",
            "observed_target_count",
            "eligible_evaluation_count",
        )

    summary = feature_summary
    for group, dimension in (
        ("panel_temporal_role", "temporal_role"),
        ("panel_geographic_role", "geographic_role"),
        ("panel_modeling_cohort", "modeling_cohort"),
    ):
        summary = summary.unionByName(panel_summary(group, dimension))
    return _lineage(summary, build_id=build_id, built_at_utc=built_at_utc)


def _quality_metrics(
    frames: dict[str, Any],
    *,
    rules: tuple[SplitRule, ...],
    build_id: str,
    built_at_utc: str,
    catalog: str,
    schema: str,
) -> list[QualityMetric]:
    """Validate keys, point-in-time timing, split roles, and table reconciliation."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    keys = {
        MODEL_FEATURE_TABLE: ("geoid_2020", "forecast_origin_year"),
        MODEL_SPLIT_TABLE: ("geoid_2020", "forecast_origin_year", "horizon_years"),
        MODELING_PANEL_TABLE: ("geoid_2020", "forecast_origin_year", "horizon_years"),
        MODEL_READINESS_SUMMARY_TABLE: (
            "summary_group",
            "horizon_years",
            "dimension_name",
            "dimension_value",
        ),
    }
    metrics: list[QualityMetric] = []
    row_counts: dict[str, int] = {}
    for table, frame in frames.items():
        row_count = frame.count()
        row_counts[table] = row_count
        duplicate_count = row_count - frame.select(*keys[table]).distinct().count()
        for metric_name, value, status, expectation in (
            ("row_count", row_count, "pass" if row_count > 0 else "fail", "> 0"),
            (
                "duplicate_key_count",
                duplicate_count,
                "pass" if duplicate_count == 0 else "fail",
                "= 0",
            ),
        ):
            metrics.append(
                _metric(
                    build_id=build_id,
                    built_at_utc=built_at_utc,
                    table_name=f"{catalog}.{schema}.{table}",
                    metric_group="model_readiness",
                    metric_name=metric_name,
                    value=value,
                    status=status,
                    expectation=expectation,
                )
            )

    features = frames[MODEL_FEATURE_TABLE]
    splits = frames[MODEL_SPLIT_TABLE]
    panel = frames[MODELING_PANEL_TABLE]
    invalid_feature_timing = features.where(
        functions.col("acs_available_year") > functions.col("forecast_origin_year")
    ).count()
    invalid_feature_age = features.where(functions.col("acs_measurement_age_years") < 0).count()
    invalid_hpi_gap = features.where(functions.col("hpi_history_gap_count") < 0).count()
    invalid_pre_2021_cohort = features.where(
        (functions.col("forecast_origin_year") <= 2020)
        & (~functions.col("is_stable_longitudinal_cohort"))
    ).count()
    unexpected_role_count = splits.where(
        ~functions.col("temporal_role").isin(*TEMPORAL_ROLES)
    ).count()
    invalid_cutoff_count = splits.where(
        functions.col("temporal_role").isin("training", "validation", "calibration")
        & (
            functions.col("target_end_year")
            > functions.col("locked_test_origin_year")
        )
    ).count()
    invalid_fit_flag_count = splits.where(
        functions.col("eligible_for_point_model_fit")
        & (
            (functions.col("temporal_role") != "training")
            | (functions.col("geographic_role") != "geographic_development")
        )
    ).count()
    holdout_by_region = (
        splits.where(functions.col("geographic_role") == "geographic_holdout")
        .select("region_code", "state_fips")
        .distinct()
        .groupBy("region_code")
        .agg(functions.countDistinct("state_fips").alias("holdout_state_count"))
    )
    invalid_holdout_region_count = holdout_by_region.where(
        functions.col("holdout_state_count") != 1
    ).count() + abs(4 - holdout_by_region.count())
    invalid_panel_feature_timing = panel.where(
        functions.col("acs_available_year") > functions.col("forecast_origin_year")
    ).count()
    invalid_panel_target_timing = panel.where(
        functions.col("target_end_year")
        != functions.col("forecast_origin_year") + functions.col("horizon_years")
    ).count()
    checks = (
        (
            MODEL_FEATURE_TABLE,
            "future_acs_selection_count",
            invalid_feature_timing,
            "= 0; ACS availability must not exceed the forecast origin",
        ),
        (
            MODEL_FEATURE_TABLE,
            "negative_acs_measurement_age_count",
            invalid_feature_age,
            "= 0",
        ),
        (
            MODEL_FEATURE_TABLE,
            "negative_hpi_history_gap_count",
            invalid_hpi_gap,
            "= 0",
        ),
        (
            MODEL_FEATURE_TABLE,
            "pre_2021_nonstable_cohort_count",
            invalid_pre_2021_cohort,
            "= 0; early feature rows must use the stable cohort",
        ),
        (
            MODEL_SPLIT_TABLE,
            "unexpected_temporal_role_count",
            unexpected_role_count,
            "= 0",
        ),
        (
            MODEL_SPLIT_TABLE,
            "future_label_in_development_count",
            invalid_cutoff_count,
            "= 0",
        ),
        (
            MODEL_SPLIT_TABLE,
            "invalid_point_model_fit_flag_count",
            invalid_fit_flag_count,
            "= 0",
        ),
        (
            MODEL_SPLIT_TABLE,
            "invalid_geographic_holdout_region_count",
            invalid_holdout_region_count,
            "= 0; one holdout state in each of four Census regions",
        ),
        (
            MODELING_PANEL_TABLE,
            "split_panel_row_difference",
            abs(row_counts[MODEL_SPLIT_TABLE] - row_counts[MODELING_PANEL_TABLE]),
            "= 0",
        ),
        (
            MODELING_PANEL_TABLE,
            "future_acs_selection_count",
            invalid_panel_feature_timing,
            "= 0",
        ),
        (
            MODELING_PANEL_TABLE,
            "invalid_target_timing_count",
            invalid_panel_target_timing,
            "= 0",
        ),
    )
    for table, metric_name, value, expectation in checks:
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=f"{catalog}.{schema}.{table}",
                metric_group="model_readiness",
                metric_name=metric_name,
                value=value,
                status="pass" if value == 0 else "fail",
                expectation=expectation,
            )
        )

    role_counts = splits.groupBy("horizon_years", "temporal_role").count().collect()
    for row in role_counts:
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=f"{catalog}.{schema}.{MODEL_SPLIT_TABLE}",
                metric_group="split_coverage",
                metric_name="row_count",
                value=int(row["count"]),
                status="info",
                expectation="reported by horizon and temporal role",
                dimension=(
                    f"horizon={int(row['horizon_years'])};role={row['temporal_role']}"
                ),
            )
        )
    for rule in rules:
        training_origin_count = (
            splits.where(
                (functions.col("horizon_years") == rule.horizon_years)
                & (functions.col("temporal_role") == "training")
            )
            .select("forecast_origin_year")
            .distinct()
            .count()
        )
        metrics.append(
            _metric(
                build_id=build_id,
                built_at_utc=built_at_utc,
                table_name=f"{catalog}.{schema}.{MODEL_SPLIT_TABLE}",
                metric_group="split_coverage",
                metric_name="training_origin_year_count",
                value=training_origin_count,
                status="warn" if training_origin_count < 5 else "pass",
                expectation=">= 5 preferred; smaller horizons remain exploratory",
                dimension=f"horizon={rule.horizon_years}",
                notes=(
                    "Limited independent origins should constrain model complexity and claims."
                    if training_origin_count < 5
                    else ""
                ),
            )
        )
    return metrics


def prepare_model_readiness_build(
    spark: Any,
    *,
    catalog: str,
    gold_schema: str,
    horizons: tuple[int, ...] = DEFAULT_FORECAST_HORIZONS,
    locked_test_origins: Mapping[int, int] = DEFAULT_LOCKED_TEST_ORIGINS,
    validation_origin_counts: Mapping[int, int] = DEFAULT_VALIDATION_ORIGIN_COUNTS,
    geographic_holdout_seed: int = DEFAULT_GEOGRAPHIC_HOLDOUT_SEED,
    built_at: datetime | None = None,
) -> ModelReadinessBuild:
    """Build and validate model features, assignments, panel, and readiness summaries."""

    if geographic_holdout_seed < 0:
        raise ValueError("Geographic holdout seed must be nonnegative")
    rules = build_split_rules(
        horizons=horizons,
        locked_test_origins=locked_test_origins,
        validation_origin_counts=validation_origin_counts,
    )
    required = {
        "state": f"{catalog}.{gold_schema}.{HISTORICAL_STATE_TABLE}",
        "targets": f"{catalog}.{gold_schema}.{HISTORICAL_TARGET_TABLE}",
    }
    missing = [name for name in required.values() if not spark.catalog.tableExists(name)]
    if missing:
        raise ValueError(f"Required model-readiness inputs do not exist: {', '.join(missing)}")

    build_id, built_at_utc = new_quality_run_id(built_at)
    state = spark.table(required["state"])
    targets = spark.table(required["targets"])
    features = _build_model_features(
        state,
        targets,
        build_id=build_id,
        built_at_utc=built_at_utc,
    ).cache()
    splits = _build_split_assignments(
        features,
        targets,
        rules=rules,
        geographic_holdout_seed=geographic_holdout_seed,
        build_id=build_id,
        built_at_utc=built_at_utc,
    ).cache()
    panel = _build_modeling_panel(
        features,
        targets,
        splits,
        build_id=build_id,
        built_at_utc=built_at_utc,
    ).cache()
    summary = _build_readiness_summary(
        features,
        panel,
        build_id=build_id,
        built_at_utc=built_at_utc,
    )
    frames = {
        MODEL_FEATURE_TABLE: features,
        MODEL_SPLIT_TABLE: splits,
        MODELING_PANEL_TABLE: panel,
        MODEL_READINESS_SUMMARY_TABLE: summary,
    }
    metrics = _quality_metrics(
        frames,
        rules=rules,
        build_id=build_id,
        built_at_utc=built_at_utc,
        catalog=catalog,
        schema=gold_schema,
    )
    return ModelReadinessBuild(build_id, built_at_utc, frames, metrics)


def publish_model_readiness_build(
    build: ModelReadinessBuild,
    *,
    catalog: str,
    schema: str,
) -> tuple[str, ...]:
    """Publish all model-readiness frames only after hard checks pass."""

    failures = hard_failures(build.metrics)
    if failures:
        names = ", ".join(
            f"{metric.table_name}:{metric.metric_name}" for metric in failures
        )
        raise ValueError(f"Model-readiness build has hard quality failures: {names}")
    published = []
    for table, frame in build.frames.items():
        name = qualified_name(catalog, schema, table)
        (
            frame.write.format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(name)
        )
        published.append(name)
    return tuple(published)

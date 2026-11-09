"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Expanded validation and representation-selection utilities for historical analogues.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from neighborhood_twin.historical_analogues import (
    DEFAULT_COMPARATOR_MODELS,
    DEFAULT_HORIZONS,
    DEFAULT_PCA_COMPONENTS,
    build_historical_analogue_run,
    build_historical_analogue_scorecard,
)

ANALOGUE_SELECTION_SCHEMA_VERSION = "1.0.0"
ANALOGUE_SELECTION_MATCH_TABLE = "historical_analogue_selection_match"
ANALOGUE_SELECTION_PREDICTION_TABLE = "historical_analogue_selection_prediction"
ANALOGUE_SELECTION_SUMMARY_TABLE = "historical_analogue_selection_summary"
ANALOGUE_SELECTION_SCORECARD_TABLE = "historical_analogue_selection_scorecard"
ANALOGUE_SELECTION_COVERAGE_TABLE = "historical_analogue_selection_coverage"

DEFAULT_SELECTION_QUERIES_PER_GROUP = 5

REQUIRED_SELECTION_COVERAGE_COLUMNS = (
    "query_housing_composition_band",
    "query_community_size_band",
    "query_acs_uncertainty_band",
)

SELECTION_SCORECARD_SLICES = (
    ("housing_composition_band", "query_housing_composition_band"),
    ("community_size_band", "query_community_size_band"),
    ("acs_uncertainty_band", "query_acs_uncertainty_band"),
)

SELECTION_COVERAGE_DIMENSIONS = (
    ("overall", "query_overall"),
    ("query_origin_year", "query_origin_year_label"),
    ("census_region", "region_name"),
    ("evaluation_geography", "query_evaluation_geography"),
    ("modeling_cohort", "modeling_cohort"),
    ("housing_composition_band", "query_housing_composition_band"),
    ("community_size_band", "query_community_size_band"),
    ("acs_uncertainty_band", "query_acs_uncertainty_band"),
    ("sampling_stratum", "query_sampling_stratum"),
)


@dataclass(frozen=True)
class AnalogueSelectionRun:
    """Expanded matches, predictions, diagnostics, scorecards, and sample coverage."""

    run_id: str
    built_at_utc: str
    matches: Any
    predictions: Any
    summary: Any
    scorecard: Any
    coverage: Any


def validate_selection_settings(*, queries_per_group: int, top_k: int) -> None:
    """Require a genuine sample expansion and enough matches for an outcome range."""

    if queries_per_group <= 1:
        raise ValueError("queries_per_group must exceed one for expanded evaluation")
    if top_k < 3:
        raise ValueError("top_k must be at least three for analogue outcome summaries")


def community_size_band(column: Any, functions: Any) -> Any:
    """Return readable population bands for expanded-query coverage review."""

    return (
        functions.when(column.isNull(), functions.lit("Missing"))
        .when(column < 2_500, functions.lit("Under 2,500"))
        .when(column < 5_000, functions.lit("2,500 to under 5,000"))
        .when(column < 10_000, functions.lit("5,000 to under 10,000"))
        .otherwise(functions.lit("10,000 or more"))
    )


def _comparator_complete_keys(
    forecast_predictions: Any,
    *,
    comparator_models: tuple[str, ...],
) -> Any:
    """Return query keys covered by every comparator required by the selection run."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        forecast_predictions.where(functions.col("model_name").isin(*comparator_models))
        .groupBy("geoid_2020", "forecast_origin_year", "horizon_years")
        .agg(functions.countDistinct("model_name").alias("_comparator_count"))
        .where(functions.col("_comparator_count") == len(comparator_models))
        .drop("_comparator_count")
    )


def _add_query_dimensions(frame: Any) -> Any:
    """Attach the governed coverage dimensions used to assess the expanded sample."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    from neighborhood_twin.forecasting import (
        acs_uncertainty_band,
        housing_composition_band,
    )

    return (
        frame.withColumn("query_overall", functions.lit("all"))
        .withColumn(
            "query_origin_year_label",
            functions.col("forecast_origin_year").cast("string"),
        )
        .withColumn(
            "query_evaluation_geography",
            functions.when(
                functions.col("geographic_role") == "geographic_holdout",
                functions.lit("held_out_state"),
            ).otherwise(functions.lit("development_states")),
        )
        .withColumn(
            "query_housing_composition_band",
            housing_composition_band(
                functions.col("single_family_share_estimate"),
                functions,
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
        .withColumn(
            "query_sampling_stratum",
            functions.concat_ws(
                " | ",
                functions.col("forecast_origin_year").cast("string"),
                functions.col("region_name"),
                functions.col("geographic_role"),
            ),
        )
    )


def eligible_selection_queries(
    modeling_panel: Any,
    forecast_predictions: Any,
    *,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS,
    comparator_models: tuple[str, ...] = DEFAULT_COMPARATOR_MODELS,
) -> Any:
    """Return validation queries eligible for identical analogue and forecast evaluation."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    if not horizons or any(horizon <= 0 for horizon in horizons):
        raise ValueError("horizons must contain positive integers")
    if not comparator_models:
        raise ValueError("At least one forecast comparator is required")
    comparator_keys = _comparator_complete_keys(
        forecast_predictions,
        comparator_models=comparator_models,
    )
    eligible = (
        modeling_panel.where(
            (functions.col("temporal_role") == "validation")
            & functions.col("target_is_observed")
            & functions.col("horizon_years").isin(*horizons)
        )
        .join(
            comparator_keys,
            ["geoid_2020", "forecast_origin_year", "horizon_years"],
            "inner",
        )
    )
    if eligible.limit(1).count() == 0:
        raise ValueError("No validation queries satisfy the expanded selection contract")
    return _add_query_dimensions(eligible)


def _selected_query_keys(predictions: Any) -> Any:
    """Extract one row per query from analogue and comparator prediction output."""

    return predictions.select(
        "query_geoid_2020",
        "query_origin_year",
        "horizon_years",
    ).distinct()


def _selected_query_dimensions(eligible: Any, predictions: Any) -> Any:
    """Join selected query keys back to their governed panel dimensions."""

    selected = _selected_query_keys(predictions).selectExpr(
        "query_geoid_2020 AS geoid_2020",
        "query_origin_year AS forecast_origin_year",
        "horizon_years",
    )
    return eligible.join(
        selected,
        ["geoid_2020", "forecast_origin_year", "horizon_years"],
        "inner",
    )


def incomplete_sampling_strata(
    eligible: Any,
    selected: Any,
    *,
    queries_per_group: int,
) -> Any:
    """Return sampling strata that do not contain the deterministic requested query count."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    group_columns = (
        "horizon_years",
        "forecast_origin_year",
        "region_name",
        "geographic_role",
    )
    eligible_counts = eligible.groupBy(*group_columns).agg(
        functions.count(functions.lit(1)).alias("eligible_query_count")
    )
    selected_counts = selected.groupBy(*group_columns).agg(
        functions.count(functions.lit(1)).alias("selected_query_count")
    )
    return (
        eligible_counts.join(selected_counts, list(group_columns), "left")
        .fillna(0, subset=["selected_query_count"])
        .withColumn(
            "expected_selected_query_count",
            functions.least(
                functions.col("eligible_query_count"),
                functions.lit(queries_per_group),
            ),
        )
        .where(
            functions.col("selected_query_count")
            < functions.col("expected_selected_query_count")
        )
    )


def _dimension_counts(frame: Any, *, count_prefix: str) -> Any:
    """Aggregate one query population across every declared coverage dimension."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    outputs = []
    for dimension_name, column_name in SELECTION_COVERAGE_DIMENSIONS:
        outputs.append(
            frame.groupBy(
                "horizon_years",
                functions.lit(dimension_name).alias("dimension_name"),
                functions.col(column_name).cast("string").alias("dimension_value"),
            ).agg(
                functions.count(functions.lit(1)).alias(f"{count_prefix}_query_count"),
                functions.countDistinct("geoid_2020").alias(
                    f"{count_prefix}_query_tract_count"
                ),
            )
        )
    combined = outputs[0]
    for output in outputs[1:]:
        combined = combined.unionByName(output)
    return combined


def build_selection_coverage(
    eligible: Any,
    selected: Any,
    *,
    run_id: str,
    built_at_utc: str,
) -> Any:
    """Compare expanded selected-query coverage with the full eligible population."""

    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    eligible_counts = _dimension_counts(eligible, count_prefix="eligible")
    selected_counts = _dimension_counts(selected, count_prefix="selected")
    keys = ["horizon_years", "dimension_name", "dimension_value"]
    combined = eligible_counts.join(selected_counts, keys, "left").fillna(
        0,
        subset=["selected_query_count", "selected_query_tract_count"],
    )
    dimension_window = Window.partitionBy("horizon_years", "dimension_name")
    return (
        combined.withColumn(
            "eligible_query_share",
            functions.col("eligible_query_count")
            / functions.sum("eligible_query_count").over(dimension_window),
        )
        .withColumn(
            "selected_query_share",
            functions.col("selected_query_count")
            / functions.sum("selected_query_count").over(dimension_window),
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
        .withColumn(
            "analogue_selection_schema_version",
            functions.lit(ANALOGUE_SELECTION_SCHEMA_VERSION),
        )
        .withColumn("analogue_selection_run_id", functions.lit(run_id))
        .withColumn(
            "analogue_selection_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
    )


def _add_selection_lineage(
    frame: Any,
    *,
    run_id: str,
    built_at_utc: str,
    queries_per_group: int,
) -> Any:
    """Attach the expanded-selection contract and run lineage to a published frame."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        frame.withColumn(
            "analogue_selection_schema_version",
            functions.lit(ANALOGUE_SELECTION_SCHEMA_VERSION),
        )
        .withColumn("analogue_selection_run_id", functions.lit(run_id))
        .withColumn(
            "analogue_selection_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
        .withColumn(
            "selection_queries_per_group",
            functions.lit(queries_per_group),
        )
    )


def build_analogue_selection_run(
    modeling_panel: Any,
    forecast_predictions: Any,
    *,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS,
    queries_per_group: int = DEFAULT_SELECTION_QUERIES_PER_GROUP,
    top_k: int = 10,
    pca_components: int = DEFAULT_PCA_COMPONENTS,
    comparator_models: tuple[str, ...] = DEFAULT_COMPARATOR_MODELS,
    run_id: str | None = None,
    built_at_utc: str | None = None,
) -> AnalogueSelectionRun:
    """Run expanded validation with distinct physical candidates and coverage evidence."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    validate_selection_settings(queries_per_group=queries_per_group, top_k=top_k)
    selection_panel = _add_query_dimensions(modeling_panel)
    historical = build_historical_analogue_run(
        selection_panel,
        forecast_predictions,
        horizons=horizons,
        queries_per_group=queries_per_group,
        top_k=top_k,
        pca_components=pca_components,
        unique_candidate_tract=True,
        required_query_coverage_columns=REQUIRED_SELECTION_COVERAGE_COLUMNS,
        comparator_models=comparator_models,
        run_id=run_id,
        built_at_utc=built_at_utc,
    )
    eligible = eligible_selection_queries(
        selection_panel,
        forecast_predictions,
        horizons=horizons,
        comparator_models=comparator_models,
    )
    selected = _selected_query_dimensions(eligible, historical.predictions)
    query_lookup = selected.select(
        functions.col("geoid_2020").alias("query_geoid_2020"),
        functions.col("forecast_origin_year").alias("query_origin_year"),
        "horizon_years",
        "query_housing_composition_band",
        "query_community_size_band",
        "query_acs_uncertainty_band",
    )
    predictions = (
        historical.predictions.join(
            query_lookup,
            ["query_geoid_2020", "query_origin_year", "horizon_years"],
            "inner",
        )
        .withColumn("unique_candidate_tract", functions.lit(True))
    )
    scorecard = build_historical_analogue_scorecard(
        predictions,
        additional_slices=SELECTION_SCORECARD_SLICES,
    )
    coverage = build_selection_coverage(
        eligible,
        selected,
        run_id=historical.run_id,
        built_at_utc=historical.built_at_utc,
    )
    return AnalogueSelectionRun(
        run_id=historical.run_id,
        built_at_utc=historical.built_at_utc,
        matches=_add_selection_lineage(
            historical.matches,
            run_id=historical.run_id,
            built_at_utc=historical.built_at_utc,
            queries_per_group=queries_per_group,
        ),
        predictions=_add_selection_lineage(
            predictions,
            run_id=historical.run_id,
            built_at_utc=historical.built_at_utc,
            queries_per_group=queries_per_group,
        ),
        summary=_add_selection_lineage(
            historical.summary,
            run_id=historical.run_id,
            built_at_utc=historical.built_at_utc,
            queries_per_group=queries_per_group,
        ),
        scorecard=_add_selection_lineage(
            scorecard,
            run_id=historical.run_id,
            built_at_utc=historical.built_at_utc,
            queries_per_group=queries_per_group,
        ),
        coverage=coverage.withColumn(
            "selection_queries_per_group",
            functions.lit(queries_per_group),
        ),
    )

"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Deterministic explanations and aligned outcome paths for current historical analogues.
"""

from __future__ import annotations

from typing import Any

from neighborhood_twin.analogue_serving import (
    ANALOGUE_SERVING_EXPLANATION_TABLE,
    ANALOGUE_SERVING_TRAJECTORY_TABLE,
    AnalogueServingRelease,
    add_serving_lineage,
)
from neighborhood_twin.historical_analogues import (
    ANALOGUE_FEATURE_COLUMNS,
    ANALOGUE_FEATURE_FAMILIES,
)

ANALOGUE_FAMILY_DISPLAY_NAMES = {
    "community_scale": "Community scale",
    "occupancy_tenure": "Occupancy and tenure",
    "housing_structure": "Housing structure",
    "affordability": "Affordability",
    "market_trajectory": "Recent housing-market trajectory",
}

ANALOGUE_FEATURE_DISPLAY_NAMES = {
    "analogue_log_population": "Population size",
    "analogue_log_housing_units": "Housing-unit count",
    "analogue_occupancy_rate": "Housing occupancy rate",
    "analogue_owner_occupancy_rate": "Owner-occupancy rate",
    "analogue_single_family_share": "Single-family housing share",
    "analogue_multifamily_share": "Multifamily housing share",
    "analogue_mobile_home_share": "Mobile-home share",
    "analogue_home_value_to_income": "Home-value-to-income ratio",
    "analogue_annual_rent_to_income": "Annual-rent-to-income ratio",
    "analogue_recent_three_year_hpi_change": "Recent three-year HPI change",
    "analogue_recent_five_year_hpi_volatility": "Recent five-year HPI volatility",
    "analogue_tract_minus_state_change": "Tract HPI change relative to its state",
}

EXPLANATION_SCOPE_NOTE = (
    "Similarities and differences describe the model's standardized input features; they do not "
    "show causal drivers or whether one community will follow another."
)
TRAJECTORY_SCOPE_NOTE = (
    "This is the observed FHFA single-family HPI path after a historical match, not a forecast "
    "or causal scenario for the selected community."
)


def validate_explanation_registry() -> None:
    """Require complete, non-overlapping feature and family labels."""

    family_features = tuple(
        feature
        for features in ANALOGUE_FEATURE_FAMILIES.values()
        for feature in features
    )
    if family_features != ANALOGUE_FEATURE_COLUMNS:
        raise ValueError("Feature-family order must match the governed analogue feature order")
    if set(ANALOGUE_FAMILY_DISPLAY_NAMES) != set(ANALOGUE_FEATURE_FAMILIES):
        raise ValueError("Every analogue family must have one display name")
    if set(ANALOGUE_FEATURE_DISPLAY_NAMES) != set(ANALOGUE_FEATURE_COLUMNS):
        raise ValueError("Every analogue feature must have one display name")


def _display_name_map(mapping: dict[str, str]) -> Any:
    """Create a Spark map expression from a small deterministic label registry."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    entries: list[Any] = []
    for key, value in mapping.items():
        entries.extend((functions.lit(key), functions.lit(value)))
    return functions.create_map(*entries)


def _feature_value(array_column: str, position: Any) -> Any:
    """Read a one-based dynamic position from a Spark feature array."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return functions.element_at(functions.col(array_column), position.cast("int"))


def build_serving_explanation_frame(
    matches: Any,
    represented: Any,
    release: AnalogueServingRelease,
) -> Any:
    """Explain each match using all family gaps and its closest and furthest features."""

    validate_explanation_registry()
    from pyspark.ml.functions import vector_to_array  # type: ignore[import-not-found]
    from pyspark.sql import functions  # type: ignore[import-not-found]

    missing_representation_columns = {
        "_analogue_unscaled_vector",
        "_analogue_standardized_vector",
        *ANALOGUE_FEATURE_COLUMNS,
    } - set(represented.columns)
    if missing_representation_columns:
        raise ValueError(
            "Represented analogue data is missing: "
            + ", ".join(sorted(missing_representation_columns))
        )

    imputed_count = sum(
        (
            functions.when(functions.col(feature).isNull(), functions.lit(1)).otherwise(
                functions.lit(0)
            )
            for feature in ANALOGUE_FEATURE_COLUMNS
        ),
        functions.lit(0),
    )
    features = represented.select(
        "geoid_2020",
        "forecast_origin_year",
        "horizon_years",
        vector_to_array("_analogue_unscaled_vector").alias("feature_values"),
        vector_to_array("_analogue_standardized_vector").alias(
            "standardized_feature_values"
        ),
        imputed_count.alias("imputed_feature_count"),
    )
    query_features = features.select(
        functions.col("geoid_2020").alias("query_geoid_2020"),
        functions.col("forecast_origin_year").alias("query_origin_year"),
        "horizon_years",
        functions.col("feature_values").alias("query_feature_values"),
        functions.col("standardized_feature_values").alias(
            "query_standardized_feature_values"
        ),
        functions.col("imputed_feature_count").alias("query_imputed_feature_count"),
    )
    candidate_features = features.select(
        functions.col("geoid_2020").alias("candidate_geoid_2020"),
        functions.col("forecast_origin_year").alias("candidate_origin_year"),
        "horizon_years",
        functions.col("feature_values").alias("candidate_feature_values"),
        functions.col("standardized_feature_values").alias(
            "candidate_standardized_feature_values"
        ),
        functions.col("imputed_feature_count").alias(
            "candidate_imputed_feature_count"
        ),
    )
    explanation = matches.join(
        query_features,
        ["query_geoid_2020", "query_origin_year", "horizon_years"],
        "inner",
    ).join(
        candidate_features,
        ["candidate_geoid_2020", "candidate_origin_year", "horizon_years"],
        "inner",
    )
    explanation = explanation.withColumn(
        "_feature_gaps",
        functions.zip_with(
            "query_standardized_feature_values",
            "candidate_standardized_feature_values",
            lambda query_value, candidate_value: functions.abs(query_value - candidate_value),
        ),
    ).withColumn(
        "_feature_order",
        functions.array(*[functions.lit(feature) for feature in ANALOGUE_FEATURE_COLUMNS]),
    )

    family_structs = []
    family_gap_columns = []
    for family, family_features in ANALOGUE_FEATURE_FAMILIES.items():
        indices = [ANALOGUE_FEATURE_COLUMNS.index(feature) for feature in family_features]
        gap = sum(
            (
                functions.element_at("_feature_gaps", functions.lit(index + 1))
                for index in indices
            ),
            functions.lit(0.0),
        ) / functions.lit(float(len(indices)))
        gap_column = f"{family}_mean_absolute_standardized_gap"
        explanation = explanation.withColumn(gap_column, gap)
        family_gap_columns.append(gap_column)
        family_structs.append(
            functions.struct(
                functions.col(gap_column).alias("gap"),
                functions.lit(family).alias("family"),
            )
        )
    explanation = explanation.withColumn(
        "_ranked_families", functions.array_sort(functions.array(*family_structs))
    )

    strongest_position = functions.expr(
        "cast(array_position(_feature_gaps, array_min(_feature_gaps)) as int)"
    )
    largest_position = functions.expr(
        "cast(array_position(_feature_gaps, array_max(_feature_gaps)) as int)"
    )
    strongest_feature = _feature_value("_feature_order", strongest_position)
    largest_feature = _feature_value("_feature_order", largest_position)
    feature_display_names = _display_name_map(ANALOGUE_FEATURE_DISPLAY_NAMES)
    family_display_names = _display_name_map(ANALOGUE_FAMILY_DISPLAY_NAMES)

    explanation = (
        explanation.withColumn(
            "strongest_shared_family", functions.element_at("_ranked_families", 1)["family"]
        )
        .withColumn(
            "strongest_shared_family_gap", functions.element_at("_ranked_families", 1)["gap"]
        )
        .withColumn(
            "second_shared_family", functions.element_at("_ranked_families", 2)["family"]
        )
        .withColumn(
            "second_shared_family_gap", functions.element_at("_ranked_families", 2)["gap"]
        )
        .withColumn(
            "largest_difference_family",
            functions.element_at("_ranked_families", -1)["family"],
        )
        .withColumn(
            "largest_difference_family_gap",
            functions.element_at("_ranked_families", -1)["gap"],
        )
        .withColumn(
            "second_difference_family",
            functions.element_at("_ranked_families", -2)["family"],
        )
        .withColumn(
            "second_difference_family_gap",
            functions.element_at("_ranked_families", -2)["gap"],
        )
        .withColumn("strongest_shared_feature", strongest_feature)
        .withColumn(
            "strongest_shared_feature_display_name",
            functions.element_at(feature_display_names, strongest_feature),
        )
        .withColumn(
            "strongest_shared_query_value",
            _feature_value("query_feature_values", strongest_position),
        )
        .withColumn(
            "strongest_shared_candidate_value",
            _feature_value("candidate_feature_values", strongest_position),
        )
        .withColumn(
            "strongest_shared_standardized_gap",
            _feature_value("_feature_gaps", strongest_position),
        )
        .withColumn("largest_difference_feature", largest_feature)
        .withColumn(
            "largest_difference_feature_display_name",
            functions.element_at(feature_display_names, largest_feature),
        )
        .withColumn(
            "largest_difference_query_value",
            _feature_value("query_feature_values", largest_position),
        )
        .withColumn(
            "largest_difference_candidate_value",
            _feature_value("candidate_feature_values", largest_position),
        )
        .withColumn(
            "largest_difference_standardized_gap",
            _feature_value("_feature_gaps", largest_position),
        )
        .withColumn(
            "strongest_shared_family_display_name",
            functions.element_at(family_display_names, functions.col("strongest_shared_family")),
        )
        .withColumn(
            "second_shared_family_display_name",
            functions.element_at(family_display_names, functions.col("second_shared_family")),
        )
        .withColumn(
            "largest_difference_family_display_name",
            functions.element_at(
                family_display_names, functions.col("largest_difference_family")
            ),
        )
        .withColumn(
            "second_difference_family_display_name",
            functions.element_at(
                family_display_names, functions.col("second_difference_family")
            ),
        )
        .withColumn("explanation_scope_note", functions.lit(EXPLANATION_SCOPE_NOTE))
    )
    compact = explanation.select(
        "query_geoid_2020",
        "query_origin_year",
        "horizon_years",
        "candidate_geoid_2020",
        "candidate_origin_year",
        "match_rank",
        "similarity_distance",
        *family_gap_columns,
        "strongest_shared_family",
        "strongest_shared_family_display_name",
        "strongest_shared_family_gap",
        "second_shared_family",
        "second_shared_family_display_name",
        "second_shared_family_gap",
        "largest_difference_family",
        "largest_difference_family_display_name",
        "largest_difference_family_gap",
        "second_difference_family",
        "second_difference_family_display_name",
        "second_difference_family_gap",
        "strongest_shared_feature",
        "strongest_shared_feature_display_name",
        "strongest_shared_query_value",
        "strongest_shared_candidate_value",
        "strongest_shared_standardized_gap",
        "largest_difference_feature",
        "largest_difference_feature_display_name",
        "largest_difference_query_value",
        "largest_difference_candidate_value",
        "largest_difference_standardized_gap",
        "query_imputed_feature_count",
        "candidate_imputed_feature_count",
        "explanation_scope_note",
    )
    return add_serving_lineage(compact, release)


def build_serving_trajectory_frame(
    matches: Any,
    historical_targets: Any,
    release: AnalogueServingRelease,
) -> Any:
    """Align each matched tract's observed annual FHFA path from origin through horizon."""

    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    required_targets = {
        "geoid_2020",
        "forecast_origin_year",
        "horizon_years",
        "target_end_year",
        "origin_hpi",
        "target_end_hpi",
        "target_is_observed",
        "origin_source_snapshot_id",
        "target_end_source_snapshot_id",
    }
    missing_targets = required_targets - set(historical_targets.columns)
    if missing_targets:
        raise ValueError(
            "Historical targets are missing: " + ", ".join(sorted(missing_targets))
        )
    one_year = historical_targets.where(functions.col("horizon_years") == 1)
    base = one_year.select(
        functions.col("geoid_2020").alias("candidate_geoid_2020"),
        functions.col("forecast_origin_year").alias("candidate_origin_year"),
        functions.col("origin_hpi").alias("trajectory_origin_hpi"),
        functions.col("origin_source_snapshot_id").alias("trajectory_origin_snapshot_id"),
    )
    observations = one_year.where(functions.col("target_is_observed")).select(
        functions.col("geoid_2020").alias("_observation_geoid"),
        functions.col("target_end_year").alias("_step_observation_year"),
        functions.col("target_end_hpi").alias("_observed_hpi"),
        functions.col("target_end_source_snapshot_id").alias("_observation_snapshot_id"),
    )
    expanded = (
        matches.join(base, ["candidate_geoid_2020", "candidate_origin_year"], "inner")
        .withColumn(
            "trajectory_year_offset",
            functions.explode(functions.sequence(functions.lit(0), "horizon_years")),
        )
        .withColumn(
            "trajectory_observation_year",
            functions.col("candidate_origin_year")
            + functions.col("trajectory_year_offset"),
        )
    )
    joined = expanded.join(
        observations,
        (functions.col("candidate_geoid_2020") == functions.col("_observation_geoid"))
        & (
            functions.col("trajectory_observation_year")
            == functions.col("_step_observation_year")
        )
        & (functions.col("trajectory_year_offset") > 0),
        "left",
    )
    trajectory_hpi = functions.when(
        functions.col("trajectory_year_offset") == 0,
        functions.col("trajectory_origin_hpi"),
    ).otherwise(functions.col("_observed_hpi"))
    trajectory_snapshot = functions.when(
        functions.col("trajectory_year_offset") == 0,
        functions.col("trajectory_origin_snapshot_id"),
    ).otherwise(functions.col("_observation_snapshot_id"))
    with_values = (
        joined.withColumn("trajectory_hpi", trajectory_hpi)
        .withColumn("trajectory_source_snapshot_id", trajectory_snapshot)
        .withColumn("trajectory_observed", functions.col("trajectory_hpi").isNotNull())
        .withColumn(
            "trajectory_cumulative_log_change",
            functions.when(
                functions.col("trajectory_observed"),
                functions.log("trajectory_hpi") - functions.log("trajectory_origin_hpi"),
            ),
        )
        .withColumn(
            "trajectory_cumulative_change_pct",
            functions.when(
                functions.col("trajectory_observed"),
                (functions.col("trajectory_hpi") / functions.col("trajectory_origin_hpi") - 1)
                * 100.0,
            ),
        )
        .withColumn(
            "is_horizon_endpoint",
            functions.col("trajectory_year_offset") == functions.col("horizon_years"),
        )
    )
    path_window = Window.partitionBy(
        "query_geoid_2020",
        "query_origin_year",
        "horizon_years",
        "candidate_geoid_2020",
        "candidate_origin_year",
        "match_rank",
    )
    compact = (
        with_values.withColumn(
            "trajectory_path_complete",
            functions.min(functions.col("trajectory_observed").cast("int")).over(path_window)
            == 1,
        )
        .withColumn("trajectory_role", functions.lit("historical_observed_outcome_path"))
        .withColumn("trajectory_scope_note", functions.lit(TRAJECTORY_SCOPE_NOTE))
        .select(
            "query_geoid_2020",
            "query_origin_year",
            "horizon_years",
            "candidate_geoid_2020",
            "candidate_origin_year",
            "match_rank",
            "candidate_state_abbreviation",
            "candidate_county_name",
            "candidate_tract_name",
            "trajectory_year_offset",
            "trajectory_observation_year",
            "trajectory_hpi",
            "trajectory_cumulative_log_change",
            "trajectory_cumulative_change_pct",
            "trajectory_observed",
            "trajectory_path_complete",
            "is_horizon_endpoint",
            "trajectory_source_snapshot_id",
            "trajectory_role",
            "trajectory_scope_note",
        )
    )
    return add_serving_lineage(compact, release)


def validate_serving_enrichment(
    matches: Any,
    explanations: Any,
    trajectories: Any,
    release: AnalogueServingRelease,
) -> dict[str, int]:
    """Reconcile enrichment keys, rankings, annual paths, endpoints, and release lineage."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    for name, frame in (
        (ANALOGUE_SERVING_EXPLANATION_TABLE, explanations),
        (ANALOGUE_SERVING_TRAJECTORY_TABLE, trajectories),
    ):
        release_ids = {row[0] for row in frame.select("serving_release_id").distinct().collect()}
        if release_ids != {release.release_id}:
            raise RuntimeError(f"{name} does not contain exactly the requested release ID")

    match_keys = [
        "query_geoid_2020",
        "query_origin_year",
        "horizon_years",
        "candidate_geoid_2020",
        "candidate_origin_year",
        "match_rank",
    ]
    if explanations.groupBy(*match_keys).count().where(
        functions.col("count") != 1
    ).limit(1).count():
        raise RuntimeError("Analogue explanations contain duplicate match keys")
    if matches.select(*match_keys).join(
        explanations.select(*match_keys), match_keys, "left_anti"
    ).limit(1).count() or explanations.select(*match_keys).join(
        matches.select(*match_keys), match_keys, "left_anti"
    ).limit(1).count():
        raise RuntimeError("Analogue explanation keys do not reconcile to serving matches")

    family_names = tuple(ANALOGUE_FEATURE_FAMILIES)
    invalid_explanation = explanations.where(
        ~functions.col("strongest_shared_family").isin(*family_names)
        | ~functions.col("second_shared_family").isin(*family_names)
        | ~functions.col("largest_difference_family").isin(*family_names)
        | ~functions.col("second_difference_family").isin(*family_names)
        | (functions.col("strongest_shared_family_gap") < 0)
        | (
            functions.col("strongest_shared_family_gap")
            > functions.col("second_shared_family_gap")
        )
        | (
            functions.col("largest_difference_family_gap")
            < functions.col("second_difference_family_gap")
        )
        | (functions.col("strongest_shared_standardized_gap") < 0)
        | (functions.col("largest_difference_standardized_gap") < 0)
        | (functions.col("query_imputed_feature_count") < 0)
        | (functions.col("query_imputed_feature_count") > len(ANALOGUE_FEATURE_COLUMNS))
        | (functions.col("candidate_imputed_feature_count") < 0)
        | (functions.col("candidate_imputed_feature_count") > len(ANALOGUE_FEATURE_COLUMNS))
    )
    if invalid_explanation.limit(1).count():
        raise RuntimeError("Analogue explanations contain invalid ranks, gaps, or feature counts")

    trajectory_keys = [*match_keys, "trajectory_year_offset"]
    if trajectories.groupBy(*trajectory_keys).count().where(
        functions.col("count") != 1
    ).limit(1).count():
        raise RuntimeError("Analogue trajectories contain duplicate match-offset keys")
    path_groups = trajectories.groupBy(*match_keys).agg(
        functions.count(functions.lit(1)).alias("path_row_count"),
        functions.min("trajectory_year_offset").alias("minimum_offset"),
        functions.max("trajectory_year_offset").alias("maximum_offset"),
        functions.sum(functions.col("is_horizon_endpoint").cast("int")).alias(
            "endpoint_count"
        ),
    )
    if path_groups.where(
        (functions.col("path_row_count") != functions.col("horizon_years") + 1)
        | (functions.col("minimum_offset") != 0)
        | (functions.col("maximum_offset") != functions.col("horizon_years"))
        | (functions.col("endpoint_count") != 1)
    ).limit(1).count():
        raise RuntimeError("Analogue trajectories do not contain one complete offset sequence")
    if matches.select(*match_keys).join(
        path_groups.select(*match_keys), match_keys, "left_anti"
    ).limit(1).count() or path_groups.select(*match_keys).join(
        matches.select(*match_keys), match_keys, "left_anti"
    ).limit(1).count():
        raise RuntimeError("Analogue trajectory keys do not reconcile to serving matches")

    endpoints = trajectories.where(functions.col("is_horizon_endpoint")).select(
        *match_keys,
        "trajectory_observed",
        "trajectory_cumulative_log_change",
    )
    endpoint_check = matches.select(
        *match_keys,
        "candidate_target_cumulative_log_change",
    ).join(endpoints, match_keys, "inner")
    if endpoint_check.where(
        ~functions.col("trajectory_observed")
        | (
            functions.abs(
                functions.col("trajectory_cumulative_log_change")
                - functions.col("candidate_target_cumulative_log_change")
            )
            > 1e-9
        )
    ).limit(1).count():
        raise RuntimeError("Analogue trajectory endpoints do not reconcile to match outcomes")

    row_counts = {
        ANALOGUE_SERVING_EXPLANATION_TABLE: explanations.count(),
        ANALOGUE_SERVING_TRAJECTORY_TABLE: trajectories.count(),
    }
    match_count = matches.count()
    expected_trajectory_count = matches.agg(
        functions.sum(functions.col("horizon_years") + 1)
    ).first()[0]
    if row_counts[ANALOGUE_SERVING_EXPLANATION_TABLE] != match_count:
        raise RuntimeError("Serving explanation and match row counts do not reconcile")
    if row_counts[ANALOGUE_SERVING_TRAJECTORY_TABLE] != expected_trajectory_count:
        raise RuntimeError("Serving trajectory row count does not match declared horizons")
    return row_counts

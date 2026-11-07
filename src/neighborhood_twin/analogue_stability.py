"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Spark workflow for bounded historical-analogue perturbation and stability evaluation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from neighborhood_twin.analogue_audit import (
    ANALOGUE_AUDIT_SCHEMA_VERSION,
    AUDIT_QUERY_KEYS,
    AnalogueAuditVariant,
    audit_feature_multipliers,
    build_baseline_match_audit,
    build_case_review,
    default_audit_variants,
    validate_audit_match_columns,
    weighted_distance_boundary_multiplier,
)
from neighborhood_twin.historical_analogues import (
    add_weighted_analogue_vector,
    fit_analogue_pca,
    fit_analogue_preprocessing,
    rank_analogue_matches,
)


@dataclass(frozen=True)
class AnalogueStabilityRun:
    """Versioned audit matches, per-query stability, baseline audit, and case review."""

    run_id: str
    built_at_utc: str
    source_historical_analogue_run_id: str
    audit_matches: Any
    stability_summary: Any
    baseline_audit: Any
    case_review: Any


def validate_stability_settings(*, top_k: int, shortlist_k: int) -> None:
    """Validate bounded retrieval settings before Spark work begins."""

    if top_k < 3:
        raise ValueError("top_k must be at least three for top-three stability")
    if shortlist_k < top_k:
        raise ValueError("shortlist_k must be greater than or equal to top_k")


def _source_run_id(matches: Any) -> str:
    """Return the one source job-502 run ID required for a stability build."""

    if "historical_analogue_run_id" not in matches.columns:
        raise ValueError("Historical analogue matches are missing their source run ID")
    run_ids = [
        str(row[0])
        for row in matches.select("historical_analogue_run_id").distinct().collect()
    ]
    if len(run_ids) != 1:
        raise ValueError("Stability evaluation requires exactly one historical analogue run ID")
    return run_ids[0]


def _queries_from_baseline(representation: Any, baseline_matches: Any) -> Any:
    """Select the exact job-502 query keys from a transformed horizon frame."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    query_keys = baseline_matches.select(
        functions.col("query_geoid_2020").alias("geoid_2020"),
        functions.col("query_origin_year").alias("forecast_origin_year"),
        "horizon_years",
    ).distinct()
    return representation.join(
        query_keys,
        ["geoid_2020", "forecast_origin_year", "horizon_years"],
        "inner",
    )


def _shortlist_keys(weighted_shortlist: Any, pca_shortlist: Any) -> Any:
    """Return the per-query union of exact weighted and PCA baseline candidates."""

    columns = [
        *AUDIT_QUERY_KEYS,
        "candidate_geoid_2020",
        "candidate_origin_year",
    ]
    return weighted_shortlist.select(*columns).unionByName(
        pca_shortlist.select(*columns)
    ).distinct()


def _shortlist_boundaries(
    weighted_shortlist: Any,
    pca_shortlist: Any,
    *,
    shortlist_k: int,
) -> Any:
    """Record the exact baseline boundary used to certify bounded reranking."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    combined = weighted_shortlist.select(
        *AUDIT_QUERY_KEYS,
        "representation_name",
        "similarity_distance",
    ).unionByName(
        pca_shortlist.select(
            *AUDIT_QUERY_KEYS,
            "representation_name",
            "similarity_distance",
        )
    )
    return combined.groupBy(*AUDIT_QUERY_KEYS, "representation_name").agg(
        functions.count(functions.lit(1)).alias("baseline_shortlist_count"),
        functions.max("similarity_distance").alias(
            "baseline_shortlist_boundary_distance"
        ),
    ).withColumn("candidate_shortlist_k", functions.lit(shortlist_k))


def _rank_shortlist_matches(
    representation: Any,
    queries: Any,
    shortlist_keys: Any,
    *,
    representation_name: str,
    vector_column: str,
    top_k: int,
    unique_candidate_tract: bool,
) -> Any:
    """Rerank one representation inside the exact union baseline shortlist."""

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
    candidate = representation.select(
        functions.col("geoid_2020").alias("candidate_geoid_2020"),
        functions.col("forecast_origin_year").alias("candidate_origin_year"),
        "horizon_years",
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
        shortlist_keys.join(query, list(AUDIT_QUERY_KEYS), "inner")
        .join(
            candidate,
            ["candidate_geoid_2020", "candidate_origin_year", "horizon_years"],
            "inner",
        )
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
        candidate_window = Window.partitionBy(
            *AUDIT_QUERY_KEYS,
            "representation_name",
            "candidate_geoid_2020",
        ).orderBy(
            "similarity_distance",
            functions.col("candidate_origin_year").desc(),
        )
        pairs = (
            pairs.withColumn("_candidate_rank", functions.row_number().over(candidate_window))
            .where(functions.col("_candidate_rank") == 1)
            .drop("_candidate_rank")
        )
    ranking = Window.partitionBy(*AUDIT_QUERY_KEYS, "representation_name").orderBy(
        "similarity_distance",
        functions.col("candidate_origin_year").desc(),
        "candidate_geoid_2020",
    )
    return (
        pairs.withColumn("match_rank", functions.row_number().over(ranking))
        .where(functions.col("match_rank") <= top_k)
        .drop("_query_vector", "_candidate_vector")
    )


def _annotate_variant(
    matches: Any,
    variant: AnalogueAuditVariant,
    *,
    shortlist_boundaries: Any,
    top_k: int,
    shortlist_k: int,
    source_run_id: str,
    run_id: str,
    built_at_utc: str,
) -> Any:
    """Attach the variant, query-level exactness evidence, and source lineage."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    annotated = matches.withColumn("variant_name", functions.lit(variant.variant_name))
    top_k_boundary = annotated.groupBy(*AUDIT_QUERY_KEYS).agg(
        functions.count(functions.lit(1)).alias("variant_match_count"),
        functions.max("similarity_distance").alias("variant_top_k_boundary_distance"),
    )
    if variant.perturbation_kind in {"small_weight_change", "candidate_uniqueness"}:
        if variant.representation_name == "weighted_standardized":
            boundary_multiplier = weighted_distance_boundary_multiplier(
                variant.family_factor_map()
            )
        else:
            boundary_multiplier = 1.0
    else:
        boundary_multiplier = None

    exactness = (
        top_k_boundary.join(
            shortlist_boundaries.where(
                functions.col("representation_name") == variant.representation_name
            ).drop("representation_name"),
            list(AUDIT_QUERY_KEYS),
            "inner",
        )
        .withColumn(
            "excluded_candidate_distance_lower_bound",
            functions.when(
                functions.lit(boundary_multiplier is not None),
                functions.col("baseline_shortlist_boundary_distance")
                * functions.lit(boundary_multiplier),
            ),
        )
        .withColumn(
            "exactness_certified",
            functions.when(
                functions.lit(variant.perturbation_kind == "baseline"),
                functions.lit(True),
            )
            .when(
                functions.col("baseline_shortlist_count") < functions.lit(shortlist_k),
                functions.lit(True),
            )
            .when(
                functions.lit(
                    variant.perturbation_kind
                    in {"small_weight_change", "candidate_uniqueness"}
                )
                & (functions.col("variant_match_count") == functions.lit(top_k))
                & (
                    functions.col("variant_top_k_boundary_distance")
                    < functions.col("excluded_candidate_distance_lower_bound")
                ),
                functions.lit(True),
            )
            .otherwise(functions.lit(False)),
        )
        .withColumn(
            "exactness_status",
            functions.when(
                functions.lit(variant.perturbation_kind == "baseline"),
                functions.lit("exact_national_baseline"),
            )
            .when(
                functions.col("baseline_shortlist_count") < functions.lit(shortlist_k),
                functions.lit("exact_exhaustive_candidate_set"),
            )
            .when(
                functions.col("exactness_certified"),
                functions.lit("exact_boundary_certified"),
            )
            .when(
                functions.lit(
                    variant.perturbation_kind
                    in {"small_weight_change", "candidate_uniqueness"}
                ),
                functions.lit("shortlist_based_boundary_not_certified"),
            )
            .otherwise(functions.lit("shortlist_based_stress_test")),
        )
    )
    return (
        annotated.join(exactness, list(AUDIT_QUERY_KEYS), "inner")
        .withColumn("perturbation_kind", functions.lit(variant.perturbation_kind))
        .withColumn("perturbed_family", functions.lit(variant.perturbed_family))
        .withColumn("pca_components", functions.lit(variant.pca_components).cast("int"))
        .withColumn(
            "unique_candidate_tract", functions.lit(variant.unique_candidate_tract)
        )
        .withColumn(
            "family_factors_json",
            functions.lit(json.dumps(variant.family_factor_map(), sort_keys=True)),
        )
        .withColumn("source_historical_analogue_run_id", functions.lit(source_run_id))
        .withColumn("analogue_audit_schema_version", functions.lit(ANALOGUE_AUDIT_SCHEMA_VERSION))
        .withColumn("analogue_audit_run_id", functions.lit(run_id))
        .withColumn(
            "analogue_audit_built_at_utc",
            functions.to_timestamp(functions.lit(built_at_utc)),
        )
    )


def build_stability_summary(audit_matches: Any, *, top_k: int) -> Any:
    """Compare every variant with its representation baseline on identical queries."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    variant_columns = (
        "variant_name",
        "representation_name",
        "perturbation_kind",
        "perturbed_family",
        "pca_components",
        "unique_candidate_tract",
        "candidate_shortlist_k",
        "exactness_status",
        "source_historical_analogue_run_id",
        "analogue_audit_schema_version",
        "analogue_audit_run_id",
        "analogue_audit_built_at_utc",
    )
    comparison = audit_matches.withColumn(
        "reference_variant_name",
        functions.when(
            functions.col("representation_name") == "pca",
            functions.lit("baseline_pca_k6"),
        ).otherwise(functions.lit("baseline_weighted_standardized")),
    )
    reference = audit_matches.where(functions.col("perturbation_kind") == "baseline").select(
        *AUDIT_QUERY_KEYS,
        functions.col("variant_name").alias("reference_variant_name"),
        "candidate_geoid_2020",
        "candidate_origin_year",
        functions.col("match_rank").alias("reference_match_rank"),
    )
    overlap_keys = [
        *AUDIT_QUERY_KEYS,
        "reference_variant_name",
        "candidate_geoid_2020",
        "candidate_origin_year",
    ]
    overlap = (
        comparison.join(reference, overlap_keys, "inner")
        .groupBy(
            *AUDIT_QUERY_KEYS,
            "variant_name",
            "reference_variant_name",
        )
        .agg(
            functions.count(functions.lit(1)).alias("top_k_overlap_count"),
            functions.sum(
                functions.when(
                    (functions.col("match_rank") <= 3)
                    & (functions.col("reference_match_rank") <= 3),
                    1,
                ).otherwise(0)
            ).alias("top_three_retention_count"),
            functions.avg(
                functions.abs(
                    functions.col("match_rank") - functions.col("reference_match_rank")
                )
            ).alias("mean_shared_rank_displacement"),
        )
    )
    inverse_distance_weight = 1.0 / (functions.col("similarity_distance") + 1e-9)
    estimates = audit_matches.groupBy(
        *AUDIT_QUERY_KEYS,
        *variant_columns,
        "query_target_cumulative_log_change",
        "query_region_name",
        "query_geographic_role",
        "query_modeling_cohort",
    ).agg(
        functions.count(functions.lit(1)).alias("match_count"),
        functions.countDistinct("candidate_geoid_2020").alias(
            "distinct_candidate_tract_count"
        ),
        functions.avg("candidate_age_years").alias("mean_candidate_age_years"),
        functions.avg(
            functions.when(
                functions.col("query_state_abbreviation")
                != functions.col("candidate_state_abbreviation"),
                1.0,
            ).otherwise(0.0)
        ).alias("cross_state_match_share"),
        functions.percentile_approx(
            "candidate_target_cumulative_log_change", 0.5, 10000
        ).alias("analogue_median_log_change"),
        (
            functions.sum(
                functions.col("candidate_target_cumulative_log_change")
                * inverse_distance_weight
            )
            / functions.sum(inverse_distance_weight)
        ).alias("analogue_inverse_distance_log_change"),
    )
    estimates = (
        estimates.withColumn(
            "median_absolute_error_log_change",
            functions.abs(
                functions.col("query_target_cumulative_log_change")
                - functions.col("analogue_median_log_change")
            ),
        )
        .withColumn(
            "inverse_distance_absolute_error_log_change",
            functions.abs(
                functions.col("query_target_cumulative_log_change")
                - functions.col("analogue_inverse_distance_log_change")
            ),
        )
        .withColumn(
            "reference_variant_name",
            functions.when(
                functions.col("representation_name") == "pca",
                functions.lit("baseline_pca_k6"),
            ).otherwise(functions.lit("baseline_weighted_standardized")),
        )
    )
    reference_estimates = estimates.where(
        functions.col("perturbation_kind") == "baseline"
    ).select(
        *AUDIT_QUERY_KEYS,
        functions.col("variant_name").alias("reference_variant_name"),
        functions.col("analogue_median_log_change").alias(
            "reference_analogue_median_log_change"
        ),
        functions.col("analogue_inverse_distance_log_change").alias(
            "reference_analogue_inverse_distance_log_change"
        ),
        functions.col("median_absolute_error_log_change").alias(
            "reference_median_absolute_error_log_change"
        ),
        functions.col("inverse_distance_absolute_error_log_change").alias(
            "reference_inverse_distance_absolute_error_log_change"
        ),
    )
    summary = estimates.join(
        reference_estimates,
        [*AUDIT_QUERY_KEYS, "reference_variant_name"],
        "inner",
    ).join(
        overlap,
        [
            *AUDIT_QUERY_KEYS,
            "variant_name",
            "reference_variant_name",
        ],
        "inner",
    )
    return (
        summary.withColumn(
            "top_k_overlap_share", functions.col("top_k_overlap_count") / functions.lit(top_k)
        )
        .withColumn(
            "top_k_jaccard_similarity",
            functions.col("top_k_overlap_count")
            / (functions.lit(2 * top_k) - functions.col("top_k_overlap_count")),
        )
        .withColumn(
            "top_three_retention_share",
            functions.col("top_three_retention_count") / functions.lit(3.0),
        )
        .withColumn(
            "stability_band",
            functions.when(functions.col("top_k_overlap_share") >= 0.7, "high")
            .when(functions.col("top_k_overlap_share") >= 0.5, "moderate")
            .otherwise("low"),
        )
        .withColumn(
            "median_estimate_change_log_change",
            functions.col("analogue_median_log_change")
            - functions.col("reference_analogue_median_log_change"),
        )
        .withColumn(
            "inverse_distance_estimate_change_log_change",
            functions.col("analogue_inverse_distance_log_change")
            - functions.col("reference_analogue_inverse_distance_log_change"),
        )
        .withColumn(
            "median_absolute_error_change_log_change",
            functions.col("median_absolute_error_log_change")
            - functions.col("reference_median_absolute_error_log_change"),
        )
        .withColumn(
            "inverse_distance_absolute_error_change_log_change",
            functions.col("inverse_distance_absolute_error_log_change")
            - functions.col("reference_inverse_distance_absolute_error_log_change"),
        )
    )


def build_analogue_stability_run(
    modeling_panel: Any,
    baseline_matches: Any,
    *,
    top_k: int = 10,
    shortlist_k: int = 1000,
    variants: tuple[AnalogueAuditVariant, ...] | None = None,
    run_id: str | None = None,
    built_at_utc: str | None = None,
) -> AnalogueStabilityRun:
    """Build exact baseline shortlists, bounded perturbations, stability, and case review."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    validate_stability_settings(top_k=top_k, shortlist_k=shortlist_k)
    validate_audit_match_columns(baseline_matches.columns)
    selected_variants = variants or default_audit_variants()
    if not selected_variants:
        raise ValueError("At least one audit variant is required")
    run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    built_at_utc = built_at_utc or datetime.now(UTC).isoformat()
    source_run_id = _source_run_id(baseline_matches)

    horizon_values = [
        int(row[0])
        for row in baseline_matches.select("horizon_years").distinct().collect()
    ]
    all_variant_matches = []
    for horizon in sorted(horizon_values):
        horizon_panel = modeling_panel.where(functions.col("horizon_years") == horizon)
        horizon_baseline = baseline_matches.where(functions.col("horizon_years") == horizon)
        standardized = fit_analogue_preprocessing(horizon_panel).cache()
        standardized.count()
        weighted_baseline = add_weighted_analogue_vector(standardized).cache()
        weighted_baseline.count()
        pca_baseline, _ = fit_analogue_pca(
            weighted_baseline,
            pca_components=6,
        )
        pca_baseline = pca_baseline.cache()
        pca_baseline.count()

        weighted_queries = _queries_from_baseline(weighted_baseline, horizon_baseline)
        pca_queries = _queries_from_baseline(pca_baseline, horizon_baseline)
        weighted_shortlist = rank_analogue_matches(
            weighted_baseline,
            weighted_queries,
            representation_name="weighted_standardized",
            vector_column="analogue_weighted_vector",
            top_k=shortlist_k,
        ).cache()
        weighted_shortlist.count()
        pca_shortlist = rank_analogue_matches(
            pca_baseline,
            pca_queries,
            representation_name="pca",
            vector_column="analogue_pca_vector",
            top_k=shortlist_k,
        ).cache()
        pca_shortlist.count()
        shortlist = _shortlist_keys(weighted_shortlist, pca_shortlist).cache()
        shortlist.count()
        shortlist_boundaries = _shortlist_boundaries(
            weighted_shortlist,
            pca_shortlist,
            shortlist_k=shortlist_k,
        ).cache()
        shortlist_boundaries.count()

        pca_frames: dict[int, Any] = {6: pca_baseline}
        for variant in selected_variants:
            if variant.representation_name == "weighted_standardized":
                if variant.perturbation_kind in {"baseline", "candidate_uniqueness"}:
                    representation = weighted_baseline
                    vector_column = "analogue_weighted_vector"
                else:
                    representation = add_weighted_analogue_vector(
                        standardized,
                        multipliers=audit_feature_multipliers(variant.family_factor_map()),
                        output_column="analogue_audit_vector",
                    )
                    vector_column = "analogue_audit_vector"
            elif variant.representation_name == "pca":
                component_count = variant.pca_components or 6
                if component_count not in pca_frames:
                    pca_frame, _ = fit_analogue_pca(
                        weighted_baseline,
                        pca_components=component_count,
                        output_column=f"analogue_pca_vector_{component_count}",
                    )
                    pca_frames[component_count] = pca_frame.cache()
                    pca_frames[component_count].count()
                representation = pca_frames[component_count]
                vector_column = (
                    "analogue_pca_vector"
                    if component_count == 6
                    else f"analogue_pca_vector_{component_count}"
                )
            else:
                raise ValueError(
                    f"Unsupported audit representation: {variant.representation_name}"
                )
            queries = _queries_from_baseline(representation, horizon_baseline)
            variant_matches = _rank_shortlist_matches(
                representation,
                queries,
                shortlist,
                representation_name=variant.representation_name,
                vector_column=vector_column,
                top_k=top_k,
                unique_candidate_tract=variant.unique_candidate_tract,
            )
            variant_matches = _annotate_variant(
                variant_matches,
                variant,
                shortlist_boundaries=shortlist_boundaries,
                top_k=top_k,
                shortlist_k=shortlist_k,
                source_run_id=source_run_id,
                run_id=run_id,
                built_at_utc=built_at_utc,
            ).cache()
            variant_matches.count()
            all_variant_matches.append(variant_matches)

    audit_matches = all_variant_matches[0]
    for variant_matches in all_variant_matches[1:]:
        audit_matches = audit_matches.unionByName(variant_matches)
    stability_summary = build_stability_summary(audit_matches, top_k=top_k)
    baseline_audit = build_baseline_match_audit(baseline_matches)
    case_review = build_case_review(baseline_matches, modeling_panel).withColumn(
        "analogue_audit_run_id", functions.lit(run_id)
    ).withColumn(
        "analogue_audit_built_at_utc",
        functions.to_timestamp(functions.lit(built_at_utc)),
    )
    return AnalogueStabilityRun(
        run_id,
        built_at_utc,
        source_run_id,
        audit_matches,
        stability_summary,
        baseline_audit,
        case_review,
    )

"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Configuration and deterministic metrics for historical-analogue review and stability testing.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Any

from neighborhood_twin.historical_analogues import (
    ANALOGUE_FEATURE_COLUMNS,
    ANALOGUE_FEATURE_FAMILIES,
    DEFAULT_PCA_COMPONENTS,
    fit_analogue_preprocessing,
)

ANALOGUE_AUDIT_SCHEMA_VERSION = "1.0.0"
ANALOGUE_AUDIT_MATCH_TABLE = "historical_analogue_audit_match"
ANALOGUE_CASE_REVIEW_TABLE = "historical_analogue_case_review"
ANALOGUE_STABILITY_SUMMARY_TABLE = "historical_analogue_stability_summary"

BASELINE_FAMILY_FACTORS = {family: 1.0 for family in ANALOGUE_FEATURE_FAMILIES}
DEFAULT_WEIGHT_PERTURBATION_FACTORS = (0.8, 1.2)
DEFAULT_PCA_COMPONENT_COUNTS = (5, DEFAULT_PCA_COMPONENTS, 7)

AUDIT_QUERY_KEYS = (
    "query_geoid_2020",
    "query_origin_year",
    "horizon_years",
)
AUDIT_MATCH_REQUIRED_COLUMNS = (
    *AUDIT_QUERY_KEYS,
    "query_region_name",
    "query_geographic_role",
    "query_modeling_cohort",
    "query_state_abbreviation",
    "query_county_name",
    "candidate_geoid_2020",
    "candidate_origin_year",
    "candidate_state_abbreviation",
    "candidate_county_name",
    "candidate_target_end_year",
    "candidate_target_cumulative_log_change",
    "candidate_age_years",
    "representation_name",
    "similarity_distance",
    "match_rank",
)


@dataclass(frozen=True)
class AnalogueAuditVariant:
    """One declared retrieval perturbation compared with the job-502 baseline."""

    variant_name: str
    representation_name: str
    perturbation_kind: str
    family_factors: tuple[tuple[str, float], ...]
    pca_components: int | None = None
    unique_candidate_tract: bool = False
    perturbed_family: str | None = None

    def family_factor_map(self) -> dict[str, float]:
        """Return the immutable family-factor pairs as a normal dictionary."""

        return dict(self.family_factors)


@dataclass(frozen=True)
class RankedOverlap:
    """Top-k stability metrics for one query under one comparison variant."""

    overlap_count: int
    overlap_share: float
    jaccard_similarity: float
    top_three_retention_count: int
    top_three_retention_share: float
    mean_shared_rank_displacement: float
    stability_band: str


def validate_audit_match_columns(available_columns: Iterable[str]) -> None:
    """Fail clearly when a match table cannot support the declared audit."""

    missing = sorted(set(AUDIT_MATCH_REQUIRED_COLUMNS) - set(available_columns))
    if missing:
        raise ValueError("Historical analogue audit input is missing: " + ", ".join(missing))


def validate_family_factors(family_factors: Mapping[str, float]) -> None:
    """Validate a complete, finite, nonnegative feature-family factor mapping."""

    expected = set(ANALOGUE_FEATURE_FAMILIES)
    actual = set(family_factors)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected: {', '.join(unexpected)}")
        raise ValueError(
            "Family factors do not match the feature registry (" + "; ".join(details) + ")"
        )
    invalid = sorted(
        family
        for family, value in family_factors.items()
        if not isfinite(float(value)) or float(value) < 0
    )
    if invalid:
        raise ValueError(
            "Family factors must be finite and nonnegative: " + ", ".join(invalid)
        )
    if sum(float(value) for value in family_factors.values()) <= 0:
        raise ValueError("At least one feature-family factor must be positive")


def normalized_family_weights(family_factors: Mapping[str, float]) -> dict[str, float]:
    """Normalize family factors so total squared-distance weight equals family count."""

    validate_family_factors(family_factors)
    factor_sum = sum(float(value) for value in family_factors.values())
    family_count = len(ANALOGUE_FEATURE_FAMILIES)
    return {
        family: float(family_factors[family]) * family_count / factor_sum
        for family in ANALOGUE_FEATURE_FAMILIES
    }


def audit_feature_weights(family_factors: Mapping[str, float]) -> tuple[float, ...]:
    """Return per-feature squared-distance weights for a declared family perturbation."""

    family_weights = normalized_family_weights(family_factors)
    feature_weights: dict[str, float] = {}
    for family, family_features in ANALOGUE_FEATURE_FAMILIES.items():
        weight = family_weights[family] / len(family_features)
        feature_weights.update({feature: weight for feature in family_features})
    return tuple(feature_weights[feature] for feature in ANALOGUE_FEATURE_COLUMNS)


def audit_feature_multipliers(family_factors: Mapping[str, float]) -> tuple[float, ...]:
    """Return vector multipliers whose squares equal the audit feature weights."""

    return tuple(sqrt(weight) for weight in audit_feature_weights(family_factors))


def weighted_distance_boundary_multiplier(
    family_factors: Mapping[str, float],
) -> float:
    """Return the lower-bound multiplier for an excluded baseline-distance candidate.

    If every candidate outside the exact baseline shortlist has baseline distance at least
    ``d``, its distance under the perturbed positive weights is at least this multiplier times
    ``d``. A zero multiplier is valid for an ablation but cannot certify a finite shortlist.
    """

    baseline_weights = audit_feature_weights(BASELINE_FAMILY_FACTORS)
    variant_weights = audit_feature_weights(family_factors)
    return sqrt(
        min(
            variant_weight / baseline_weight
            for variant_weight, baseline_weight in zip(
                variant_weights, baseline_weights, strict=True
            )
        )
    )


def _factor_pairs(family_factors: Mapping[str, float]) -> tuple[tuple[str, float], ...]:
    """Return family factors in the governed feature-family order."""

    validate_family_factors(family_factors)
    return tuple(
        (family, float(family_factors[family])) for family in ANALOGUE_FEATURE_FAMILIES
    )


def default_audit_variants() -> tuple[AnalogueAuditVariant, ...]:
    """Build the bounded baseline, weight, ablation, PCA, and candidate-policy variants."""

    variants = [
        AnalogueAuditVariant(
            "baseline_weighted_standardized",
            "weighted_standardized",
            "baseline",
            _factor_pairs(BASELINE_FAMILY_FACTORS),
        ),
        AnalogueAuditVariant(
            f"baseline_pca_k{DEFAULT_PCA_COMPONENTS}",
            "pca",
            "baseline",
            _factor_pairs(BASELINE_FAMILY_FACTORS),
            pca_components=DEFAULT_PCA_COMPONENTS,
        ),
    ]
    for family in ANALOGUE_FEATURE_FAMILIES:
        for factor in DEFAULT_WEIGHT_PERTURBATION_FACTORS:
            family_factors = {**BASELINE_FAMILY_FACTORS, family: factor}
            direction = "down" if factor < 1 else "up"
            variants.append(
                AnalogueAuditVariant(
                    f"weight_{family}_{direction}_{int(round(factor * 100))}pct",
                    "weighted_standardized",
                    "small_weight_change",
                    _factor_pairs(family_factors),
                    perturbed_family=family,
                )
            )
        ablation_factors = {**BASELINE_FAMILY_FACTORS, family: 0.0}
        variants.append(
            AnalogueAuditVariant(
                f"ablate_{family}",
                "weighted_standardized",
                "family_ablation",
                _factor_pairs(ablation_factors),
                perturbed_family=family,
            )
        )
    for component_count in DEFAULT_PCA_COMPONENT_COUNTS:
        if component_count == DEFAULT_PCA_COMPONENTS:
            continue
        variants.append(
            AnalogueAuditVariant(
                f"pca_k{component_count}",
                "pca",
                "pca_component_count",
                _factor_pairs(BASELINE_FAMILY_FACTORS),
                pca_components=component_count,
            )
        )
    variants.extend(
        [
            AnalogueAuditVariant(
                "weighted_standardized_unique_tract",
                "weighted_standardized",
                "candidate_uniqueness",
                _factor_pairs(BASELINE_FAMILY_FACTORS),
                unique_candidate_tract=True,
            ),
            AnalogueAuditVariant(
                f"pca_k{DEFAULT_PCA_COMPONENTS}_unique_tract",
                "pca",
                "candidate_uniqueness",
                _factor_pairs(BASELINE_FAMILY_FACTORS),
                pca_components=DEFAULT_PCA_COMPONENTS,
                unique_candidate_tract=True,
            ),
        ]
    )
    names = [variant.variant_name for variant in variants]
    if len(names) != len(set(names)):
        raise ValueError("Audit variant names must be unique")
    return tuple(variants)


def stability_band(overlap_share: float) -> str:
    """Classify top-k retention using the project's declared review bands."""

    if not isfinite(overlap_share) or not 0 <= overlap_share <= 1:
        raise ValueError("overlap_share must be finite and between zero and one")
    if overlap_share >= 0.7:
        return "high"
    if overlap_share >= 0.5:
        return "moderate"
    return "low"


def ranked_overlap(
    reference: Sequence[Hashable] | Iterable[Hashable],
    comparison: Sequence[Hashable] | Iterable[Hashable],
    *,
    top_k: int,
    top_n: int = 3,
) -> RankedOverlap:
    """Compare two deterministic rankings without treating absent items as tied ranks."""

    if top_k <= 0:
        raise ValueError("top_k must be positive")
    if top_n <= 0 or top_n > top_k:
        raise ValueError("top_n must be positive and no greater than top_k")
    reference_values = tuple(reference)[:top_k]
    comparison_values = tuple(comparison)[:top_k]
    if len(reference_values) != top_k or len(comparison_values) != top_k:
        raise ValueError("Both rankings must contain at least top_k items")
    if len(set(reference_values)) != len(reference_values):
        raise ValueError("The reference ranking contains duplicate identifiers")
    if len(set(comparison_values)) != len(comparison_values):
        raise ValueError("The comparison ranking contains duplicate identifiers")

    reference_set = set(reference_values)
    comparison_set = set(comparison_values)
    shared = reference_set & comparison_set
    union = reference_set | comparison_set
    overlap_count = len(shared)
    overlap_share = overlap_count / top_k
    reference_ranks = {value: index + 1 for index, value in enumerate(reference_values)}
    comparison_ranks = {value: index + 1 for index, value in enumerate(comparison_values)}
    mean_rank_displacement = (
        sum(abs(reference_ranks[value] - comparison_ranks[value]) for value in shared)
        / overlap_count
        if shared
        else float(top_k)
    )
    top_n_retained = len(set(reference_values[:top_n]) & set(comparison_values[:top_n]))
    return RankedOverlap(
        overlap_count=overlap_count,
        overlap_share=overlap_share,
        jaccard_similarity=overlap_count / len(union),
        top_three_retention_count=top_n_retained,
        top_three_retention_share=top_n_retained / top_n,
        mean_shared_rank_displacement=mean_rank_displacement,
        stability_band=stability_band(overlap_share),
    )


def build_baseline_match_audit(matches: Any) -> Any:
    """Summarize top-k completeness, repeated tracts, age, distance, and geography per query."""

    available_columns = getattr(matches, "columns", ())
    validate_audit_match_columns(available_columns)

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        matches.groupBy(
            *AUDIT_QUERY_KEYS,
            "query_region_name",
            "query_geographic_role",
            "query_modeling_cohort",
            "representation_name",
        )
        .agg(
            functions.count(functions.lit(1)).alias("match_count"),
            functions.countDistinct("candidate_geoid_2020").alias(
                "distinct_candidate_tract_count"
            ),
            functions.countDistinct(
                "candidate_geoid_2020", "candidate_origin_year"
            ).alias("distinct_candidate_state_count"),
            functions.min("candidate_origin_year").alias("oldest_candidate_origin_year"),
            functions.max("candidate_origin_year").alias("newest_candidate_origin_year"),
            functions.avg("candidate_age_years").alias("mean_candidate_age_years"),
            functions.avg("similarity_distance").alias("mean_similarity_distance"),
            functions.max("similarity_distance").alias("maximum_similarity_distance"),
            functions.avg(
                functions.when(
                    functions.col("query_state_abbreviation")
                    != functions.col("candidate_state_abbreviation"),
                    1.0,
                ).otherwise(0.0)
            ).alias("cross_state_match_share"),
            functions.avg(
                functions.when(
                    (
                        functions.col("query_state_abbreviation")
                        == functions.col("candidate_state_abbreviation")
                    )
                    & (
                        functions.col("query_county_name")
                        == functions.col("candidate_county_name")
                    ),
                    1.0,
                ).otherwise(0.0)
            ).alias("same_county_match_share"),
        )
        .withColumn(
            "repeated_candidate_tract_count",
            functions.col("match_count") - functions.col("distinct_candidate_tract_count"),
        )
        .withColumn(
            "has_repeated_candidate_tract",
            functions.col("repeated_candidate_tract_count") > 0,
        )
    )


def select_case_review_queries(matches: Any) -> Any:
    """Select deterministic representative and diagnostic queries without using future outcomes."""

    available_columns = getattr(matches, "columns", ())
    validate_audit_match_columns(available_columns)

    from pyspark.sql import Window, functions  # type: ignore[import-not-found]

    baseline_audit = build_baseline_match_audit(matches)
    query_summary = baseline_audit.groupBy(
        *AUDIT_QUERY_KEYS,
        "query_region_name",
        "query_geographic_role",
        "query_modeling_cohort",
    ).agg(
        functions.avg("mean_similarity_distance").alias("mean_similarity_distance"),
        functions.max("maximum_similarity_distance").alias("maximum_similarity_distance"),
        functions.max(functions.col("has_repeated_candidate_tract").cast("int")).alias(
            "has_repeated_candidate_tract_int"
        ),
    )

    raw = matches.where(
        functions.col("representation_name") == "weighted_standardized"
    ).select(
        *AUDIT_QUERY_KEYS,
        "candidate_geoid_2020",
        "candidate_origin_year",
    )
    pca = matches.where(functions.col("representation_name") == "pca").select(
        *AUDIT_QUERY_KEYS,
        "candidate_geoid_2020",
        "candidate_origin_year",
    )
    overlap = (
        raw.join(
            pca,
            [*AUDIT_QUERY_KEYS, "candidate_geoid_2020", "candidate_origin_year"],
            "inner",
        )
        .groupBy(*AUDIT_QUERY_KEYS)
        .agg(functions.count(functions.lit(1)).alias("representation_overlap_count"))
    )
    query_summary = query_summary.join(overlap, list(AUDIT_QUERY_KEYS), "left").fillna(
        {"representation_overlap_count": 0}
    )

    stable_hash = functions.xxhash64(*AUDIT_QUERY_KEYS)
    representative_window = Window.partitionBy(
        "horizon_years", "query_region_name", "query_geographic_role"
    ).orderBy(stable_hash, "query_geoid_2020", "query_origin_year")
    representative = (
        query_summary.withColumn(
            "_case_rank", functions.row_number().over(representative_window)
        )
        .where(functions.col("_case_rank") == 1)
        .select(*AUDIT_QUERY_KEYS)
        .withColumn("case_selection_reason", functions.lit("representative_region_and_role"))
    )

    low_overlap_window = Window.partitionBy("horizon_years").orderBy(
        "representation_overlap_count", stable_hash
    )
    low_overlap = (
        query_summary.withColumn("_case_rank", functions.row_number().over(low_overlap_window))
        .where(functions.col("_case_rank") <= 2)
        .select(*AUDIT_QUERY_KEYS)
        .withColumn("case_selection_reason", functions.lit("lowest_representation_overlap"))
    )

    distant_window = Window.partitionBy("horizon_years").orderBy(
        functions.col("mean_similarity_distance").desc(), stable_hash
    )
    distant = (
        query_summary.withColumn("_case_rank", functions.row_number().over(distant_window))
        .where(functions.col("_case_rank") <= 2)
        .select(*AUDIT_QUERY_KEYS)
        .withColumn("case_selection_reason", functions.lit("largest_mean_match_distance"))
    )
    repeated = (
        query_summary.where(functions.col("has_repeated_candidate_tract_int") > 0)
        .select(*AUDIT_QUERY_KEYS)
        .withColumn("case_selection_reason", functions.lit("repeated_candidate_tract"))
    )

    selections = representative.unionByName(low_overlap).unionByName(distant).unionByName(repeated)
    return selections.groupBy(*AUDIT_QUERY_KEYS).agg(
        functions.concat_ws(
            ",",
            functions.sort_array(functions.collect_set("case_selection_reason")),
        ).alias("case_selection_reasons")
    )


def build_case_review(matches: Any, modeling_panel: Any) -> Any:
    """Attach feature arrays and family gaps to deterministic review cases."""

    available_columns = getattr(matches, "columns", ())
    validate_audit_match_columns(available_columns)

    from pyspark.ml.functions import vector_to_array  # type: ignore[import-not-found]
    from pyspark.sql import functions  # type: ignore[import-not-found]

    selected_queries = select_case_review_queries(matches)
    review_matches = matches.join(selected_queries, list(AUDIT_QUERY_KEYS), "inner")
    horizon_values = [row[0] for row in review_matches.select("horizon_years").distinct().collect()]
    feature_frames = []
    for horizon in sorted(int(value) for value in horizon_values):
        horizon_panel = modeling_panel.where(functions.col("horizon_years") == horizon)
        standardized = fit_analogue_preprocessing(horizon_panel)
        feature_frames.append(
            standardized.select(
                "geoid_2020",
                "forecast_origin_year",
                "horizon_years",
                vector_to_array("_analogue_unscaled_vector").alias("feature_values"),
                vector_to_array("_analogue_standardized_vector").alias(
                    "standardized_feature_values"
                ),
            )
        )
    features = feature_frames[0]
    for feature_frame in feature_frames[1:]:
        features = features.unionByName(feature_frame)

    query_features = features.select(
        functions.col("geoid_2020").alias("query_geoid_2020"),
        functions.col("forecast_origin_year").alias("query_origin_year"),
        "horizon_years",
        functions.col("feature_values").alias("query_feature_values"),
        functions.col("standardized_feature_values").alias(
            "query_standardized_feature_values"
        ),
    )
    candidate_features = features.select(
        functions.col("geoid_2020").alias("candidate_geoid_2020"),
        functions.col("forecast_origin_year").alias("candidate_origin_year"),
        "horizon_years",
        functions.col("feature_values").alias("candidate_feature_values"),
        functions.col("standardized_feature_values").alias(
            "candidate_standardized_feature_values"
        ),
    )
    review = review_matches.join(query_features, list(AUDIT_QUERY_KEYS), "inner").join(
        candidate_features,
        ["candidate_geoid_2020", "candidate_origin_year", "horizon_years"],
        "inner",
    )
    review = review.withColumn(
        "standardized_absolute_feature_differences",
        functions.zip_with(
            "query_standardized_feature_values",
            "candidate_standardized_feature_values",
            lambda query_value, candidate_value: functions.abs(query_value - candidate_value),
        ),
    ).withColumn(
        "analogue_feature_order",
        functions.array(*[functions.lit(feature) for feature in ANALOGUE_FEATURE_COLUMNS]),
    )

    family_gap_columns = []
    for family, family_features in ANALOGUE_FEATURE_FAMILIES.items():
        indices = [ANALOGUE_FEATURE_COLUMNS.index(feature) for feature in family_features]
        family_gap = sum(
            (
                functions.element_at(
                    "standardized_absolute_feature_differences", index + 1
                )
                for index in indices
            ),
            functions.lit(0.0),
        ) / functions.lit(float(len(indices)))
        column_name = f"{family}_mean_absolute_standardized_gap"
        review = review.withColumn(column_name, family_gap)
        family_gap_columns.append(column_name)

    review = (
        review.withColumn(
            "strongest_shared_feature",
            functions.expr(
                "element_at(analogue_feature_order, "
                "cast(array_position(standardized_absolute_feature_differences, "
                "array_min(standardized_absolute_feature_differences)) as int))"
            ),
        )
        .withColumn(
            "largest_difference_feature",
            functions.expr(
                "element_at(analogue_feature_order, "
                "cast(array_position(standardized_absolute_feature_differences, "
                "array_max(standardized_absolute_feature_differences)) as int))"
            ),
        )
        .withColumn(
            "case_review_schema_version", functions.lit(ANALOGUE_AUDIT_SCHEMA_VERSION)
        )
    )
    return review.select(
        *review_matches.columns,
        "query_feature_values",
        "candidate_feature_values",
        "analogue_feature_order",
        "standardized_absolute_feature_differences",
        *family_gap_columns,
        "strongest_shared_feature",
        "largest_difference_feature",
        "case_review_schema_version",
    )

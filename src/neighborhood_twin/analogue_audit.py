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

from neighborhood_twin.historical_analogues import (
    ANALOGUE_FEATURE_COLUMNS,
    ANALOGUE_FEATURE_FAMILIES,
    DEFAULT_PCA_COMPONENTS,
)

ANALOGUE_AUDIT_SCHEMA_VERSION = "1.0.0"
ANALOGUE_AUDIT_MATCH_TABLE = "historical_analogue_audit_match"
ANALOGUE_CASE_REVIEW_TABLE = "historical_analogue_case_review"
ANALOGUE_STABILITY_SUMMARY_TABLE = "historical_analogue_stability_summary"

BASELINE_FAMILY_FACTORS = {family: 1.0 for family in ANALOGUE_FEATURE_FAMILIES}
DEFAULT_WEIGHT_PERTURBATION_FACTORS = (0.8, 1.2)
DEFAULT_PCA_COMPONENT_COUNTS = (5, DEFAULT_PCA_COMPONENTS, 7)


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

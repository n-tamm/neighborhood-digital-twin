"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.analogue_audit import (
    AUDIT_MATCH_REQUIRED_COLUMNS,
    BASELINE_FAMILY_FACTORS,
    audit_feature_multipliers,
    audit_feature_weights,
    default_audit_variants,
    normalized_family_weights,
    ranked_overlap,
    stability_band,
    validate_audit_match_columns,
    validate_family_factors,
)
from neighborhood_twin.historical_analogues import (
    ANALOGUE_FEATURE_COLUMNS,
    ANALOGUE_FEATURE_FAMILIES,
)


def test_baseline_audit_weights_reproduce_equal_family_weighting() -> None:
    family_weights = normalized_family_weights(BASELINE_FAMILY_FACTORS)
    feature_weights = dict(
        zip(
            ANALOGUE_FEATURE_COLUMNS,
            audit_feature_weights(BASELINE_FAMILY_FACTORS),
            strict=True,
        )
    )
    multipliers = audit_feature_multipliers(BASELINE_FAMILY_FACTORS)

    assert sum(family_weights.values()) == pytest.approx(len(ANALOGUE_FEATURE_FAMILIES))
    for family, features in ANALOGUE_FEATURE_FAMILIES.items():
        assert family_weights[family] == pytest.approx(1.0)
        assert sum(feature_weights[feature] for feature in features) == pytest.approx(1.0)
    for multiplier, weight in zip(multipliers, feature_weights.values(), strict=True):
        assert multiplier**2 == pytest.approx(weight)


def test_weight_perturbations_are_renormalized_and_ablations_remain_valid() -> None:
    increased = {**BASELINE_FAMILY_FACTORS, "affordability": 1.2}
    increased_weights = normalized_family_weights(increased)
    assert increased_weights["affordability"] > 1.0
    assert sum(increased_weights.values()) == pytest.approx(5.0)

    ablated = {**BASELINE_FAMILY_FACTORS, "market_trajectory": 0.0}
    ablated_weights = normalized_family_weights(ablated)
    assert ablated_weights["market_trajectory"] == 0.0
    assert all(
        ablated_weights[family] == pytest.approx(1.25)
        for family in ANALOGUE_FEATURE_FAMILIES
        if family != "market_trajectory"
    )


def test_family_factor_validation_rejects_registry_and_numeric_errors() -> None:
    validate_family_factors(BASELINE_FAMILY_FACTORS)
    with pytest.raises(ValueError, match="missing"):
        validate_family_factors({"community_scale": 1.0})
    with pytest.raises(ValueError, match="unexpected"):
        validate_family_factors({**BASELINE_FAMILY_FACTORS, "unknown": 1.0})
    with pytest.raises(ValueError, match="nonnegative"):
        validate_family_factors({**BASELINE_FAMILY_FACTORS, "affordability": -0.1})
    with pytest.raises(ValueError, match="At least one"):
        validate_family_factors({family: 0.0 for family in ANALOGUE_FEATURE_FAMILIES})


def test_match_audit_contract_rejects_missing_baseline_fields() -> None:
    validate_audit_match_columns(AUDIT_MATCH_REQUIRED_COLUMNS)
    with pytest.raises(ValueError, match="candidate_target_cumulative_log_change"):
        validate_audit_match_columns(
            tuple(
                column
                for column in AUDIT_MATCH_REQUIRED_COLUMNS
                if column != "candidate_target_cumulative_log_change"
            )
        )


def test_default_variants_are_bounded_unique_and_separate_stress_tests() -> None:
    variants = default_audit_variants()
    names = [variant.variant_name for variant in variants]
    kinds = [variant.perturbation_kind for variant in variants]

    assert len(variants) == 21
    assert len(names) == len(set(names))
    assert kinds.count("baseline") == 2
    assert kinds.count("small_weight_change") == 10
    assert kinds.count("family_ablation") == 5
    assert kinds.count("pca_component_count") == 2
    assert kinds.count("candidate_uniqueness") == 2


def test_ranked_overlap_reports_retention_jaccard_and_rank_movement() -> None:
    result = ranked_overlap(
        ("a", "b", "c", "d", "e"),
        ("b", "a", "c", "x", "y"),
        top_k=5,
    )

    assert result.overlap_count == 3
    assert result.overlap_share == pytest.approx(0.6)
    assert result.jaccard_similarity == pytest.approx(3 / 7)
    assert result.top_three_retention_count == 3
    assert result.top_three_retention_share == pytest.approx(1.0)
    assert result.mean_shared_rank_displacement == pytest.approx(2 / 3)
    assert result.stability_band == "moderate"


def test_ranked_overlap_rejects_incomplete_or_duplicate_rankings() -> None:
    with pytest.raises(ValueError, match="at least top_k"):
        ranked_overlap(("a",), ("a", "b"), top_k=2, top_n=2)
    with pytest.raises(ValueError, match="reference.*duplicate"):
        ranked_overlap(("a", "a"), ("a", "b"), top_k=2, top_n=2)
    with pytest.raises(ValueError, match="comparison.*duplicate"):
        ranked_overlap(("a", "b"), ("a", "a"), top_k=2, top_n=2)


def test_stability_bands_are_validated_and_apply_declared_thresholds() -> None:
    assert stability_band(0.7) == "high"
    assert stability_band(0.5) == "moderate"
    assert stability_band(0.49) == "low"
    with pytest.raises(ValueError, match="between zero and one"):
        stability_band(1.1)

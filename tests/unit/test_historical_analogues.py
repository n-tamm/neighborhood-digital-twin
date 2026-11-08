"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.historical_analogues import (
    ANALOGUE_FEATURE_COLUMNS,
    ANALOGUE_FEATURE_FAMILIES,
    ANALOGUE_REQUIRED_COLUMNS,
    add_weighted_analogue_vector,
    analogue_feature_multipliers,
    analogue_feature_weights,
    fit_analogue_pca,
    latest_candidate_origin_year,
    validate_analogue_columns,
    validate_analogue_settings,
)


def test_candidate_cutoff_requires_the_outcome_to_be_known_by_query_time() -> None:
    assert latest_candidate_origin_year(2022, 1) == 2021
    assert latest_candidate_origin_year(2022, 3) == 2019
    with pytest.raises(ValueError, match="positive"):
        latest_candidate_origin_year(2022, 0)


def test_feature_families_receive_equal_total_distance_weight() -> None:
    weights = dict(zip(ANALOGUE_FEATURE_COLUMNS, analogue_feature_weights(), strict=True))
    multipliers = analogue_feature_multipliers()
    assert len(weights) == len(ANALOGUE_FEATURE_COLUMNS)
    assert len(multipliers) == len(ANALOGUE_FEATURE_COLUMNS)
    for family_features in ANALOGUE_FEATURE_FAMILIES.values():
        assert sum(weights[feature] for feature in family_features) == pytest.approx(1.0)
    for multiplier, weight in zip(multipliers, weights.values(), strict=True):
        assert multiplier**2 == pytest.approx(weight)


def test_historical_analogue_contract_rejects_missing_columns_and_invalid_settings() -> None:
    validate_analogue_columns(ANALOGUE_REQUIRED_COLUMNS)
    with pytest.raises(ValueError, match="state_origin_mean_annual_change_pct"):
        validate_analogue_columns(ANALOGUE_REQUIRED_COLUMNS[:-1])

    validate_analogue_settings(
        horizons=(1, 3),
        queries_per_group=1,
        top_k=10,
        pca_components=6,
    )
    with pytest.raises(ValueError, match="duplicates"):
        validate_analogue_settings(
            horizons=(1, 1),
            queries_per_group=1,
            top_k=10,
            pca_components=6,
        )
    with pytest.raises(ValueError, match="queries_per_group"):
        validate_analogue_settings(
            horizons=(1,),
            queries_per_group=0,
            top_k=10,
            pca_components=6,
        )
    with pytest.raises(ValueError, match="top_k"):
        validate_analogue_settings(
            horizons=(1,),
            queries_per_group=1,
            top_k=0,
            pca_components=6,
        )


def test_reusable_representation_helpers_validate_before_spark_execution() -> None:
    with pytest.raises(ValueError, match="feature count"):
        add_weighted_analogue_vector(object(), multipliers=(1.0,))
    with pytest.raises(ValueError, match="between one"):
        fit_analogue_pca(object(), pca_components=0)

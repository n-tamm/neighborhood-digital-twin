"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.model_readiness import (
    DEFAULT_LOCKED_TEST_ORIGINS,
    DEFAULT_VALIDATION_ORIGIN_COUNTS,
    TEMPORAL_ROLES,
    build_split_rules,
    parse_horizon_mapping,
    temporal_split_role,
)


def test_horizon_mapping_parser_requires_distinct_positive_integer_pairs() -> None:
    assert parse_horizon_mapping("1:2024,3:2022,5:2020", label="test") == {
        1: 2024,
        3: 2022,
        5: 2020,
    }
    with pytest.raises(ValueError, match="horizon:value"):
        parse_horizon_mapping("1=2024", label="test")
    with pytest.raises(ValueError, match="must not repeat"):
        parse_horizon_mapping("1:2024,1:2023", label="test")
    with pytest.raises(ValueError, match="must be positive"):
        parse_horizon_mapping("1:0", label="test")


def test_split_rules_derive_point_in_time_calibration_and_validation_years() -> None:
    rules = build_split_rules(
        horizons=(1, 3, 5),
        locked_test_origins=DEFAULT_LOCKED_TEST_ORIGINS,
        validation_origin_counts=DEFAULT_VALIDATION_ORIGIN_COUNTS,
    )

    assert [rule.to_record() for rule in rules] == [
        {
            "horizon_years": 1,
            "locked_test_origin_year": 2024,
            "calibration_origin_year": 2023,
            "validation_start_origin_year": 2021,
            "validation_end_origin_year": 2022,
        },
        {
            "horizon_years": 3,
            "locked_test_origin_year": 2022,
            "calibration_origin_year": 2019,
            "validation_start_origin_year": 2017,
            "validation_end_origin_year": 2018,
        },
        {
            "horizon_years": 5,
            "locked_test_origin_year": 2020,
            "calibration_origin_year": 2015,
            "validation_start_origin_year": 2014,
            "validation_end_origin_year": 2014,
        },
    ]


def test_split_rules_require_complete_horizon_configuration() -> None:
    with pytest.raises(ValueError, match="every configured horizon"):
        build_split_rules(
            horizons=(1, 3, 5),
            locked_test_origins={1: 2024, 3: 2022},
            validation_origin_counts=DEFAULT_VALIDATION_ORIGIN_COUNTS,
        )
    with pytest.raises(ValueError, match="at least one validation"):
        build_split_rules(
            horizons=(1, 3, 5),
            locked_test_origins=DEFAULT_LOCKED_TEST_ORIGINS,
            validation_origin_counts={1: 2, 3: 2, 5: 0},
        )


def test_temporal_split_roles_purge_labels_unknown_at_the_locked_origin() -> None:
    rules = {
        rule.horizon_years: rule
        for rule in build_split_rules(
            horizons=(1, 3, 5),
            locked_test_origins=DEFAULT_LOCKED_TEST_ORIGINS,
            validation_origin_counts=DEFAULT_VALIDATION_ORIGIN_COUNTS,
        )
    }

    assert temporal_split_role(
        forecast_origin_year=2024,
        target_end_year=2025,
        target_is_observed=True,
        rule=rules[1],
    ) == "locked_temporal_test"
    assert temporal_split_role(
        forecast_origin_year=2023,
        target_end_year=2024,
        target_is_observed=True,
        rule=rules[1],
    ) == "calibration"
    assert temporal_split_role(
        forecast_origin_year=2021,
        target_end_year=2022,
        target_is_observed=True,
        rule=rules[1],
    ) == "validation"
    assert temporal_split_role(
        forecast_origin_year=2020,
        target_end_year=2021,
        target_is_observed=True,
        rule=rules[1],
    ) == "training"
    assert temporal_split_role(
        forecast_origin_year=2020,
        target_end_year=2023,
        target_is_observed=True,
        rule=rules[3],
    ) == "purged_pretest"
    assert temporal_split_role(
        forecast_origin_year=2025,
        target_end_year=2026,
        target_is_observed=False,
        rule=rules[1],
    ) == "future_scoring"
    assert set(TEMPORAL_ROLES) == {
        "training",
        "validation",
        "calibration",
        "purged_pretest",
        "locked_temporal_test",
        "future_scoring",
        "ineligible_target",
    }

"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.exploration import validate_horizons
from neighborhood_twin.products import (
    ACS_PROFILE_COLUMNS,
    KNOWN_CURRENT_ACS_GEOID_EXCEPTION_STATES,
    SIMILARITY_FEATURE_COLUMNS,
    parse_state_fips_codes,
)
from neighborhood_twin.visual_exploration import housing_composition_band


def test_similarity_features_are_available_in_current_profile() -> None:
    assert set(SIMILARITY_FEATURE_COLUMNS).issubset(ACS_PROFILE_COLUMNS)
    assert len(SIMILARITY_FEATURE_COLUMNS) == len(set(SIMILARITY_FEATURE_COLUMNS))


def test_connecticut_is_the_only_reviewed_residual_water_geoid_exception() -> None:
    assert KNOWN_CURRENT_ACS_GEOID_EXCEPTION_STATES == ("09",)


def test_demo_state_scope_is_normalized() -> None:
    assert parse_state_fips_codes("04, 26,42") == ("04", "26", "42")


@pytest.mark.parametrize("value", ["", "4", "AA", "04,04"])
def test_demo_state_scope_rejects_ambiguous_values(value: str) -> None:
    with pytest.raises(ValueError):
        parse_state_fips_codes(value)


def test_validate_horizons_orders_supported_values() -> None:
    assert validate_horizons((5, 1, 3)) == (1, 3, 5)


@pytest.mark.parametrize("horizons", [(), (0,), (1, 1), (1, -3)])
def test_validate_horizons_rejects_invalid_values(horizons: tuple[int, ...]) -> None:
    with pytest.raises(ValueError):
        validate_horizons(horizons)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "Missing housing composition"),
        (0.0, "Less than 25% single-family"),
        (0.2499, "Less than 25% single-family"),
        (0.25, "25% to less than 50%"),
        (0.5, "50% to less than 75%"),
        (0.75, "75% to less than 90%"),
        (0.9, "90% to 100%"),
        (1.0, "90% to 100%"),
    ],
)
def test_housing_composition_bands_have_explicit_boundaries(
    value: float | None, expected: str
) -> None:
    assert housing_composition_band(value) == expected


@pytest.mark.parametrize("value", [-0.01, 1.02])
def test_housing_composition_bands_reject_invalid_shares(value: float) -> None:
    with pytest.raises(ValueError):
        housing_composition_band(value)

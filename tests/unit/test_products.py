"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.products import (
    ACS_PROFILE_COLUMNS,
    SIMILARITY_FEATURE_COLUMNS,
    parse_state_fips_codes,
)


def test_similarity_features_are_available_in_current_profile() -> None:
    assert set(SIMILARITY_FEATURE_COLUMNS).issubset(ACS_PROFILE_COLUMNS)
    assert len(SIMILARITY_FEATURE_COLUMNS) == len(set(SIMILARITY_FEATURE_COLUMNS))


def test_demo_state_scope_is_normalized() -> None:
    assert parse_state_fips_codes("04, 26,42") == ("04", "26", "42")


@pytest.mark.parametrize("value", ["", "4", "AA", "04,04"])
def test_demo_state_scope_rejects_ambiguous_values(value: str) -> None:
    with pytest.raises(ValueError):
        parse_state_fips_codes(value)

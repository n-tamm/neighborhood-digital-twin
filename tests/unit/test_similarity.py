"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.products import SIMILARITY_FEATURE_COLUMNS
from neighborhood_twin.similarity import (
    parse_geoid_list,
    transformed_feature_name,
    validate_similarity_features,
)


def test_similarity_geoid_parser_accepts_optional_explicit_queries() -> None:
    assert parse_geoid_list("") == ()
    assert parse_geoid_list("01001020100, 26163500100") == (
        "01001020100",
        "26163500100",
    )
    with pytest.raises(ValueError, match="duplicates"):
        parse_geoid_list("01001020100,01001020100")
    with pytest.raises(ValueError, match="eleven"):
        parse_geoid_list("123")


def test_similarity_feature_registry_and_transforms_are_explicit() -> None:
    validate_similarity_features(SIMILARITY_FEATURE_COLUMNS)
    with pytest.raises(ValueError, match="population_total_estimate"):
        validate_similarity_features(SIMILARITY_FEATURE_COLUMNS[1:])
    assert transformed_feature_name("population_total_estimate").endswith("__log1p")
    assert transformed_feature_name("single_family_share_estimate").endswith("__identity")

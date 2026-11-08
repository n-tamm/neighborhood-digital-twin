"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.analogue_selection import (
    DEFAULT_SELECTION_QUERIES_PER_GROUP,
    REQUIRED_SELECTION_COVERAGE_COLUMNS,
    SELECTION_COVERAGE_DIMENSIONS,
    SELECTION_SCORECARD_SLICES,
    validate_selection_settings,
)


def test_selection_defaults_expand_the_baseline_and_keep_named_dimensions_unique() -> None:
    assert DEFAULT_SELECTION_QUERIES_PER_GROUP == 5
    assert len(SELECTION_COVERAGE_DIMENSIONS) == len(
        {name for name, _ in SELECTION_COVERAGE_DIMENSIONS}
    )
    assert len(SELECTION_SCORECARD_SLICES) == len(
        {name for name, _ in SELECTION_SCORECARD_SLICES}
    )
    assert set(REQUIRED_SELECTION_COVERAGE_COLUMNS) == {
        "query_housing_composition_band",
        "query_community_size_band",
        "query_acs_uncertainty_band",
    }


def test_selection_settings_require_expansion_and_an_outcome_range() -> None:
    validate_selection_settings(queries_per_group=5, top_k=10)
    with pytest.raises(ValueError, match="exceed one"):
        validate_selection_settings(queries_per_group=1, top_k=10)
    with pytest.raises(ValueError, match="at least three"):
        validate_selection_settings(queries_per_group=5, top_k=2)

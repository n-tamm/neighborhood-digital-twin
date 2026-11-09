"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.current_analogues import (
    CURRENT_ANALOGUE_REPRESENTATION,
    CURRENT_ANALOGUE_SCHEMA_VERSION,
    LOCKED_TEMPORAL_ROLE,
    validate_current_analogue_settings,
)


def test_current_analogue_contract_freezes_the_selected_representation() -> None:
    assert CURRENT_ANALOGUE_SCHEMA_VERSION == "1.0.0"
    assert CURRENT_ANALOGUE_REPRESENTATION == "weighted_standardized"
    assert LOCKED_TEMPORAL_ROLE == "locked_temporal_test"


def test_current_analogue_settings_require_bounded_valid_retrieval() -> None:
    validate_current_analogue_settings(
        horizons=(1, 3), queries_per_state=1, top_k=10, as_of_year=2025
    )
    with pytest.raises(ValueError, match="positive integers"):
        validate_current_analogue_settings(
            horizons=(0,), queries_per_state=1, top_k=10, as_of_year=2025
        )
    with pytest.raises(ValueError, match="duplicates"):
        validate_current_analogue_settings(
            horizons=(1, 1), queries_per_state=1, top_k=10, as_of_year=2025
        )
    with pytest.raises(ValueError, match="queries_per_state"):
        validate_current_analogue_settings(
            horizons=(1,), queries_per_state=0, top_k=10, as_of_year=2025
        )
    with pytest.raises(ValueError, match="at least three"):
        validate_current_analogue_settings(
            horizons=(1,), queries_per_state=1, top_k=2, as_of_year=2025
        )
    with pytest.raises(ValueError, match="four-digit"):
        validate_current_analogue_settings(
            horizons=(1,), queries_per_state=1, top_k=10, as_of_year=25
        )

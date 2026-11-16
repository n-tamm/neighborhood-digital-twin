"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

from neighborhood_twin.analogue_serving_enrichment import (
    ANALOGUE_FAMILY_DISPLAY_NAMES,
    ANALOGUE_FEATURE_DISPLAY_NAMES,
    EXPLANATION_SCOPE_NOTE,
    TRAJECTORY_SCOPE_NOTE,
    validate_explanation_registry,
)
from neighborhood_twin.historical_analogues import (
    ANALOGUE_FEATURE_COLUMNS,
    ANALOGUE_FEATURE_FAMILIES,
)


def test_explanation_registry_covers_every_governed_family_and_feature() -> None:
    validate_explanation_registry()

    assert set(ANALOGUE_FAMILY_DISPLAY_NAMES) == set(ANALOGUE_FEATURE_FAMILIES)
    assert set(ANALOGUE_FEATURE_DISPLAY_NAMES) == set(ANALOGUE_FEATURE_COLUMNS)
    assert all(value.strip() for value in ANALOGUE_FAMILY_DISPLAY_NAMES.values())
    assert all(value.strip() for value in ANALOGUE_FEATURE_DISPLAY_NAMES.values())


def test_interpretation_notes_preserve_descriptive_boundaries() -> None:
    assert "causal" in EXPLANATION_SCOPE_NOTE
    assert "not a forecast" in TRAJECTORY_SCOPE_NOTE
    assert "single-family" in TRAJECTORY_SCOPE_NOTE

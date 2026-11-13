"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.analogue_serving import (
    ANALOGUE_SERVING_AVAILABILITY_TABLE,
    ANALOGUE_SERVING_MATCH_TABLE,
    ANALOGUE_SERVING_SCHEMA_VERSION,
    ANALOGUE_SERVING_SUMMARY_TABLE,
    AnalogueServingRelease,
    new_analogue_serving_release,
    validate_analogue_serving_release,
)


def _release(**overrides: object) -> AnalogueServingRelease:
    values = {
        "release_id": "analogue-20261112T120000000000Z",
        "built_at_utc": "2026-11-12T12:00:00+00:00",
        "as_of_year": 2025,
        "horizons": (1, 3),
        "top_k": 10,
        "model_readiness_build_id": "model-build",
        "source_tree_run_id": "tree-run",
    }
    values.update(overrides)
    return AnalogueServingRelease(**values)  # type: ignore[arg-type]


def test_serving_contract_constants_and_release_factory() -> None:
    assert ANALOGUE_SERVING_SCHEMA_VERSION == "1.0.0"
    assert ANALOGUE_SERVING_MATCH_TABLE == "serving_analogue_match_current"
    assert ANALOGUE_SERVING_SUMMARY_TABLE == "serving_analogue_summary_current"
    assert ANALOGUE_SERVING_AVAILABILITY_TABLE == "serving_analogue_availability_current"

    release = new_analogue_serving_release(
        as_of_year=2025,
        horizons=(1, 3),
        top_k=10,
        model_readiness_build_id="model-build",
        source_tree_run_id="tree-run",
        release_id="release-id",
        built_at_utc="2026-11-12T12:00:00+00:00",
    )
    assert release.release_id == "release-id"
    assert release.horizons == (1, 3)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"release_id": ""}, "release_id"),
        ({"built_at_utc": ""}, "built_at_utc"),
        ({"as_of_year": 25}, "as_of_year"),
        ({"horizons": ()}, "horizons"),
        ({"horizons": (1, 1)}, "duplicates"),
        ({"top_k": 2}, "top_k"),
        ({"model_readiness_build_id": ""}, "model_readiness_build_id"),
        ({"source_tree_run_id": ""}, "source_tree_run_id"),
    ],
)
def test_serving_release_validation_rejects_invalid_settings(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_analogue_serving_release(_release(**overrides))

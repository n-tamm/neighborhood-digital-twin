"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.forecast_serving import (
    new_forecast_serving_release,
    validate_forecast_serving_release,
)


def test_forecast_release_normalizes_horizons_and_validates_lineage() -> None:
    release = new_forecast_serving_release(
        as_of_year=2025,
        horizons=(3, 1),
        model_readiness_build_id="readiness-1",
        forecast_final_run_id="forecast-1",
        release_id="release-1",
        built_at_utc="2026-11-19T12:00:00+00:00",
    )
    assert release.horizons == (1, 3)
    validate_forecast_serving_release(release)


def test_forecast_release_rejects_invalid_settings() -> None:
    with pytest.raises(ValueError, match="as_of_year"):
        new_forecast_serving_release(
            as_of_year=25,
            horizons=(1,),
            model_readiness_build_id="readiness-1",
            forecast_final_run_id="forecast-1",
        )
    with pytest.raises(ValueError, match="must not contain duplicates"):
        new_forecast_serving_release(
            as_of_year=2025,
            horizons=(1, 1),
            model_readiness_build_id="readiness-1",
            forecast_final_run_id="forecast-1",
        )

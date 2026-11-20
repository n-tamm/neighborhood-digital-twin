"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.historical import (
    ACS_PUBLICATION_LAG_YEARS,
    DEFAULT_FORECAST_HORIZONS,
    HISTORICAL_STATE_COLUMNS,
    acs_available_year,
    validate_forecast_horizons,
)


def test_acs_availability_uses_the_conservative_next_year_rule() -> None:
    assert ACS_PUBLICATION_LAG_YEARS == 1
    assert acs_available_year(2019) == 2020
    assert acs_available_year(2024) == 2025


def test_acs_availability_rejects_pre_five_year_release_dates() -> None:
    with pytest.raises(ValueError, match="2009 or later"):
        acs_available_year(2008)


def test_forecast_horizons_are_ordered_and_validated() -> None:
    assert DEFAULT_FORECAST_HORIZONS == (1, 3, 5)
    assert validate_forecast_horizons((5, 1, 3)) == (1, 3, 5)
    with pytest.raises(ValueError, match="must not contain duplicates"):
        validate_forecast_horizons((1, 1))
    with pytest.raises(ValueError, match="positive integers"):
        validate_forecast_horizons((0, 1))


def test_historical_state_contract_retains_alignment_and_timing_fields() -> None:
    required = {
        "geoid_2020",
        "acs_source_geoid",
        "acs_release_year",
        "acs_available_year",
        "source_geography_vintage",
        "geography_alignment_method",
    }
    assert required.issubset(HISTORICAL_STATE_COLUMNS)
    assert len(HISTORICAL_STATE_COLUMNS) == len(set(HISTORICAL_STATE_COLUMNS))

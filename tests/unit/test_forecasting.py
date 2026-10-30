"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import math

import pytest

from neighborhood_twin.forecasting import (
    LINEAR_FEATURE_COLUMNS,
    annualized_rate_from_cumulative_log,
    cumulative_log_from_annual_rate,
    validate_feature_registry,
)


@pytest.mark.parametrize("rate,horizon", [(0.0, 1), (4.5, 3), (-2.0, 5)])
def test_forecast_target_transforms_round_trip(rate: float, horizon: int) -> None:
    cumulative = cumulative_log_from_annual_rate(rate, horizon)
    assert annualized_rate_from_cumulative_log(cumulative, horizon) == pytest.approx(rate)


def test_forecast_target_transforms_validate_domain() -> None:
    with pytest.raises(ValueError, match="positive"):
        cumulative_log_from_annual_rate(3.0, 0)
    with pytest.raises(ValueError, match="greater than -100"):
        cumulative_log_from_annual_rate(-100.0, 1)
    with pytest.raises(ValueError, match="positive"):
        annualized_rate_from_cumulative_log(math.log(1.03), 0)


def test_forecast_feature_registry_names_missing_fields() -> None:
    validate_feature_registry(LINEAR_FEATURE_COLUMNS)
    with pytest.raises(ValueError, match="origin_annual_change_pct"):
        validate_feature_registry(LINEAR_FEATURE_COLUMNS[1:])

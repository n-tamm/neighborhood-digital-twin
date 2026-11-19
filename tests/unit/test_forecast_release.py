"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.forecast_release import (
    ForecastReleaseGatePolicy,
    evaluate_release_gate_values,
    validate_release_gate_policy,
)


def test_release_gate_accepts_a_better_calibrated_champion() -> None:
    eligible, reasons = evaluate_release_gate_values(
        observation_count=42_082,
        champion_mae=0.0599,
        zero_change_mae=0.0627,
        empirical_interval_coverage=0.894,
        nominal_coverage=0.90,
        policy=ForecastReleaseGatePolicy(),
    )
    assert eligible
    assert reasons == ()


def test_release_gate_records_each_failed_requirement() -> None:
    eligible, reasons = evaluate_release_gate_values(
        observation_count=500,
        champion_mae=0.294,
        zero_change_mae=0.157,
        empirical_interval_coverage=0.482,
        nominal_coverage=0.90,
        policy=ForecastReleaseGatePolicy(),
    )
    assert not eligible
    assert reasons == (
        "insufficient_locked_observations",
        "worse_than_zero_change_mae",
        "interval_coverage_below_threshold",
    )


def test_release_gate_rejects_invalid_policy() -> None:
    with pytest.raises(ValueError, match="positive"):
        validate_release_gate_policy(ForecastReleaseGatePolicy(minimum_observation_count=0))
    with pytest.raises(ValueError, match=r"\[0, 1\)"):
        validate_release_gate_policy(ForecastReleaseGatePolicy(interval_coverage_tolerance=1.0))

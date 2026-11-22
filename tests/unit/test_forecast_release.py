"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.forecast_release import (
    ForecastEvaluationPolicy,
    evaluate_threshold_values,
    validate_evaluation_policy,
)


def test_evaluation_threshold_accepts_a_better_calibrated_model() -> None:
    eligible, reasons = evaluate_threshold_values(
        observation_count=42_082,
        model_mae=0.0599,
        zero_change_mae=0.0627,
        empirical_interval_coverage=0.894,
        nominal_coverage=0.90,
        policy=ForecastEvaluationPolicy(),
    )
    assert eligible
    assert reasons == ()


def test_evaluation_threshold_records_each_failed_requirement() -> None:
    eligible, reasons = evaluate_threshold_values(
        observation_count=500,
        model_mae=0.294,
        zero_change_mae=0.157,
        empirical_interval_coverage=0.482,
        nominal_coverage=0.90,
        policy=ForecastEvaluationPolicy(),
    )
    assert not eligible
    assert reasons == (
        "insufficient_later_period_observations",
        "worse_than_zero_change_mae",
        "interval_coverage_below_threshold",
    )


def test_evaluation_threshold_rejects_invalid_policy() -> None:
    with pytest.raises(ValueError, match="positive"):
        validate_evaluation_policy(ForecastEvaluationPolicy(minimum_observation_count=0))
    with pytest.raises(ValueError, match=r"\[0, 1\)"):
        validate_evaluation_policy(ForecastEvaluationPolicy(interval_coverage_tolerance=1.0))

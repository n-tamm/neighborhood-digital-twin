"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.forecast_finalization import (
    ForecastModelSpecification,
    interval_quantile_probability,
    validate_model_specifications,
)


def test_model_specifications_require_both_models_per_horizon() -> None:
    specifications = (
        ForecastModelSpecification(1, "regularized_linear"),
        ForecastModelSpecification(1, "gradient_boosted_trees", gbt_max_depth=2),
        ForecastModelSpecification(3, "regularized_linear"),
        ForecastModelSpecification(3, "gradient_boosted_trees", gbt_max_depth=4),
    )
    validate_model_specifications(specifications)
    with pytest.raises(ValueError, match="repeat a model and horizon"):
        validate_model_specifications((specifications[0], specifications[0]))
    with pytest.raises(ValueError, match="Unsupported forecast model"):
        validate_model_specifications((ForecastModelSpecification(1, "random_forest"),))
    with pytest.raises(ValueError, match="Every horizon"):
        validate_model_specifications((specifications[0],))


def test_interval_quantile_uses_finite_sample_correction() -> None:
    assert interval_quantile_probability(100, 0.90) == pytest.approx(0.91)
    assert interval_quantile_probability(9, 0.90) == pytest.approx(1.0)
    with pytest.raises(ValueError, match="sample_count"):
        interval_quantile_probability(0, 0.90)
    with pytest.raises(ValueError, match="coverage"):
        interval_quantile_probability(100, 1.0)

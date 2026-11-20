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
    acs_uncertainty_band,
    active_forecast_model_horizons,
    annualized_rate_from_cumulative_log,
    cumulative_log_from_annual_rate,
    gbt_temporal_cv_origin_years,
    validate_feature_registry,
    validate_gradient_boosted_tree_parameters,
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


def test_gradient_boosted_tree_parameters_validate_domain() -> None:
    validate_gradient_boosted_tree_parameters(
        max_depth=4,
        max_iter=50,
        step_size=0.05,
        subsampling_rate=0.8,
    )
    with pytest.raises(ValueError, match="max_depth must be positive"):
        validate_gradient_boosted_tree_parameters(
            max_depth=0,
            max_iter=50,
            step_size=0.05,
            subsampling_rate=0.8,
        )
    with pytest.raises(ValueError, match="step_size"):
        validate_gradient_boosted_tree_parameters(
            max_depth=4,
            max_iter=50,
            step_size=0.0,
            subsampling_rate=0.8,
        )
    with pytest.raises(ValueError, match="subsampling_rate"):
        validate_gradient_boosted_tree_parameters(
            max_depth=4,
            max_iter=50,
            step_size=0.05,
            subsampling_rate=1.1,
        )


def test_active_forecast_models_ignore_five_year_panel_rows() -> None:
    assert active_forecast_model_horizons((1, 3, 5)) == (1, 3)
    assert active_forecast_model_horizons((3, 5)) == (3,)
    assert active_forecast_model_horizons((5,)) == ()


def test_gbt_temporal_cv_uses_recent_purge_safe_origins() -> None:
    one_year_origins = [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2020]
    assert gbt_temporal_cv_origin_years(
        one_year_origins, horizon_years=1
    ) == (2017, 2018, 2020)
    assert gbt_temporal_cv_origin_years(
        [2011, 2012, 2013], horizon_years=3
    ) == ()
    assert gbt_temporal_cv_origin_years([2011, 2012], horizon_years=5) == ()


@pytest.mark.parametrize(
    ("origins", "horizon", "max_folds", "message"),
    [
        ([2011, 2012], 0, 3, "horizon_years must be positive"),
        ([2011, 2012], 1, 0, "max_folds must be positive"),
    ],
)
def test_gbt_temporal_cv_validates_fold_settings(
    origins: list[int], horizon: int, max_folds: int, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        gbt_temporal_cv_origin_years(
            origins,
            horizon_years=horizon,
            max_folds=max_folds,
        )


def test_acs_uncertainty_band_is_publicly_importable() -> None:
    assert callable(acs_uncertainty_band)

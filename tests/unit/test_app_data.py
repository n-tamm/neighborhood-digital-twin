"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Contract tests for application configuration and the reduced local data repository.
"""

from pathlib import Path

import pytest
from neighborhood_app.data import (
    REQUIRED_RELEASE_COMPONENTS,
    AppSettings,
    SampleNeighborhoodRepository,
    validate_release_rows,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = REPOSITORY_ROOT / "app" / "sample_data" / "autauga_demo.json"


def test_sample_settings_and_repository_load_real_fixture() -> None:
    """The local app fixture should satisfy the same top-level view contract as live data."""

    settings = AppSettings(data_mode="sample", sample_path=SAMPLE_PATH)
    settings.validate()
    repository = SampleNeighborhoodRepository(SAMPLE_PATH)

    places = repository.search_places("Autauga")
    neighborhood = repository.load_neighborhood("01001020300")

    assert places["geoid_2020"].tolist() == ["01001020300"]
    assert neighborhood.profile["county_name"] == "Autauga County"
    assert neighborhood.horizon_available(1)
    assert neighborhood.horizon_available(3)
    assert set(neighborhood.summaries["horizon_years"]) == {1, 3}
    assert neighborhood.data_mode == "sample"


def test_settings_reject_unsafe_schema_identifier() -> None:
    """Schema configuration must not create an SQL-injection path."""

    settings = AppSettings(
        data_mode="sample",
        gold_schema="gold; DROP TABLE profile",
        sample_path=SAMPLE_PATH,
    )

    with pytest.raises(ValueError, match="Unsafe SQL identifier"):
        settings.validate()


def test_settings_require_warehouse_in_live_mode() -> None:
    """Live mode should fail early when the app resource was not injected."""

    settings = AppSettings(data_mode="live", warehouse_id=None)

    with pytest.raises(ValueError, match="DATABRICKS_WAREHOUSE_ID"):
        settings.validate()


def test_manifest_validation_accepts_one_complete_release() -> None:
    """One validated row per required serving component forms a compatible release."""

    rows = [
        {
            "serving_release_id": "release-1",
            "table_name": component,
            "release_status": "validated",
        }
        for component in REQUIRED_RELEASE_COMPONENTS
    ]

    validate_release_rows(rows)


def test_manifest_validation_rejects_partial_release() -> None:
    """The app must not combine a partial or mixed historical-analogue release."""

    rows = [
        {
            "serving_release_id": "release-1",
            "table_name": next(iter(REQUIRED_RELEASE_COMPONENTS)),
            "release_status": "validated",
        }
    ]

    with pytest.raises(ValueError, match="missing components"):
        validate_release_rows(rows)

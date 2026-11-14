"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Contract tests for application configuration and the reduced local data repository.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from neighborhood_app.data import (
    REQUIRED_RELEASE_COMPONENTS,
    AppSettings,
    DatabricksNeighborhoodRepository,
    SampleNeighborhoodRepository,
    validate_release_rows,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = REPOSITORY_ROOT / "app" / "sample_data" / "autauga_demo.json"


class RecordingExecutor:
    """Small executor double that records whether neighborhood reads use one batch."""

    def __init__(self) -> None:
        self.batch_queries: Sequence[tuple[str, Mapping[str, Any] | None]] = []

    def fetch_frame(
        self,
        statement: str,
        parameters: Mapping[str, Any] | None = None,
    ) -> pd.DataFrame:
        """Return one complete manifest for repository initialization."""

        del statement, parameters
        return pd.DataFrame(
            [
                {
                    "serving_release_id": "release-1",
                    "table_name": component,
                    "release_status": "validated",
                    "serving_built_at_utc": "2026-11-14T00:00:00Z",
                }
                for component in REQUIRED_RELEASE_COMPONENTS
            ]
        )

    def fetch_frames(
        self,
        queries: Sequence[tuple[str, Mapping[str, Any] | None]],
    ) -> list[pd.DataFrame]:
        """Return the seven result sets required by a neighborhood view."""

        self.batch_queries = queries
        profile = pd.DataFrame([{"geoid_2020": "01001020300", "county_name": "Autauga County"}])
        context = pd.DataFrame(
            [
                {
                    "geoid_2020": "01001020300",
                    "minimum_longitude": -86.5,
                    "minimum_latitude": 32.4,
                    "maximum_longitude": -86.4,
                    "maximum_latitude": 32.5,
                    "geometry_geojson": '{"type":"Polygon","coordinates":[]}',
                }
            ]
        )
        availability = pd.DataFrame([{"horizon_years": 1, "analogue_available": True}])
        return [
            profile,
            context,
            pd.DataFrame(),
            availability,
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        ]


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


def test_live_repository_batches_neighborhood_queries_and_loads_geometry() -> None:
    """One selected tract should reuse a connection while adding local boundary context."""

    executor = RecordingExecutor()
    settings = AppSettings(data_mode="live", warehouse_id="warehouse-1")
    repository = DatabricksNeighborhoodRepository(settings, executor)

    neighborhood = repository.load_neighborhood("01001020300")

    assert len(executor.batch_queries) == 7
    assert "st_asgeojson" in executor.batch_queries[1][0].lower()
    assert neighborhood.bounds["minimum_longitude"] == -86.5
    assert neighborhood.map_context["geoid_2020"].tolist() == ["01001020300"]

"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Known-answer tests for application formatting and chart construction.
"""

from pathlib import Path

import pandas as pd
import pytest
from neighborhood_app.charts import hpi_history_figure, neighborhood_context_map_figure
from neighborhood_app.ui import (
    format_currency,
    format_percent,
    format_square_miles,
    place_label,
)
from streamlit.testing.v1 import AppTest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_hpi_chart_does_not_plot_unavailable_observations() -> None:
    """Missing FHFA values must remain absent instead of becoming a continuous invented path."""

    history = pd.DataFrame(
        {
            "observation_year": [2022, 2023, 2024],
            "hpi": [200.0, None, 225.0],
            "hpi_available": [True, False, True],
        }
    )

    figure = hpi_history_figure(history)

    assert list(figure.data[0].x) == [2022, 2024]
    assert list(figure.data[0].y) == [200.0, 225.0]


def test_formatters_preserve_interpretable_units() -> None:
    """Current profile metrics should carry explicit currency and percentage units."""

    assert format_currency(63939) == "$63,939"
    assert format_percent(0.66559, value_is_share=True) == "66.6%"
    assert format_percent(3.24) == "3.2%"
    assert format_square_miles(2_589_988.110336) == "1.0 sq mi"
    assert format_currency(None) == "Not available"


def test_context_map_uses_boundaries_instead_of_point_markers() -> None:
    """The main geography view should render tract polygons and surrounding context."""

    geometry = (
        '{"type":"Polygon","coordinates":[['
        "[-86.5,32.4],[-86.4,32.4],[-86.4,32.5],[-86.5,32.5],[-86.5,32.4]"
        "]]}"
    )
    context = pd.DataFrame(
        [
            {
                "geoid_2020": "01001020300",
                "county_name": "Autauga County",
                "tract_name": "Census Tract 203",
                "minimum_longitude": -86.5,
                "minimum_latitude": 32.4,
                "maximum_longitude": -86.4,
                "maximum_latitude": 32.5,
                "geometry_geojson": geometry,
            }
        ]
    )
    profile = {
        "geoid_2020": "01001020300",
        "county_name": "Autauga County",
        "state_abbreviation": "AL",
        "tract_name": "Census Tract 203",
    }
    bounds = {str(key): value for key, value in context.iloc[0].to_dict().items()}

    figure = neighborhood_context_map_figure(profile, bounds, context)

    assert [trace.type for trace in figure.data] == ["choroplethmap", "choroplethmap"]
    assert figure.data[1].locations == ("01001020300",)


def test_place_label_keeps_geography_and_identifier_visible() -> None:
    """Search choices should not hide tract identity behind a generic place label."""

    label = place_label(
        {
            "county_name": "Autauga County",
            "state_abbreviation": "AL",
            "tract_name": "Census Tract 203",
            "geoid_2020": "01001020300",
        }
    )

    assert label == "Autauga County, AL · Census Tract 203 · 01001020300"


def test_streamlit_app_starts_in_explicit_sample_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """The committed app should render locally without Databricks credentials or mock claims."""

    monkeypatch.setenv("NEIGHBORHOOD_TWIN_DATA_MODE", "sample")
    app = AppTest.from_file(str(REPOSITORY_ROOT / "app" / "streamlit_app.py"))
    app.run(timeout=30)

    assert not app.exception
    assert app.title[0].value.startswith("A neighborhood’s history")
    assert any(
        "Forecast serving output is not published yet" in item.value for item in app.markdown
    )

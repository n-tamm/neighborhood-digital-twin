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
from neighborhood_app.charts import (
    analogue_map_figure,
    county_tract_browser_map_figure,
    forecast_interval_figure,
    forecast_validation_comparison_figure,
    hpi_history_figure,
    neighborhood_context_map_figure,
    state_browser_map_figure,
)
from neighborhood_app.ui import (
    format_currency,
    format_integer,
    format_percent,
    format_square_miles,
    place_label,
    selected_geoid_from_map_event,
    selected_rank_from_table_event,
    selected_state_from_map_event,
    tract_browser_label,
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


def test_forecast_chart_keeps_point_interval_and_baseline_distinct() -> None:
    """Both models should display uncertainty without blending into the baseline."""

    forecasts = pd.DataFrame(
        {
            "horizon_years": [1, 1, 3, 3],
            "target_end_year": [2026, 2026, 2028, 2028],
            "model_name": [
                "regularized_linear",
                "gradient_boosted_trees",
                "regularized_linear",
                "gradient_boosted_trees",
            ],
            "prediction_annualized_change_pct": [2.0, 2.4, 3.0, 3.3],
            "prediction_lower_annualized_change_pct": [-1.0, -0.5, 0.5, 0.8],
            "prediction_upper_annualized_change_pct": [5.0, 5.2, 5.5, 5.8],
            "baseline_prediction_annualized_change_pct": [1.5, 1.5, 1.8, 1.8],
        }
    )

    figure = forecast_interval_figure(forecasts)

    assert len(figure.data) == 2
    assert len(figure.data[0].x) == 4
    assert set(figure.data[0].y) == {
        "1-year · Regularized linear",
        "1-year · Gradient-boosted trees",
        "3-year · Regularized linear",
        "3-year · Gradient-boosted trees",
    }
    assert len(figure.data[0].error_x.arrayminus) == 4
    assert list(figure.data[1].x).count(1.5) == 2


def test_validation_chart_keeps_supervised_models_and_baselines_visible() -> None:
    """The evaluation view should compare model results without relabeling a baseline."""

    scorecard = pd.DataFrame(
        {
            "model_name": [
                "regularized_linear",
                "gradient_boosted_trees",
                "state_current_trend",
            ]
            * 2,
            "horizon_years": [1, 1, 1, 3, 3, 3],
            "mae_log_change": [0.077, 0.073, 0.076, 0.103, 0.081, 0.067],
        }
    )

    figure = forecast_validation_comparison_figure(scorecard)

    assert len(figure.data) == 2
    assert {trace.name for trace in figure.data} == {"1-year", "3-year"}
    assert "State trend baseline" in set(figure.data[1].y)


def test_formatters_preserve_interpretable_units() -> None:
    """Current profile metrics should carry explicit currency and percentage units."""

    assert format_currency(63939) == "$63,939"
    assert format_integer(85528) == "85,528"
    assert format_percent(0.66559, value_is_share=True) == "66.6%"
    assert format_percent(3.24) == "3.2%"
    assert format_square_miles(2_589_988.110336) == "1.0 sq mi"
    assert format_currency(None) == "Not available"


def test_context_map_combines_visible_point_with_boundary_context() -> None:
    """The main view should retain a point at high level and boundaries after zooming."""

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

    assert [trace.type for trace in figure.data] == [
        "choroplethmap",
        "choroplethmap",
        "scattermap",
    ]
    assert figure.data[1].locations == ("01001020300",)
    assert figure.data[2].marker.size == 15


def test_analogue_map_keeps_national_points_and_local_tract_outlines() -> None:
    """Historical matches must remain visible before their small polygons can be resolved."""

    geometry = (
        '{"type":"Polygon","coordinates":[['
        "[-86.5,32.4],[-86.4,32.4],[-86.4,32.5],[-86.5,32.5],[-86.5,32.4]"
        "]] }"
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
    matches = pd.DataFrame(
        [
            {
                "candidate_geoid_2020": "06001000100",
                "candidate_county_name": "Alameda County",
                "candidate_state_abbreviation": "CA",
                "candidate_origin_year": 2019,
                "candidate_longitude": -122.25,
                "candidate_latitude": 37.80,
                "candidate_geometry_geojson": geometry,
                "similarity_distance": 0.72,
                "match_rank": 1,
            }
        ]
    )

    figure = analogue_map_figure(profile, context.iloc[0].to_dict(), context, matches)

    assert [trace.type for trace in figure.data] == [
        "choroplethmap",
        "scattermap",
        "choroplethmap",
        "scattermap",
    ]
    assert figure.data[1].mode == "markers+text"
    assert figure.data[1].customdata[0][0] == 1
    assert figure.layout.map.zoom < 2.2


def test_table_selection_resolves_to_one_match_rank() -> None:
    """The county table should be the only detailed-match selection authority."""

    table = pd.DataFrame([{"Rank": 2}, {"Rank": 4}])
    table_event = {"selection": {"rows": [1]}}

    assert selected_rank_from_table_event(table_event, table) == 4


def test_geography_map_events_resolve_state_and_tract_identifiers() -> None:
    """Map navigation should accept governed state and tract identifiers only."""

    state_event = {"selection": {"points": [{"location": "MI"}]}}
    tract_event = {"selection": {"points": [{"customdata": ["26125144200", "Oakland County"]}]}}

    assert selected_state_from_map_event(state_event) == "MI"
    assert selected_geoid_from_map_event(tract_event) == "26125144200"


def test_state_browser_map_encodes_coverage_without_scoring_quality() -> None:
    """The navigation map color should describe model coverage, not neighborhood quality."""

    states = pd.DataFrame(
        [
            {
                "state_abbreviation": "MI",
                "state_name": "Michigan",
                "tract_count": 100,
                "analogue_ready_tract_count": 55,
                "analogue_ready_share": 0.55,
                "forecast_ready_tract_count": 40,
                "forecast_ready_share": 0.40,
                "forecast_3_year_ready_tract_count": 0,
                "forecast_3_year_ready_share": 0.0,
            }
        ]
    )

    figure = state_browser_map_figure(states, "MI")

    assert [trace.type for trace in figure.data] == ["choropleth", "choropleth"]
    assert figure.data[0].locations == ("MI",)
    assert figure.data[0].z == (55.00000000000001,)
    assert figure.data[0].customdata[0][3] == 40
    assert figure.data[0].customdata[0][5] == 0
    assert figure.data[1].marker.line.width == 3.2


def test_county_tract_browser_map_supports_location_first_selection() -> None:
    """County browsing should expose tract locations and identifiers without requiring a GEOID."""

    tracts = pd.DataFrame(
        [
            {
                "geoid_2020": "01001020300",
                "tract_name": "Census Tract 203",
                "county_name": "Autauga County",
                "state_abbreviation": "AL",
                "population_total_estimate": 4433,
                "forecast_available": True,
                "forecast_3_year_available": False,
                "analogue_available": True,
                "minimum_longitude": -86.48,
                "minimum_latitude": 32.45,
                "maximum_longitude": -86.45,
                "maximum_latitude": 32.49,
            },
            {
                "geoid_2020": "01001020400",
                "tract_name": "Census Tract 204",
                "county_name": "Autauga County",
                "state_abbreviation": "AL",
                "population_total_estimate": 3812,
                "forecast_available": False,
                "forecast_3_year_available": False,
                "analogue_available": True,
                "minimum_longitude": -86.45,
                "minimum_latitude": 32.47,
                "maximum_longitude": -86.42,
                "maximum_latitude": 32.51,
            },
        ]
    )

    figure = county_tract_browser_map_figure(tracts, "01001020300")

    assert [trace.type for trace in figure.data] == ["scattermap", "scattermap"]
    assert figure.data[0].customdata[0][0] == "01001020300"
    assert figure.data[0].customdata[0][2] == "Autauga County"
    assert figure.data[0].customdata[0][6] == "Unavailable"
    assert figure.data[1].marker.color == "#F2B84B"


def test_place_label_keeps_geography_and_identifier_visible() -> None:
    """Search choices should not hide tract identity behind a generic place label."""

    label = place_label(
        {
            "county_name": "Autauga County",
            "state_abbreviation": "AL",
            "tract_name": "Census Tract 203",
            "geoid_2020": "01001020300",
            "population_total_estimate": 4433,
            "forecast_available": True,
            "forecast_3_year_available": False,
            "analogue_available": True,
        }
    )

    assert label == (
        "Autauga County, AL · Census Tract 203 · 4,433 residents · 1-year forecast available · "
        "no 3-year forecast · analogues available · GEOID 01001020300"
    )


def test_tract_browser_label_explains_place_without_requiring_geoid_knowledge() -> None:
    """County tract choices should expose population and both model states in plain language."""

    label = tract_browser_label(
        {
            "tract_name": "Census Tract 203",
            "county_name": "Autauga County",
            "state_abbreviation": "AL",
            "population_total_estimate": 4433,
            "forecast_available": False,
            "forecast_3_year_available": False,
            "analogue_available": True,
        }
    )

    assert label == (
        "Autauga County, AL · Census Tract 203 · 4,433 residents · 1-year forecast — · "
        "3-year forecast — · analogues ✓"
    )


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
    assert "Data Science Results" in [tab.label for tab in app.tabs]

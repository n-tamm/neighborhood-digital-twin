"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Plotly figures for the initial Neighborhood Digital Twin application.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from typing import Any

import pandas as pd
import plotly.graph_objects as go  # type: ignore[import-untyped]

TEXT = "#E8F0F2"
NAVY = "#63B3D1"
TEAL = "#2DD4BF"
TEAL_LIGHT = "#5FB3A9"
GOLD = "#F2B84B"
ORANGE = "#F28C5B"
PURPLE = "#A78BFA"
MUTED = "#9FB0BC"
GRID = "#2A3A49"
SURFACE = "#101D2B"


def _geometry_feature(
    feature_id: str,
    geometry_json: str,
    properties: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert one stored GeoJSON geometry into a Plotly feature."""

    return {
        "type": "Feature",
        "id": feature_id,
        "properties": dict(properties or {}),
        "geometry": json.loads(geometry_json),
    }


def _bounds_geometry(bounds: Mapping[str, Any]) -> str:
    """Build a rectangular local-fixture fallback when exact geometry is unavailable."""

    minimum_longitude = float(bounds["minimum_longitude"])
    minimum_latitude = float(bounds["minimum_latitude"])
    maximum_longitude = float(bounds["maximum_longitude"])
    maximum_latitude = float(bounds["maximum_latitude"])
    coordinates = [
        [minimum_longitude, minimum_latitude],
        [maximum_longitude, minimum_latitude],
        [maximum_longitude, maximum_latitude],
        [minimum_longitude, maximum_latitude],
        [minimum_longitude, minimum_latitude],
    ]
    return json.dumps({"type": "Polygon", "coordinates": [coordinates]})


def _map_view(
    minimum_longitude: float,
    minimum_latitude: float,
    maximum_longitude: float,
    maximum_latitude: float,
    *,
    minimum_zoom: float = 0.6,
) -> dict[str, Any]:
    """Calculate a bounded MapLibre center and zoom from an extent."""

    longitude_span = max(maximum_longitude - minimum_longitude, 0.005)
    latitude_span = max(maximum_latitude - minimum_latitude, 0.005)
    visual_span = max(longitude_span, latitude_span * 1.35)
    zoom = min(12.5, max(minimum_zoom, math.log2(360.0 / visual_span) - 2.2))
    return {
        "style": "carto-darkmatter",
        "center": {
            "lon": (minimum_longitude + maximum_longitude) / 2.0,
            "lat": (minimum_latitude + maximum_latitude) / 2.0,
        },
        "zoom": zoom,
    }


def _constant_colorscale(color: str) -> list[list[Any]]:
    """Return a one-color Plotly colorscale without a visible numeric meaning."""

    return [[0.0, color], [1.0, color]]


def _selected_geometry_frame(
    profile: Mapping[str, Any],
    bounds: Mapping[str, Any],
    map_context: pd.DataFrame,
) -> pd.DataFrame:
    """Return the exact selected geometry or an explicit local-fixture extent fallback."""

    geoid = str(profile["geoid_2020"])
    if not map_context.empty and "geometry_geojson" in map_context:
        selected = map_context.loc[map_context["geoid_2020"].astype(str) == geoid]
        if not selected.empty and selected.iloc[0]["geometry_geojson"]:
            return selected.copy()
    return pd.DataFrame(
        [
            {
                "geoid_2020": geoid,
                "county_name": profile["county_name"],
                "state_abbreviation": profile["state_abbreviation"],
                "tract_name": profile["tract_name"],
                "minimum_longitude": bounds["minimum_longitude"],
                "minimum_latitude": bounds["minimum_latitude"],
                "maximum_longitude": bounds["maximum_longitude"],
                "maximum_latitude": bounds["maximum_latitude"],
                "geometry_geojson": _bounds_geometry(bounds),
            }
        ]
    )


def _layout(figure: go.Figure, *, height: int, margin_top: int = 35) -> go.Figure:
    figure.update_layout(
        height=height,
        margin={"l": 18, "r": 18, "t": margin_top, "b": 24},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, ui-sans-serif, system-ui", "color": TEXT},
        hoverlabel={"bgcolor": SURFACE, "font_color": TEXT, "bordercolor": "#395064"},
        showlegend=False,
    )
    return figure


def housing_mix_figure(profile: Mapping[str, Any]) -> go.Figure:
    """Build a single horizontal composition bar for the current housing stock."""

    labels = ["Single-family", "Multifamily", "Mobile home", "Other"]
    fields = [
        "single_family_share_estimate",
        "multifamily_share_estimate",
        "mobile_home_share_estimate",
        "other_structure_share_estimate",
    ]
    colors = [TEAL, GOLD, PURPLE, MUTED]
    figure = go.Figure()
    for label, field, color in zip(labels, fields, colors, strict=True):
        value = float(profile.get(field) or 0.0)
        figure.add_bar(
            x=[value * 100],
            y=["Current housing units"],
            name=label,
            orientation="h",
            marker_color=color,
            text=f"{label}<br>{value:.0%}" if value >= 0.08 else "",
            textposition="inside",
            hovertemplate=f"{label}: %{{x:.1f}}%<extra></extra>",
        )
    figure.update_layout(
        barmode="stack",
        xaxis={"range": [0, 100], "ticksuffix": "%", "showgrid": False, "title": None},
        yaxis={"showticklabels": False},
        showlegend=True,
        legend={"orientation": "h", "y": -0.28, "x": 0, "font": {"size": 12}},
    )
    return _layout(figure, height=235, margin_top=8)


def hpi_history_figure(history: pd.DataFrame) -> go.Figure:
    """Plot observed FHFA single-family HPI without filling unavailable years."""

    available = history.loc[history["hpi_available"].fillna(False)].copy()
    figure = go.Figure()
    figure.add_scatter(
        x=available["observation_year"],
        y=available["hpi"],
        mode="lines+markers",
        line={"color": NAVY, "width": 3},
        marker={"color": TEAL, "size": 7, "line": {"color": SURFACE, "width": 1}},
        hovertemplate="%{x}: HPI %{y:.1f}<extra></extra>",
    )
    figure.update_xaxes(showgrid=False, title=None, dtick=2)
    figure.update_yaxes(gridcolor=GRID, title="FHFA HPI", rangemode="tozero")
    return _layout(figure, height=330)


def forecast_interval_figure(forecasts: pd.DataFrame) -> go.Figure:
    """Compare approved annualized forecasts, calibrated intervals, and state-trend baselines."""

    figure = go.Figure()
    if forecasts.empty:
        return _layout(figure, height=300)
    ordered = forecasts.sort_values("horizon_years").copy()
    ordered["horizon_label"] = ordered["horizon_years"].map(
        lambda value: f"{int(value)}-year horizon"
    )
    point = ordered["prediction_annualized_change_pct"].astype(float)
    lower = ordered["prediction_lower_annualized_change_pct"].astype(float)
    upper = ordered["prediction_upper_annualized_change_pct"].astype(float)
    figure.add_scatter(
        x=point,
        y=ordered["horizon_label"],
        mode="markers",
        marker={"size": 13, "color": TEAL, "line": {"color": TEXT, "width": 1}},
        error_x={
            "type": "data",
            "symmetric": False,
            "array": upper - point,
            "arrayminus": point - lower,
            "color": TEAL_LIGHT,
            "thickness": 4,
            "width": 8,
        },
        customdata=ordered[
            [
                "prediction_lower_annualized_change_pct",
                "prediction_upper_annualized_change_pct",
                "target_end_year",
                "model_name",
            ]
        ],
        hovertemplate=(
            "Annualized forecast %{x:.1f}%<br>"
            "%{customdata[0]:.1f}% to %{customdata[1]:.1f}% interval<br>"
            "Through %{customdata[2]} · %{customdata[3]}<extra>Approved forecast</extra>"
        ),
        name="Forecast and calibrated interval",
    )
    figure.add_scatter(
        x=ordered["baseline_prediction_annualized_change_pct"],
        y=ordered["horizon_label"],
        mode="markers",
        marker={"size": 11, "color": GOLD, "symbol": "diamond"},
        hovertemplate="State-trend baseline %{x:.1f}%<extra>Baseline</extra>",
        name="State-trend baseline",
    )
    figure.add_vline(x=0, line_color=MUTED, line_width=1)
    figure.update_xaxes(
        title="Annualized FHFA HPI change",
        ticksuffix="%",
        gridcolor=GRID,
        zeroline=False,
    )
    figure.update_yaxes(title=None, showgrid=False, categoryorder="array")
    figure.update_layout(
        showlegend=True,
        legend={"orientation": "h", "y": -0.28, "x": 0},
    )
    return _layout(figure, height=340, margin_top=12)


def neighborhood_context_map_figure(
    profile: Mapping[str, Any],
    bounds: Mapping[str, Any],
    map_context: pd.DataFrame,
) -> go.Figure:
    """Show a visible selected point and boundary within nearby tract outlines."""

    selected = _selected_geometry_frame(profile, bounds, map_context)
    context = (
        map_context.dropna(subset=["geometry_geojson"]).copy()
        if "geometry_geojson" in map_context
        else pd.DataFrame()
    )
    if context.empty:
        context = selected.copy()

    features = [
        _geometry_feature(
            str(row["geoid_2020"]),
            str(row["geometry_geojson"]),
        )
        for _, row in context.iterrows()
    ]
    figure = go.Figure(
        go.Choroplethmap(
            geojson={"type": "FeatureCollection", "features": features},
            locations=context["geoid_2020"].astype(str),
            z=[0.0] * len(context),
            colorscale=_constant_colorscale("rgba(86,109,126,0.22)"),
            marker={"line": {"color": "#8FA8B8", "width": 1.15}},
            customdata=context[["geoid_2020", "county_name", "tract_name"]],
            hovertemplate=(
                "%{customdata[2]}<br>%{customdata[1]}<br>"
                "2020 tract %{location}<extra>Surrounding tract</extra>"
            ),
            showscale=False,
            name="Surrounding tracts",
        )
    )
    selected_feature = _geometry_feature(
        str(selected.iloc[0]["geoid_2020"]),
        str(selected.iloc[0]["geometry_geojson"]),
    )
    figure.add_trace(
        go.Choroplethmap(
            geojson={"type": "FeatureCollection", "features": [selected_feature]},
            locations=[str(selected.iloc[0]["geoid_2020"])],
            z=[1.0],
            colorscale=_constant_colorscale("rgba(45,212,191,0.32)"),
            marker={"line": {"color": TEAL, "width": 3.2}},
            hovertemplate=(
                f"{profile['tract_name']}<br>{profile['county_name']}, "
                f"{profile['state_abbreviation']}<br>2020 tract %{{location}}"
                "<extra>Selected neighborhood</extra>"
            ),
            showscale=False,
            name="Selected tract",
        )
    )
    selected_longitude = (
        float(selected.iloc[0]["minimum_longitude"]) + float(selected.iloc[0]["maximum_longitude"])
    ) / 2.0
    selected_latitude = (
        float(selected.iloc[0]["minimum_latitude"]) + float(selected.iloc[0]["maximum_latitude"])
    ) / 2.0
    figure.add_trace(
        go.Scattermap(
            lon=[selected_longitude],
            lat=[selected_latitude],
            mode="markers",
            marker={"size": 15, "color": TEAL},
            customdata=[[str(profile["geoid_2020"])]],
            hovertemplate=(
                f"{profile['tract_name']}<br>{profile['county_name']}, "
                f"{profile['state_abbreviation']}<extra>Selected neighborhood</extra>"
            ),
            showlegend=False,
            name="Selected neighborhood point",
        )
    )
    figure.update_layout(
        map=_map_view(
            float(context["minimum_longitude"].min()),
            float(context["minimum_latitude"].min()),
            float(context["maximum_longitude"].max()),
            float(context["maximum_latitude"].max()),
            minimum_zoom=3.0,
        ),
        showlegend=True,
        legend={
            "orientation": "h",
            "y": 0.01,
            "x": 0.01,
            "font": {"color": TEXT},
            "bgcolor": "rgba(10,22,34,.92)",
        },
    )
    return _layout(figure, height=510, margin_top=5)


def analogue_map_figure(
    profile: Mapping[str, Any],
    bounds: Mapping[str, Any],
    map_context: pd.DataFrame,
    matches: pd.DataFrame,
) -> go.Figure:
    """Layer high-visibility points over tract footprints for national-to-local review."""

    selected = _selected_geometry_frame(profile, bounds, map_context)
    query_lon = (
        float(selected.iloc[0]["minimum_longitude"]) + float(selected.iloc[0]["maximum_longitude"])
    ) / 2
    query_lat = (
        float(selected.iloc[0]["minimum_latitude"]) + float(selected.iloc[0]["maximum_latitude"])
    ) / 2
    figure = go.Figure()
    outlined = (
        matches.dropna(subset=["candidate_geometry_geojson"]).copy()
        if "candidate_geometry_geojson" in matches
        else pd.DataFrame()
    )
    located = matches.dropna(subset=["candidate_longitude", "candidate_latitude"]).copy()
    if not outlined.empty:
        match_features = [
            _geometry_feature(
                str(row["candidate_geoid_2020"]),
                str(row["candidate_geometry_geojson"]),
            )
            for _, row in outlined.iterrows()
        ]
        figure.add_trace(
            go.Choroplethmap(
                geojson={"type": "FeatureCollection", "features": match_features},
                locations=outlined["candidate_geoid_2020"].astype(str),
                z=[1.0] * len(outlined),
                colorscale=_constant_colorscale("rgba(242,184,75,0.22)"),
                marker={"line": {"color": GOLD, "width": 1.8}},
                customdata=outlined[
                    [
                        "match_rank",
                        "candidate_county_name",
                        "candidate_state_abbreviation",
                        "candidate_origin_year",
                        "similarity_distance",
                    ]
                ],
                hovertemplate=(
                    "#%{customdata[0]} %{customdata[1]}, %{customdata[2]}<br>"
                    "Historical year %{customdata[3]}<br>Distance %{customdata[4]:.3f}"
                    "<extra>Historical match</extra>"
                ),
                showscale=False,
                name="Historical matches",
            )
        )
    if not located.empty:
        figure.add_trace(
            go.Scattermap(
                lon=located["candidate_longitude"],
                lat=located["candidate_latitude"],
                mode="markers+text",
                marker={"size": 24, "color": GOLD},
                text=located["match_rank"].astype(int).astype(str),
                textposition="middle center",
                textfont={"color": "#1A1407", "size": 11, "weight": 800},
                customdata=located[
                    [
                        "match_rank",
                        "candidate_county_name",
                        "candidate_state_abbreviation",
                        "candidate_origin_year",
                        "similarity_distance",
                    ]
                ],
                hovertemplate=(
                    "#%{customdata[0]} %{customdata[1]}, %{customdata[2]}<br>"
                    "Historical year %{customdata[3]}<br>Distance %{customdata[4]:.3f}"
                    "<extra>Historical match</extra>"
                ),
                showlegend=False,
                name="Historical match points",
            )
        )
    selected_feature = _geometry_feature(
        str(selected.iloc[0]["geoid_2020"]),
        str(selected.iloc[0]["geometry_geojson"]),
    )
    figure.add_trace(
        go.Choroplethmap(
            geojson={"type": "FeatureCollection", "features": [selected_feature]},
            locations=[str(profile["geoid_2020"])],
            z=[1.0],
            colorscale=_constant_colorscale("rgba(45,212,191,0.28)"),
            marker={"line": {"color": NAVY, "width": 2.5}},
            hovertemplate=(
                f"{profile['tract_name']}<br>{profile['county_name']}, "
                f"{profile['state_abbreviation']}<br>2020 tract %{{location}}"
                "<extra>Selected neighborhood</extra>"
            ),
            showscale=False,
            name="Selected neighborhood",
        )
    )
    figure.add_trace(
        go.Scattermap(
            lon=[query_lon],
            lat=[query_lat],
            mode="markers",
            marker={"size": 18, "color": NAVY},
            customdata=[[0, profile["county_name"], profile["state_abbreviation"]]],
            hovertemplate=(
                f"{profile['tract_name']}<br>{profile['county_name']}, "
                f"{profile['state_abbreviation']}<extra>Selected neighborhood</extra>"
            ),
            showlegend=False,
            name="Selected neighborhood point",
        )
    )
    all_longitudes = [query_lon, *located["candidate_longitude"].astype(float).tolist()]
    all_latitudes = [query_lat, *located["candidate_latitude"].astype(float).tolist()]
    figure.update_layout(
        map=_map_view(
            min(all_longitudes) - 0.5,
            min(all_latitudes) - 0.35,
            max(all_longitudes) + 0.5,
            max(all_latitudes) + 0.35,
            minimum_zoom=0.6,
        ),
        showlegend=True,
        legend={
            "orientation": "h",
            "y": 0.01,
            "x": 0.01,
            "font": {"color": TEXT},
            "bgcolor": "rgba(10,22,34,.92)",
        },
    )
    return _layout(figure, height=490, margin_top=5)


def state_browser_map_figure(
    states: pd.DataFrame,
    selected_state: str | None,
) -> go.Figure:
    """Render a selectable state map with analogue color and both model coverage counts."""

    figure = go.Figure()
    if states.empty:
        return _layout(figure, height=455, margin_top=8)
    plotted = states.copy()
    if "forecast_ready_tract_count" not in plotted:
        plotted["forecast_ready_tract_count"] = 0
    if "forecast_ready_share" not in plotted:
        plotted["forecast_ready_share"] = 0.0
    plotted["analogue_ready_pct"] = plotted["analogue_ready_share"].astype(float) * 100.0
    plotted["forecast_ready_pct"] = plotted["forecast_ready_share"].astype(float) * 100.0
    figure.add_trace(
        go.Choropleth(
            locationmode="USA-states",
            locations=plotted["state_abbreviation"],
            z=plotted["analogue_ready_pct"],
            zmin=0,
            zmax=100,
            colorscale=[
                [0.0, "#203142"],
                [0.45, "#226B70"],
                [1.0, TEAL],
            ],
            marker={"line": {"color": "#07111D", "width": 1.2}},
            customdata=plotted[
                [
                    "state_name",
                    "tract_count",
                    "analogue_ready_tract_count",
                    "forecast_ready_tract_count",
                    "forecast_ready_pct",
                ]
            ],
            hovertemplate=(
                "%{customdata[0]}<br>%{customdata[2]:,} of %{customdata[1]:,} tracts "
                "support analogues (%{z:.1f}%)<br>"
                "%{customdata[3]:,} support an approved 1-year forecast "
                "(%{customdata[4]:.1f}%)<extra>Select state</extra>"
            ),
            colorbar={
                "title": {"text": "Analogue-ready<br>tract share", "font": {"color": TEXT}},
                "tickfont": {"color": TEXT},
                "ticksuffix": "%",
                "thickness": 12,
                "len": 0.62,
            },
            name="State coverage",
        )
    )
    if selected_state and selected_state in set(plotted["state_abbreviation"].astype(str)):
        figure.add_trace(
            go.Choropleth(
                locationmode="USA-states",
                locations=[selected_state],
                z=[1.0],
                colorscale=_constant_colorscale("rgba(242,184,75,0.18)"),
                marker={"line": {"color": GOLD, "width": 3.2}},
                hoverinfo="skip",
                showscale=False,
                name="Selected state",
            )
        )
    figure.update_geos(
        scope="usa",
        projection_type="albers usa",
        bgcolor="rgba(0,0,0,0)",
        showland=True,
        landcolor="#152433",
        showlakes=True,
        lakecolor="#07111D",
    )
    figure.update_layout(showlegend=False)
    return _layout(figure, height=455, margin_top=8)


def tract_outline_figure(
    geometry_geojson: str | None,
    *,
    bounds: Mapping[str, Any],
    color: str,
    hover_label: str,
) -> go.Figure:
    """Render one tract footprint at a local zoom for side-by-side shape comparison."""

    geometry = geometry_geojson or _bounds_geometry(bounds)
    feature = _geometry_feature("tract", geometry)
    figure = go.Figure(
        go.Choroplethmap(
            geojson={"type": "FeatureCollection", "features": [feature]},
            locations=["tract"],
            z=[1.0],
            colorscale=_constant_colorscale(color),
            marker={"line": {"color": NAVY, "width": 2.5}},
            hovertemplate=f"{hover_label}<extra></extra>",
            showscale=False,
        )
    )
    figure.update_layout(
        map=_map_view(
            float(bounds["minimum_longitude"]),
            float(bounds["minimum_latitude"]),
            float(bounds["maximum_longitude"]),
            float(bounds["maximum_latitude"]),
        )
    )
    return _layout(figure, height=315, margin_top=4)


def trajectory_figure(trajectories: pd.DataFrame) -> go.Figure:
    """Plot aligned observed post-match paths and keep missing annual points visible."""

    figure = go.Figure()
    if trajectories.empty:
        return _layout(figure, height=330)
    for rank, group in trajectories.groupby("match_rank", sort=True):
        rank_int = int(str(rank))
        ordered = group.sort_values("trajectory_year_offset")
        label = (
            f"#{rank_int} {ordered.iloc[0]['candidate_county_name']}, "
            f"{ordered.iloc[0]['candidate_state_abbreviation']}"
        )
        figure.add_scatter(
            x=ordered["trajectory_year_offset"],
            y=ordered["trajectory_cumulative_change_pct"],
            mode="lines+markers",
            connectgaps=False,
            name=label,
            line={
                "width": 3 if rank_int == 1 else 1.5,
                "color": NAVY if rank_int == 1 else TEAL_LIGHT,
            },
            marker={"size": 7 if rank_int == 1 else 4},
            opacity=1.0 if rank_int == 1 else 0.55,
            hovertemplate=(
                f"{label}<br>Year offset %{{x}}<br>Observed change %{{y:.1f}}%<extra></extra>"
            ),
        )
    figure.add_hline(y=0, line_color=MUTED, line_width=1)
    figure.update_xaxes(title="Years after historical match", dtick=1, showgrid=False)
    figure.update_yaxes(title="Observed cumulative FHFA HPI change", ticksuffix="%", gridcolor=GRID)
    figure.update_layout(showlegend=True, legend={"orientation": "h", "y": -0.25, "x": 0})
    return _layout(figure, height=390)


def feature_gap_figure(match: Mapping[str, Any]) -> go.Figure:
    """Show the five standardized feature-family gaps for one historical match."""

    labels = [
        "Community scale",
        "Occupancy & tenure",
        "Housing structure",
        "Affordability",
        "Recent market path",
    ]
    fields = [
        "community_scale_mean_absolute_standardized_gap",
        "occupancy_tenure_mean_absolute_standardized_gap",
        "housing_structure_mean_absolute_standardized_gap",
        "affordability_mean_absolute_standardized_gap",
        "market_trajectory_mean_absolute_standardized_gap",
    ]
    values = [float(match.get(field) or 0.0) for field in fields]
    order = sorted(range(len(values)), key=values.__getitem__, reverse=True)
    figure = go.Figure(
        go.Bar(
            x=[values[index] for index in order],
            y=[labels[index] for index in order],
            orientation="h",
            marker_color=[ORANGE if position == 0 else TEAL for position in range(len(order))],
            text=[f"{values[index]:.2f}" for index in order],
            textposition="outside",
            hovertemplate="%{y}: %{x:.3f}<extra></extra>",
        )
    )
    figure.update_xaxes(
        title="Mean absolute standardized gap",
        gridcolor=GRID,
        rangemode="tozero",
    )
    figure.update_yaxes(title=None, autorange="reversed")
    return _layout(figure, height=310)

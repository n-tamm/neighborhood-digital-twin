"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Plotly figures for the initial Neighborhood Digital Twin application.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd
import plotly.graph_objects as go  # type: ignore[import-untyped]

NAVY = "#173E4F"
TEAL = "#147D72"
TEAL_LIGHT = "#72B7AE"
GOLD = "#D49A2A"
ORANGE = "#C96A3D"
PURPLE = "#7562A8"
MUTED = "#667A76"
GRID = "#DDE5E1"


def _layout(figure: go.Figure, *, height: int, margin_top: int = 35) -> go.Figure:
    figure.update_layout(
        height=height,
        margin={"l": 18, "r": 18, "t": margin_top, "b": 24},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, ui-sans-serif, system-ui", "color": "#18312E"},
        hoverlabel={"bgcolor": "white", "font_color": "#18312E"},
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
        marker={"color": TEAL, "size": 7, "line": {"color": "white", "width": 1}},
        hovertemplate="%{x}: HPI %{y:.1f}<extra></extra>",
    )
    figure.update_xaxes(showgrid=False, title=None, dtick=2)
    figure.update_yaxes(gridcolor=GRID, title="FHFA HPI", rangemode="tozero")
    return _layout(figure, height=330)


def analogue_map_figure(
    profile: Mapping[str, Any],
    bounds: Mapping[str, Any],
    matches: pd.DataFrame,
) -> go.Figure:
    """Map the selected tract and available historical matches using display-only centers."""

    query_lon = (float(bounds["minimum_longitude"]) + float(bounds["maximum_longitude"])) / 2
    query_lat = (float(bounds["minimum_latitude"]) + float(bounds["maximum_latitude"])) / 2
    figure = go.Figure()
    usable = matches.dropna(subset=["candidate_longitude", "candidate_latitude"]).copy()
    if not usable.empty:
        figure.add_trace(
            go.Scattermap(
                lon=usable["candidate_longitude"],
                lat=usable["candidate_latitude"],
                mode="markers+text",
                text=usable["match_rank"].astype(int).astype(str),
                textposition="top center",
                marker={"size": 13, "color": GOLD, "opacity": 0.9},
                customdata=usable[
                    [
                        "candidate_county_name",
                        "candidate_state_abbreviation",
                        "candidate_origin_year",
                        "similarity_distance",
                    ]
                ],
                hovertemplate=(
                    "#%{text} %{customdata[0]}, %{customdata[1]}<br>"
                    "Historical year %{customdata[2]}<br>Distance %{customdata[3]:.3f}"
                    "<extra>Historical match</extra>"
                ),
                name="Historical matches",
            )
        )
    figure.add_trace(
        go.Scattermap(
            lon=[query_lon],
            lat=[query_lat],
            mode="markers",
            marker={"size": 19, "color": TEAL, "symbol": "circle"},
            hovertemplate=(
                f"{profile['tract_name']}<br>{profile['county_name']}, "
                f"{profile['state_abbreviation']}<extra>Selected neighborhood</extra>"
            ),
            name="Selected neighborhood",
        )
    )
    figure.update_layout(
        map={
            "style": "carto-positron",
            "center": {"lon": query_lon, "lat": query_lat},
            "zoom": 3.2 if not usable.empty else 10.5,
        },
        showlegend=True,
        legend={"orientation": "h", "y": 0.01, "x": 0.01, "bgcolor": "rgba(255,255,255,.9)"},
    )
    return _layout(figure, height=490, margin_top=5)


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

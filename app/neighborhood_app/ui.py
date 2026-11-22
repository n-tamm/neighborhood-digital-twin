"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Formatting and shared presentation helpers for the Streamlit application.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import pandas as pd
import streamlit as st


def format_integer(value: Any) -> str:
    """Format an estimated count while retaining an explicit unavailable state."""

    if value is None or pd.isna(value):
        return "Not available"
    return f"{float(value):,.0f}"


def format_currency(value: Any) -> str:
    """Format a nominal dollar estimate without implying more precision than the source."""

    if value is None or pd.isna(value):
        return "Not available"
    return f"${float(value):,.0f}"


def format_square_miles(square_meters: Any) -> str:
    """Format land area in a familiar unit without overstating boundary precision."""

    if square_meters is None or pd.isna(square_meters):
        return "Area not available"
    return f"{float(square_meters) / 2_589_988.110336:,.1f} sq mi"


def format_percent(value: Any, *, value_is_share: bool = False, digits: int = 1) -> str:
    """Format a percentage from either a proportion or a percentage-point value."""

    if value is None or pd.isna(value):
        return "Not available"
    numeric = float(value) * 100 if value_is_share else float(value)
    return f"{numeric:.{digits}f}%"


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a possibly missing display value without propagating NaN to HTML."""

    if value is None:
        return default
    numeric = float(value)
    return default if math.isnan(numeric) else numeric


def selected_rank_from_table_event(event: Any, table: pd.DataFrame) -> int | None:
    """Return the match rank represented by one selected table row."""

    selection = getattr(event, "selection", None)
    if selection is None and isinstance(event, dict):
        selection = event.get("selection", {})
    rows = getattr(selection, "rows", None)
    if rows is None and isinstance(selection, dict):
        rows = selection.get("rows", [])
    if not rows:
        return None
    row_index = int(rows[0])
    if row_index < 0 or row_index >= len(table):
        return None
    return int(table.iloc[row_index]["Rank"])


def selected_geoid_from_map_event(event: Any) -> str | None:
    """Return an eleven-digit tract GEOID from a local map-selection event."""

    selection = getattr(event, "selection", None)
    if selection is None and isinstance(event, dict):
        selection = event.get("selection", {})
    points = getattr(selection, "points", None)
    if points is None and isinstance(selection, dict):
        points = selection.get("points", [])
    for point in points or []:
        if not isinstance(point, dict):
            continue
        candidates = [point.get("location")]
        customdata = point.get("customdata")
        if isinstance(customdata, (list, tuple)) and customdata:
            candidates.insert(0, customdata[0])
        for candidate in candidates:
            geoid = str(candidate or "")
            if len(geoid) == 11 and geoid.isdigit():
                return geoid
    return None


def selected_state_from_map_event(event: Any) -> str | None:
    """Return a two-letter state abbreviation from a state-map selection event."""

    selection = getattr(event, "selection", None)
    if selection is None and isinstance(event, dict):
        selection = event.get("selection", {})
    points = getattr(selection, "points", None)
    if points is None and isinstance(selection, dict):
        points = selection.get("points", [])
    for point in points or []:
        if not isinstance(point, dict):
            continue
        abbreviation = str(point.get("location") or "").upper()
        if len(abbreviation) == 2 and abbreviation.isalpha():
            return abbreviation
    return None


def place_label(row: Mapping[str, Any]) -> str:
    """Build a readable search label with population and model availability context."""

    population = format_integer(row.get("population_total_estimate"))
    forecast = (
        "1-year forecast available"
        if bool(row.get("forecast_available"))
        else "no 1-year forecast"
    )
    forecast_3_year = (
        "3-year forecast available"
        if bool(row.get("forecast_3_year_available"))
        else "no 3-year forecast"
    )
    analogues = "analogues available" if bool(row.get("analogue_available")) else "no analogues"
    return (
        f"{row['county_name']}, {row['state_abbreviation']} · "
        f"{row['tract_name']} · {population} residents · {forecast} · {forecast_3_year} · "
        f"{analogues} · GEOID {row['geoid_2020']}"
    )


def tract_browser_label(row: Mapping[str, Any]) -> str:
    """Build one county-browser option that a user can compare without knowing a GEOID."""

    population = format_integer(row.get("population_total_estimate"))
    forecast = "1-year forecast ✓" if bool(row.get("forecast_available")) else "1-year forecast —"
    forecast_3_year = (
        "3-year forecast ✓"
        if bool(row.get("forecast_3_year_available"))
        else "3-year forecast —"
    )
    analogues = "analogues ✓" if bool(row.get("analogue_available")) else "analogues —"
    return (
        f"{row['county_name']}, {row['state_abbreviation']} · {row['tract_name']} · "
        f"{population} residents · {forecast} · {forecast_3_year} · {analogues}"
    )


def metric_card(label: str, value: str, note: str = "") -> None:
    """Render a compact, accessible current-state metric card."""

    note_html = f'<div class="metric-note">{note}</div>' if note else ""
    st.markdown(
        (
            '<div class="metric-card">'
            f'<div class="metric-label">{label}</div>'
            f'<div class="metric-value">{value}</div>'
            f"{note_html}</div>"
        ),
        unsafe_allow_html=True,
    )


def status_badge(label: str, *, available: bool) -> str:
    """Return an HTML badge that does not rely on color alone for status meaning."""

    status_class = "available" if available else "unavailable"
    symbol = "●" if available else "○"
    return f'<span class="status-badge {status_class}">{symbol} {label}</span>'


def apply_styles() -> None:
    """Apply the midnight application design without hiding accessibility controls."""

    st.markdown(
        """
        <style>
        :root {
          --ink: #e8f0f2;
          --muted: #9fb0bc;
          --teal: #2dd4bf;
          --teal-soft: #123b3b;
          --navy: #63b3d1;
          --gold: #f2b84b;
          --surface: #101d2b;
          --surface-raised: #142536;
          --line: #2a3a49;
        }
        .stApp { background: #07111d; color: var(--ink); }
        .block-container { max-width: 1500px; padding-top: 1.4rem; padding-bottom: 4rem; }
        [data-testid="stSidebar"] { background: #0b1724; border-right: 1px solid var(--line); }
        [data-testid="stSidebar"] .block-container { padding-top: 1.6rem; }
        h1, h2, h3 { color: var(--ink); letter-spacing: -0.025em; }
        h1 { font-size: clamp(2rem, 3.2vw, 3.4rem) !important; line-height: 1.02 !important; }
        h2 { margin-top: 0.3rem !important; }
        .app-kicker { color: var(--teal); font-weight: 750; letter-spacing: .11em;
                      text-transform: uppercase; font-size: .76rem; }
        .hero-copy { color: var(--muted); max-width: 880px; font-size: 1.05rem;
                     line-height: 1.55; margin-top: .55rem; }
        .place-title { font-size: 1.55rem; font-weight: 760; color: var(--ink); }
        .place-subtitle { color: var(--muted); margin-top: .15rem; }
        .metric-card { background: var(--surface); border: 1px solid var(--line);
                       border-radius: 14px; padding: 1rem 1.05rem; min-height: 112px;
                       box-shadow: 0 12px 30px rgba(0,0,0,.20); }
        .metric-label { color: var(--muted); text-transform: uppercase; font-size: .72rem;
                        letter-spacing: .07em; font-weight: 700; }
        .metric-value { color: var(--ink); font-size: 1.5rem; font-weight: 760;
                        margin-top: .28rem; line-height: 1.15; }
        .metric-note { color: var(--muted); font-size: .78rem; margin-top: .35rem; }
        .status-badge { display: inline-block; border-radius: 999px; padding: .32rem .66rem;
                        margin: .15rem .25rem .15rem 0; font-size: .78rem; font-weight: 700; }
        .status-badge.available { background: var(--teal-soft); color: #72eadb; }
        .status-badge.unavailable { background: #3a2927; color: #f1a17f; }
        .section-note { border-left: 3px solid var(--gold); padding: .75rem 1rem;
                        background: #282418; color: #e4d7b7; border-radius: 0 10px 10px 0; }
        .model-boundary { background: #102431; border: 1px solid #294655; border-radius: 14px;
                          padding: 1rem 1.1rem; }
        .sample-banner { background: #2c2617; border: 1px solid #665127; border-radius: 10px;
                         padding: .7rem .85rem; color: #eed59c; font-size: .87rem; }
        [data-testid="stPlotlyChart"] { background: var(--surface); border: 1px solid var(--line);
                                        border-radius: 14px; overflow: hidden;
                                        box-shadow: 0 12px 30px rgba(0,0,0,.18); }
        [data-baseweb="tab-list"] { gap: .35rem; }
        [data-baseweb="tab"] { border-radius: 9px 9px 0 0; padding: .65rem 1rem; }
        [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; }
        [data-testid="stForm"] { background: rgba(16,29,43,.55); border-color: var(--line); }
        @media (max-width: 800px) {
          .block-container { padding-left: 1rem; padding-right: 1rem; }
          .metric-card { min-height: 96px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

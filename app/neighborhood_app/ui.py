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


def selected_rank_from_map_event(event: Any) -> int | None:
    """Return a historical-match rank from a Plotly point-selection event."""

    selection = getattr(event, "selection", None)
    if selection is None and isinstance(event, dict):
        selection = event.get("selection", {})
    points = getattr(selection, "points", None)
    if points is None and isinstance(selection, dict):
        points = selection.get("points", [])
    for point in points or []:
        customdata = point.get("customdata") if isinstance(point, dict) else None
        if isinstance(customdata, (list, tuple)) and customdata:
            try:
                rank = int(customdata[0])
            except (TypeError, ValueError):
                continue
            if rank > 0:
                return rank
    return None


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


def place_label(row: Mapping[str, Any]) -> str:
    """Build one consistent tract label for search results and page headings."""

    return (
        f"{row['county_name']}, {row['state_abbreviation']} · "
        f"{row['tract_name']} · {row['geoid_2020']}"
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
    """Apply the first application design system without hiding Streamlit accessibility controls."""

    st.markdown(
        """
        <style>
        :root {
          --ink: #18312e;
          --muted: #667a76;
          --teal: #147d72;
          --teal-soft: #dcece8;
          --navy: #173e4f;
          --gold: #d49a2a;
          --surface: #ffffff;
          --line: #d9e2de;
        }
        .stApp { background: #f5f7f4; color: var(--ink); }
        .block-container { max-width: 1500px; padding-top: 1.4rem; padding-bottom: 4rem; }
        [data-testid="stSidebar"] { background: #eef3ef; border-right: 1px solid var(--line); }
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
                       box-shadow: 0 8px 24px rgba(23,62,79,.045); }
        .metric-label { color: var(--muted); text-transform: uppercase; font-size: .72rem;
                        letter-spacing: .07em; font-weight: 700; }
        .metric-value { color: var(--ink); font-size: 1.5rem; font-weight: 760;
                        margin-top: .28rem; line-height: 1.15; }
        .metric-note { color: var(--muted); font-size: .78rem; margin-top: .35rem; }
        .status-badge { display: inline-block; border-radius: 999px; padding: .32rem .66rem;
                        margin: .15rem .25rem .15rem 0; font-size: .78rem; font-weight: 700; }
        .status-badge.available { background: var(--teal-soft); color: #0b665c; }
        .status-badge.unavailable { background: #f4e8df; color: #8b4b2e; }
        .section-note { border-left: 3px solid var(--gold); padding: .75rem 1rem;
                        background: #fffaf0; color: #5f5a4c; border-radius: 0 10px 10px 0; }
        .model-boundary { background: #edf3f5; border: 1px solid #cfdee3; border-radius: 14px;
                          padding: 1rem 1.1rem; }
        .sample-banner { background: #fff7e6; border: 1px solid #ead39f; border-radius: 10px;
                         padding: .7rem .85rem; color: #6c582b; font-size: .87rem; }
        [data-testid="stPlotlyChart"] { background: white; border: 1px solid var(--line);
                                        border-radius: 14px; overflow: hidden;
                                        box-shadow: 0 8px 24px rgba(23,62,79,.04); }
        [data-baseweb="tab-list"] { gap: .35rem; }
        [data-baseweb="tab"] { border-radius: 9px 9px 0 0; padding: .65rem 1rem; }
        [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; }
        @media (max-width: 800px) {
          .block-container { padding-left: 1rem; padding-right: 1rem; }
          .metric-card { min-height: 96px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

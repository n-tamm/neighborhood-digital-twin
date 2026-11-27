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
from typing import Any, Literal

import pandas as pd
import streamlit as st

# These are the current-profile screening fields in neighborhood_twin.products.
# They describe ACS coverage, which is distinct from the point-in-time model inputs.
ACS_PROFILE_FEATURE_LABELS = {
    "population_total_estimate": "total population",
    "housing_units_total_estimate": "total housing units",
    "occupancy_rate_estimate": "occupancy rate",
    "vacancy_rate_estimate": "vacancy rate",
    "owner_occupancy_rate_estimate": "owner-occupancy rate",
    "renter_occupancy_rate_estimate": "renter-occupancy rate",
    "single_family_share_estimate": "single-family housing share",
    "multifamily_share_estimate": "multifamily housing share",
    "mobile_home_share_estimate": "mobile-home share",
    "median_household_income_estimate": "median household income",
    "median_owner_occupied_value_estimate": "median owner-occupied home value",
    "median_gross_rent_estimate": "median gross rent",
}


def availability_details(
    profile: Mapping[str, Any],
    history: pd.DataFrame,
    release: Mapping[str, Any],
    reason: str | None,
    *,
    product: Literal["forecast", "analogue"],
) -> list[str]:
    """Explain a missing result using the release year and verified tract evidence."""

    if reason is None or pd.isna(reason):
        return ["The current release has no coverage record for this tract and time horizon."]
    if reason == "available":
        return ["The release lists a result for this tract, but the app could not load it."]
    if reason == "horizon_failed_locked_release_gate":
        return ["This version of the forecast release did not publish this time horizon."]

    known_reasons = {
        "forecast": {"not_in_model_ready_cohort", "both_model_predictions_not_published"},
        "analogue": {
            "current_acs_unavailable",
            "insufficient_current_similarity_features",
            "fhfa_history_unavailable",
            "model_ready_market_features_unavailable",
        },
    }
    details = []
    missing_origin = False
    if reason in known_reasons[product]:
        origin = release.get("serving_as_of_year")
        if pd.notna(origin) and {"observation_year", "hpi", "hpi_available"} <= set(history):
            origin_year = int(origin)
            usable = history.loc[
                history["hpi_available"].fillna(False) & history["hpi"].gt(0).fillna(False),
                "observation_year",
            ].dropna()
            missing_origin = origin_year not in set(usable.astype(int))
            if missing_origin:
                purpose = (
                    "Both forecast models need that starting value to estimate future change."
                    if product == "forecast"
                    else "Historical matching needs that starting value to compare recent price "
                    "trends with those of earlier neighborhoods."
                )
                if usable.empty:
                    latest = "The tract has no usable FHFA index observations."
                else:
                    latest = f"The latest usable observation is from {int(usable.max())}."
                details.append(
                    f"The {origin_year} FHFA single-family home price index is missing for this "
                    f"tract. {latest} {purpose}"
                )

        if reason == "current_acs_unavailable" or (
            reason == "not_in_model_ready_cohort"
            and profile.get("has_current_acs_profile") is not None
            and pd.notna(profile["has_current_acs_profile"])
            and not profile["has_current_acs_profile"]
        ):
            details.append(
                "The app has no current American Community Survey (ACS) profile for this tract. "
                "That profile supplies the Census housing and population inputs for screening."
            )
        count = profile.get("hpi_observation_count")
        if reason == "not_in_model_ready_cohort" and pd.notna(count) and int(count) < 10:
            details.append(
                f"The forecast coverage screen requires at least 10 annual FHFA observations. "
                f"This tract has {int(count)}."
            )
        if reason == "insufficient_current_similarity_features":
            feature_count = profile.get("similarity_feature_count")
            if pd.notna(feature_count) and int(feature_count) < 8:
                details.append(
                    "The preliminary screen for historical matching needs at least 8 of 12 "
                    "Census profile measures. "
                    f"This tract has {int(feature_count)}."
                )
            for field in ("population_total_estimate", "housing_units_total_estimate"):
                value = profile.get(field)
                if pd.isna(value) or float(value) <= 0:
                    details.append(
                        "Historical matching needs a positive Census estimate for "
                        f"{ACS_PROFILE_FEATURE_LABELS[field]} to compare neighborhood size."
                    )

    if not details:
        details.append(
            "The current release did not publish this result. The coverage record does not "
            "identify a specific missing input."
        )
    if pd.notna(profile.get("acs_reference_period")):
        missing = [
            label for field, label in ACS_PROFILE_FEATURE_LABELS.items()
            if field in profile and pd.isna(profile[field])
        ]
        if missing:
            period = profile["acs_reference_period"]
            if reason == "insufficient_current_similarity_features":
                screening_note = "The preliminary profile check counts these estimates."
            elif missing_origin:
                screening_note = "The missing FHFA starting value is enough to explain the gap."
            else:
                screening_note = "The release gives no evidence that these gaps blocked the result."
            details.append(
                f"Missing estimates in the {period} Census profile include "
                f"{', '.join(missing)}. {screening_note}"
            )
    return details


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


def format_signed_percent(value: Any, *, digits: int = 1) -> str:
    """Format a display percentage with an explicit direction."""

    if value is None or pd.isna(value):
        return "Not available"
    return f"{float(value):+.{digits}f}%"


def cumulative_percent_from_log_change(value: Any) -> float | None:
    """Translate modeled cumulative log change into a user-facing percent change."""

    if value is None or pd.isna(value):
        return None
    return math.expm1(float(value)) * 100.0


def indexed_value_from_log_change(reference_value: Any, cumulative_log_change: Any) -> float | None:
    """Scale a reference amount by modeled HPI change for display only."""

    if (
        reference_value is None
        or cumulative_log_change is None
        or pd.isna(reference_value)
        or pd.isna(cumulative_log_change)
    ):
        return None
    return float(reference_value) * math.exp(float(cumulative_log_change))


def reference_amount_for_display(
    value: Any,
    *,
    fallback: float = 300_000.0,
    minimum: float = 50_000.0,
    maximum: float = 5_000_000.0,
) -> float:
    """Return a bounded housing-value reference used only for app presentation."""

    if value is None or pd.isna(value) or float(value) <= 0:
        value = fallback
    return min(max(float(value), minimum), maximum)


def forecast_series_key_html() -> str:
    """Return an always-visible key for the three forecast chart series."""

    return """
    <div class="chart-series-key" role="list" aria-label="Forecast chart legend">
      <span class="chart-series-key-title">Chart key</span>
      <span class="chart-series-key-item" role="listitem">
        <span class="chart-series-swatch chart-series-linear"></span>Regularized linear
      </span>
      <span class="chart-series-key-item" role="listitem">
        <span class="chart-series-swatch chart-series-tree"></span>Gradient-boosted trees
      </span>
      <span class="chart-series-key-item" role="listitem">
        <span class="chart-series-swatch chart-series-baseline"></span>State-trend baseline
      </span>
    </div>
    """


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
        .chart-series-key { display: flex; flex-wrap: wrap; align-items: center; gap: .55rem 1.1rem;
                            background: var(--surface); border: 1px solid var(--line);
                            border-radius: 10px; padding: .65rem .85rem; margin: .15rem 0 .55rem; }
        .chart-series-key-title { color: var(--muted); font-size: .75rem; font-weight: 750;
                                  letter-spacing: .06em; text-transform: uppercase; }
        .chart-series-key-item { display: inline-flex; align-items: center; gap: .42rem;
                                 color: var(--ink); font-size: .86rem; font-weight: 650; }
        .chart-series-swatch { display: inline-block; width: 16px; height: 11px;
                               border: 1px solid rgba(255,255,255,.45); border-radius: 2px; }
        .chart-series-linear { background: #63b3d1; }
        .chart-series-tree { background: #2dd4bf; }
        .chart-series-baseline { width: 10px; height: 10px; background: #f2b84b;
                                 transform: rotate(45deg); margin: 0 3px; }
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
          .chart-series-key { align-items: flex-start; flex-direction: column; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

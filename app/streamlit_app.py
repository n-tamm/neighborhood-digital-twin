# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd
import streamlit as st
from neighborhood_app.charts import (
    analogue_map_figure,
    feature_gap_figure,
    forecast_interval_figure,
    housing_mix_figure,
    hpi_history_figure,
    neighborhood_context_map_figure,
    state_browser_map_figure,
    tract_outline_figure,
    trajectory_figure,
)
from neighborhood_app.data import AppSettings, NeighborhoodData, create_repository
from neighborhood_app.ui import (
    apply_styles,
    format_currency,
    format_integer,
    format_percent,
    format_square_miles,
    metric_card,
    place_label,
    safe_float,
    selected_geoid_from_map_event,
    selected_rank_from_table_event,
    selected_state_from_map_event,
    status_badge,
)

st.set_page_config(
    page_title="Neighborhood Housing Intelligence",
    page_icon="⌂",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_styles()


@st.cache_resource(show_spinner=False)
def get_repository() -> Any:
    """Create one validated repository for the current application process."""

    return create_repository(AppSettings.from_environment())


@st.cache_data(ttl=900, show_spinner=False)
def search_places(search_text: str) -> pd.DataFrame:
    """Cache a bounded place search without caching credentials or connections."""

    return get_repository().search_places(search_text)


@st.cache_data(ttl=3600, show_spinner=False)
def load_states() -> pd.DataFrame:
    """Cache the compact state navigation summary for the active release."""

    return get_repository().list_states()


@st.cache_data(ttl=3600, show_spinner=False)
def load_counties(state_abbreviation: str) -> pd.DataFrame:
    """Cache counties for one state without loading neighborhood evidence."""

    return get_repository().list_counties(state_abbreviation)


@st.cache_data(ttl=3600, show_spinner=False)
def load_tracts(county_geoid: str) -> pd.DataFrame:
    """Cache tract identities for one county without loading analytical outputs."""

    return get_repository().list_tracts(county_geoid)


@st.cache_data(ttl=900, show_spinner="Loading neighborhood evidence…")
def load_neighborhood(geoid_2020: str) -> NeighborhoodData:
    """Cache one compact neighborhood view by canonical tract identifier."""

    return get_repository().load_neighborhood(geoid_2020)


def selected_summary(data: NeighborhoodData, horizon_years: int) -> dict[str, Any]:
    """Return the single published analogue summary for a selected horizon."""

    rows = data.summaries.loc[data.summaries["horizon_years"] == horizon_years]
    return rows.iloc[0].to_dict() if not rows.empty else {}


def render_overview(data: NeighborhoodData) -> None:
    """Render observed current state and housing-market history."""

    profile = data.profile
    st.subheader("Current neighborhood profile")
    st.caption(
        f"ACS {profile.get('acs_reference_period', 'reference period unavailable')} estimates. "
        "Annual ACS releases overlap because each tract value summarizes five years."
    )
    row_one = st.columns(4)
    with row_one[0]:
        metric_card(
            "Population",
            format_integer(profile.get("population_total_estimate")),
            f"±{format_integer(profile.get('population_total_moe'))} ACS margin of error",
        )
    with row_one[1]:
        metric_card(
            "Housing units",
            format_integer(profile.get("housing_units_total_estimate")),
            f"±{format_integer(profile.get('housing_units_total_moe'))} ACS margin of error",
        )
    with row_one[2]:
        metric_card(
            "Median household income",
            format_currency(profile.get("median_household_income_estimate")),
            "Nominal ACS estimate",
        )
    with row_one[3]:
        metric_card(
            "Median gross rent",
            format_currency(profile.get("median_gross_rent_estimate")),
            "Monthly ACS estimate",
        )

    composition_col, tenure_col = st.columns([1.55, 1])
    with composition_col:
        st.markdown("#### Housing composition")
        st.plotly_chart(
            housing_mix_figure(profile),
            width="stretch",
            key="overview_housing_mix",
            config={"displayModeBar": False},
        )
    with tenure_col:
        st.markdown("#### Occupancy and tenure")
        tenure = st.columns(2)
        with tenure[0]:
            metric_card(
                "Occupied",
                format_percent(profile.get("occupancy_rate_estimate"), value_is_share=True),
            )
        with tenure[1]:
            metric_card(
                "Owner occupied",
                format_percent(profile.get("owner_occupancy_rate_estimate"), value_is_share=True),
            )
        st.markdown(
            '<div class="section-note">The profile describes the full housing stock. '
            "The FHFA model and analogue outcomes below describe the single-family market "
            "only.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("#### Observed single-family housing-market history")
    st.plotly_chart(
        hpi_history_figure(data.history),
        width="stretch",
        key="overview_hpi_history",
        config={"displayModeBar": False},
    )
    st.caption(
        "FHFA tract HPI is an index of single-family price movement. It is not an individual home "
        "value or a measure of multifamily prices. Missing annual observations are not "
        "interpolated."
    )


def render_forecast_status(data: NeighborhoodData) -> None:
    """Render approved forecasts or an explicit unavailable state without substitution."""

    profile = data.profile
    st.subheader("Forecast model")
    if data.forecasts.empty:
        if not data.forecast_release:
            boundary_title = "Forecast serving output is not published yet."
            boundary_text = (
                "The forecasting workstream is still selecting the final point model and "
                "calibrating uncertainty."
            )
        else:
            reasons = (
                data.forecast_availability["availability_reason"].dropna().astype(str).unique()
                if not data.forecast_availability.empty
                else ["No availability record was published"]
            )
            boundary_title = "An approved forecast is unavailable for this tract."
            boundary_text = "Reason: " + ", ".join(reasons) + "."
        st.markdown(
            f"""
            <div class="model-boundary">
              <strong>{boundary_title}</strong><br>
              {boundary_text} This application will not substitute a validation result,
              historical analogue outcome, or fabricated number for an approved forecast.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("#### Current tract readiness")
        readiness = [
            status_badge(
                "Current ACS profile available",
                available=bool(profile.get("has_current_acs_profile")),
            ),
            status_badge(
                "FHFA history available", available=bool(profile.get("has_fhfa_history"))
            ),
            status_badge(
                "Current forecast candidate", available=bool(profile.get("forecast_candidate"))
            ),
        ]
        st.markdown(" ".join(readiness), unsafe_allow_html=True)
        return

    forecast_as_of_year = int(data.forecasts["forecast_origin_year"].max())
    st.markdown(
        f"""
        <div class="model-boundary">
          <strong>Approved tract forecast as of {forecast_as_of_year}.</strong><br>
          The point estimate and interval forecast FHFA single-family tract HPI. They are not an
          individual-home valuation, a forecast for multifamily prices, or an investment rating.
        </div>
        """,
        unsafe_allow_html=True,
    )
    cards = st.columns(len(data.forecasts))
    for card, (_, row) in zip(
        cards,
        data.forecasts.sort_values("horizon_years").iterrows(),
        strict=True,
    ):
        with card:
            metric_card(
                f"{int(row['horizon_years'])}-year annualized forecast",
                format_percent(row["prediction_annualized_change_pct"]),
                (
                    f"{format_percent(row['prediction_lower_annualized_change_pct'])} to "
                    f"{format_percent(row['prediction_upper_annualized_change_pct'])} · "
                    f"through {int(row['target_end_year'])}"
                ),
            )
    st.plotly_chart(
        forecast_interval_figure(data.forecasts),
        width="stretch",
        key="approved_forecast_intervals",
        config={"displayModeBar": False},
    )
    st.caption(
        "The diamond is the state-trend baseline. The interval is calibrated from a reserved "
        "historical year and then evaluated on a later locked test; it is not a guarantee."
    )
    first = data.forecasts.sort_values("horizon_years").iloc[0]
    st.markdown("#### What drives the model")
    st.write(str(first["driver_summary"]))
    st.info(
        "Historical analogues remain a separate evidence source. Their observed later outcomes "
        "do not set or widen this forecast interval."
    )
    st.caption(
        f"Forecast release {data.forecast_release.get('serving_release_id', 'unavailable')} · "
        f"model {first['model_name']} for the primary horizon · "
        f"nominal coverage {float(first['nominal_coverage']):.0%}"
    )


def render_analogues(data: NeighborhoodData, horizon_years: int) -> None:
    """Render historical matches as explanatory evidence, not as the primary forecast."""

    st.subheader("Historical analogues")
    st.caption(
        "Earlier communities that looked similar under the approved housing-focused "
        "representation. Their later outcomes are observed history, not a forecast for the "
        "selected tract."
    )
    availability = data.availability.loc[data.availability["horizon_years"] == horizon_years]
    if availability.empty or not bool(availability.iloc[0]["analogue_available"]):
        reason = (
            str(availability.iloc[0]["availability_reason"])
            if not availability.empty
            else "No availability record"
        )
        st.warning(f"Historical analogues are unavailable for this horizon: {reason}.")
        return

    summary = selected_summary(data, horizon_years)
    summary_columns = st.columns(4)
    with summary_columns[0]:
        metric_card(
            "Published matches",
            format_integer(summary.get("analogue_match_count")),
            "Distinct historical tracts",
        )
    with summary_columns[1]:
        metric_card(
            "Median later change",
            format_percent(summary.get("analogue_median_cumulative_change_pct")),
            f"Observed over {horizon_years} year{'s' if horizon_years > 1 else ''}",
        )
    with summary_columns[2]:
        outcome_range = (
            f"{format_percent(summary.get('analogue_outcome_p10_cumulative_change_pct'))} to "
            f"{format_percent(summary.get('analogue_outcome_p90_cumulative_change_pct'))}"
        )
        metric_card("Historical middle 80%", outcome_range, "Descriptive, not calibrated")
    with summary_columns[3]:
        metric_card(
            "Cross-state matches",
            format_percent(summary.get("cross_state_match_share"), value_is_share=True),
            "National comparison space",
        )

    matches = data.matches.loc[data.matches["horizon_years"] == horizon_years].copy()
    trajectories = data.trajectories.loc[data.trajectories["horizon_years"] == horizon_years].copy()
    map_col, list_col = st.columns([1.55, 1])
    table_event: Any = None
    table = pd.DataFrame()
    with map_col:
        st.plotly_chart(
            analogue_map_figure(data.profile, data.bounds, data.map_context, matches),
            width="stretch",
            key=f"analogue_detail_map_{horizon_years}",
            config={"displayModeBar": False},
        )
        st.caption(
            "Gold numbered points keep all matches visible nationally. Zoom in to inspect the "
            "actual tract outlines; select a county row to update the comparison below."
        )
    with list_col:
        st.markdown("#### Closest historical communities")
        if matches.empty:
            st.warning("The release summary is available, but no local match rows were loaded.")
        else:
            table = matches[
                [
                    "match_rank",
                    "candidate_county_name",
                    "candidate_state_abbreviation",
                    "candidate_origin_year",
                    "similarity_distance",
                ]
            ].rename(
                columns={
                    "match_rank": "Rank",
                    "candidate_county_name": "County",
                    "candidate_state_abbreviation": "State",
                    "candidate_origin_year": "Year",
                    "similarity_distance": "Distance",
                }
            )
            table_event = st.dataframe(
                table,
                hide_index=True,
                width="stretch",
                column_config={
                    "Distance": st.column_config.NumberColumn(format="%.3f"),
                },
                on_select="rerun",
                selection_mode="single-row",
                key=f"analogue_match_table_{horizon_years}",
            )
            st.caption("Select a county row to update the detailed comparison below.")
            if data.data_mode == "sample":
                st.caption(
                    "The local fixture retains one real match for layout testing. Live mode reads "
                    "all ten published matches from Databricks."
                )

    if matches.empty:
        return
    options = matches["match_rank"].astype(int).tolist()
    table_rank = selected_rank_from_table_event(table_event, table)
    selector_key = f"selected_analogue_rank_{horizon_years}"
    if table_rank in options:
        st.session_state[selector_key] = table_rank
    selected_rank = int(st.session_state.get(selector_key, options[0]))
    if selected_rank not in options:
        selected_rank = options[0]
        st.session_state[selector_key] = selected_rank
    selected_match = matches.loc[matches["match_rank"] == selected_rank].iloc[0].to_dict()
    selected_label = (
        f"#{selected_rank} · {selected_match['candidate_county_name']}, "
        f"{selected_match['candidate_state_abbreviation']}"
    )
    st.markdown(f"#### Inspecting {selected_label}")
    selected_geometry = data.map_context.loc[
        data.map_context.get("geoid_2020", pd.Series(dtype=str)).astype(str)
        == str(data.profile["geoid_2020"])
    ]
    candidate_geometry = selected_match.get("candidate_geometry_geojson")
    candidate_bounds_fields = {
        "minimum_longitude": selected_match.get("candidate_minimum_longitude"),
        "minimum_latitude": selected_match.get("candidate_minimum_latitude"),
        "maximum_longitude": selected_match.get("candidate_maximum_longitude"),
        "maximum_latitude": selected_match.get("candidate_maximum_latitude"),
    }
    candidate_bounds_available = all(
        value is not None and not pd.isna(value) for value in candidate_bounds_fields.values()
    )
    if candidate_geometry and candidate_bounds_available:
        st.markdown("#### Compare neighborhood footprints")
        st.caption(
            "These maps show the actual simplified tract outlines. Each panel fits its own "
            "boundary, so use the area labels—not apparent screen size—to compare scale."
        )
        query_shape, match_shape = st.columns(2)
        with query_shape:
            st.markdown("**Selected neighborhood today**")
            query_geometry = (
                str(selected_geometry.iloc[0]["geometry_geojson"])
                if not selected_geometry.empty
                else None
            )
            st.plotly_chart(
                tract_outline_figure(
                    query_geometry,
                    bounds=data.bounds,
                    color="#147D72",
                    hover_label=(
                        f"{data.profile['tract_name']} · {data.profile['county_name']}, "
                        f"{data.profile['state_abbreviation']}"
                    ),
                ),
                width="stretch",
                key=f"query_footprint_{horizon_years}_{selected_rank}",
                config={"displayModeBar": False},
            )
            st.caption(format_square_miles(data.bounds.get("land_area_sqm")))
        with match_shape:
            st.markdown(
                f"**Historical match #{selected_rank} · {selected_match['candidate_origin_year']}**"
            )
            st.plotly_chart(
                tract_outline_figure(
                    str(candidate_geometry),
                    bounds=candidate_bounds_fields,
                    color="#D49A2A",
                    hover_label=(
                        f"{selected_match['candidate_tract_name']} · "
                        f"{selected_match['candidate_county_name']}, "
                        f"{selected_match['candidate_state_abbreviation']}"
                    ),
                ),
                width="stretch",
                key=f"match_footprint_{horizon_years}_{selected_rank}",
                config={"displayModeBar": False},
            )
            st.caption(format_square_miles(selected_match.get("candidate_land_area_sqm")))

    explanation_col, detail_col = st.columns([1.35, 1])
    with explanation_col:
        st.markdown("#### Why it matched")
        st.plotly_chart(
            feature_gap_figure(selected_match),
            width="stretch",
            key=f"feature_gaps_{horizon_years}_{selected_rank}",
            config={"displayModeBar": False},
        )
    with detail_col:
        st.markdown("#### Most alike and most different")
        metric_card(
            "Strongest shared feature family",
            str(selected_match.get("strongest_shared_family_display_name", "Not available")),
            f"Standardized gap {safe_float(selected_match.get('strongest_shared_family_gap')):.2f}",
        )
        st.write("")
        metric_card(
            "Largest feature-family difference",
            str(selected_match.get("largest_difference_family_display_name", "Not available")),
            "Standardized gap "
            f"{safe_float(selected_match.get('largest_difference_family_gap')):.2f}",
        )
        st.caption(
            "Smaller gaps indicate closer model inputs. These differences explain the retrieval "
            "distance; they are not causes of later housing-price changes."
        )

    st.markdown("#### What happened afterward")
    selected_paths = trajectories.loc[trajectories["match_rank"] == selected_rank]
    st.plotly_chart(
        trajectory_figure(selected_paths),
        width="stretch",
        key=f"analogue_trajectory_{horizon_years}_{selected_rank}",
        config={"displayModeBar": False},
    )
    st.caption(
        "Observed FHFA single-family HPI path after the historical match. The app does not connect "
        "across missing intermediate observations or treat this path as the selected tract's "
        "future."
    )


def render_methods(data: NeighborhoodData) -> None:
    """Expose lineage, definitions, and limitations inside the product."""

    release = data.release
    profile = data.profile
    st.subheader("Methods, data, and limitations")
    method_col, lineage_col = st.columns([1.25, 1])
    with method_col:
        st.markdown("#### What the application currently shows")
        st.markdown(
            """
            - **Observed community profile:** ACS rolling five-year estimates for the current tract.
            - **Observed market history:** annual FHFA single-family tract HPI where available.
            - **Historical analogues:** ten earlier, distinct communities selected with weighted
              standardized distance and time-safe outcomes.
            - **Forecast:** intentionally withheld until model selection and calibrated uncertainty
              are published through a serving contract.
            """
        )
        st.markdown("#### Important boundaries")
        st.markdown(
            """
            The project does not value individual properties, rank neighborhood quality, make
            buy/sell recommendations, or claim that matched communities are causal comparisons.
            Display geometry is used only to locate places on the map—not to calculate distance,
            adjacency, or similarity.
            """
        )
    with lineage_col:
        st.markdown("#### Current release")
        lineage = {
            "Application mode": data.data_mode,
            "Analogue release": release.get("serving_release_id"),
            "Serving schema": release.get("serving_schema_version"),
            "Serving as of": release.get("serving_as_of_year"),
            "ACS release": profile.get("acs_release_year"),
            "Profile build": profile.get("product_build_id"),
            "Model-readiness build": release.get("source_model_readiness_build_id"),
            "Exact retrieval run": release.get("source_analogue_tree_run_id"),
        }
        lineage_rows = [
            {"Item": item, "Value": "Not available" if value is None else str(value)}
            for item, value in lineage.items()
        ]
        st.dataframe(
            pd.DataFrame(lineage_rows),
            hide_index=True,
            width="stretch",
        )


def render_geography_browser(profile: Mapping[str, Any]) -> None:
    """Render state-map, county, and tract navigation without loading model outputs early."""

    states = load_states()
    if states.empty:
        st.warning("State navigation is unavailable for the active release.")
        return
    state_options = set(states["state_abbreviation"].astype(str))
    current_state = str(st.session_state.get("browse_state", profile.get("state_abbreviation", "")))
    if current_state not in state_options:
        current_state = str(states.iloc[0]["state_abbreviation"])
        st.session_state["browse_state"] = current_state

    state_event = st.plotly_chart(
        state_browser_map_figure(states, current_state),
        width="stretch",
        key=f"state_browser_map_{current_state}",
        config={"displayModeBar": False},
        on_select="rerun",
        selection_mode="points",
    )
    clicked_state = selected_state_from_map_event(state_event)
    if clicked_state in state_options and clicked_state != current_state:
        st.session_state["browse_state"] = clicked_state
        st.rerun()

    state_row = states.loc[states["state_abbreviation"] == current_state].iloc[0]
    st.markdown(
        f"**{state_row['state_name']} selected** · "
        f"{int(state_row['analogue_ready_tract_count']):,} of "
        f"{int(state_row['tract_count']):,} current tracts support historical analogues"
    )
    counties = load_counties(current_state)
    if counties.empty:
        st.warning("No counties were returned for the selected state.")
        return
    county_records = counties.to_dict(orient="records")
    county_labels = {
        (
            f"{row['county_name']} · {int(row['tract_count']):,} tracts · "
            f"{int(row['analogue_ready_tract_count']):,} analogue-ready"
        ): str(row["county_geoid"])
        for row in county_records
    }
    county_label = st.selectbox(
        "County",
        options=list(county_labels),
        key=f"browse_county_{current_state}",
    )
    county_geoid = county_labels[county_label]
    tracts = load_tracts(county_geoid)
    if tracts.empty:
        st.warning("No current tracts were returned for the selected county.")
        return
    tract_records = tracts.to_dict(orient="records")
    tract_labels = {
        (
            f"{row['tract_name']} · {row['geoid_2020']}"
            + (" · analogues available" if bool(row["analogue_available"]) else "")
        ): str(row["geoid_2020"])
        for row in tract_records
    }
    tract_label = st.selectbox(
        "Neighborhood",
        options=list(tract_labels),
        key=f"browse_tract_{county_geoid}",
    )
    if st.button("Open this neighborhood", key=f"open_browse_{county_geoid}"):
        st.session_state["selected_geoid"] = tract_labels[tract_label]
        st.rerun()


def main() -> None:
    """Run the initial neighborhood explorer experience."""

    st.markdown(
        '<div class="app-kicker">Neighborhood Housing Intelligence</div>',
        unsafe_allow_html=True,
    )
    st.title("A neighborhood’s history, forecast, and historical context—kept distinct.")
    st.markdown(
        '<div class="hero-copy">Select a Census tract to explore its current housing profile, '
        "observed single-family market history, model readiness, and earlier communities that "
        "looked similar. The application shows where evidence ends instead of filling gaps with "
        "unsupported claims.</div>",
        unsafe_allow_html=True,
    )

    try:
        get_repository()
    except Exception as error:
        st.error(f"The application data contract could not be initialized: {error}")
        st.stop()

    settings = AppSettings.from_environment()
    with st.sidebar:
        st.markdown("## Explore a neighborhood")
        if settings.data_mode == "sample":
            st.markdown(
                '<div class="sample-banner"><strong>Local sample mode</strong><br>'
                "A reduced, real public-data fixture is loaded. Databricks deployment uses the "
                "complete validated release.</div>",
                unsafe_allow_html=True,
            )
        with st.form("place_search"):
            search_text = st.text_input(
                "Search by county, state, or 11-digit tract GEOID",
                value=st.session_state.get("place_search_text", "Autauga"),
                placeholder="Oakland County or 26125144200",
            )
            submitted = st.form_submit_button("Find neighborhoods", width="stretch")
        if submitted or "place_results" not in st.session_state:
            try:
                st.session_state["place_results"] = search_places(search_text)
                st.session_state["place_search_text"] = search_text
            except Exception as error:
                st.error(f"Place search failed: {error}")
                st.stop()
        results = st.session_state["place_results"]
        if results.empty:
            st.warning("No current tracts matched that search.")
            st.stop()
        option_rows = results.to_dict(orient="records")
        option_map = {place_label(row): str(row["geoid_2020"]) for row in option_rows}
        selected_label = st.selectbox(
            "Search results",
            options=list(option_map),
            key="search_result_selection",
        )
        if "selected_geoid" not in st.session_state:
            st.session_state["selected_geoid"] = option_map[selected_label]
        if st.button("Open search result", width="stretch"):
            st.session_state["selected_geoid"] = option_map[selected_label]
            st.rerun()
        selected_geoid = str(st.session_state["selected_geoid"])
        st.markdown("---")
        horizon_years = st.radio(
            "Historical outcome horizon",
            options=[1, 3],
            index=1,
            horizontal=True,
            format_func=lambda value: f"{value} year" if value == 1 else f"{value} years",
        )
        st.caption(
            "This control changes the historical analogue evidence. It does not select a forecast."
        )
        st.markdown("---")
        st.caption(
            "Use search, click a nearby tract, or browse from state to county to change place."
        )

    try:
        data = load_neighborhood(selected_geoid)
    except Exception as error:
        st.error(f"Neighborhood evidence could not be loaded: {error}")
        st.stop()

    profile = data.profile
    st.markdown(
        f'<div class="place-title">{profile["county_name"]}, {profile["state_abbreviation"]} · '
        f'{profile["tract_name"]}</div><div class="place-subtitle">2020 Census tract '
        f"{profile['geoid_2020']} · current ACS release "
        f"{profile.get('acs_release_year', '—')}</div>",
        unsafe_allow_html=True,
    )
    map_col, context_col = st.columns([1.6, 1])
    with map_col:
        map_view = st.segmented_control(
            "Map view",
            options=["Neighborhood map", "Browse U.S."],
            default="Neighborhood map",
            key="primary_map_view",
            label_visibility="collapsed",
        )
        if map_view == "Neighborhood map":
            context_event = st.plotly_chart(
                neighborhood_context_map_figure(profile, data.bounds, data.map_context),
                width="stretch",
                key=f"neighborhood_context_map_{selected_geoid}_{horizon_years}",
                config={"displayModeBar": False},
                on_select="rerun",
                selection_mode="points",
            )
            clicked_geoid = selected_geoid_from_map_event(context_event)
            if clicked_geoid and clicked_geoid != selected_geoid:
                st.session_state["selected_geoid"] = clicked_geoid
                st.rerun()
            st.caption(
                "The selected tract is outlined in teal. Select a nearby tract to open it. "
                "Simplified boundaries are for display and are not similarity inputs."
            )
        else:
            render_geography_browser(profile)
    with context_col:
        st.markdown("### Evidence at a glance")
        status_html = [
            status_badge(
                "Current profile",
                available=bool(profile.get("has_current_acs_profile")),
            ),
            status_badge("FHFA history", available=bool(profile.get("has_fhfa_history"))),
            status_badge(
                f"{horizon_years}-year analogues",
                available=data.horizon_available(horizon_years),
            ),
            status_badge(
                f"{horizon_years}-year forecast",
                available=data.forecast_horizon_available(horizon_years),
            ),
        ]
        st.markdown(" ".join(status_html), unsafe_allow_html=True)
        st.write("")
        metric_card(
            "Latest observed FHFA movement",
            format_percent(profile.get("latest_hpi_annual_change_pct")),
            f"Single-family HPI · {profile.get('latest_hpi_year', 'year unavailable')}",
        )
        st.write("")
        metric_card(
            "Single-family share",
            format_percent(profile.get("single_family_share_estimate"), value_is_share=True),
            "Share of current ACS housing units",
        )
        st.markdown(
            '<div class="section-note">A tract can have a useful profile even when one of the '
            "models is unavailable. Missing analytical results remain visible and explained.</div>",
            unsafe_allow_html=True,
        )

    overview_tab, forecast_tab, analogue_tab, methods_tab = st.tabs(
        ["Overview", "Forecast", "Historical analogues", "Methods & limitations"]
    )
    with overview_tab:
        render_overview(data)
    with forecast_tab:
        render_forecast_status(data)
    with analogue_tab:
        render_analogues(data, horizon_years)
    with methods_tab:
        render_methods(data)


main()

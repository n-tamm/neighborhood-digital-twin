# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import pandas as pd
import streamlit as st
from neighborhood_app.charts import (
    analogue_map_figure,
    county_tract_browser_map_figure,
    feature_gap_figure,
    forecast_interval_figure,
    forecast_validation_comparison_figure,
    housing_mix_figure,
    hpi_history_figure,
    neighborhood_context_map_figure,
    state_browser_map_figure,
    tract_outline_figure,
    trajectory_figure,
)
from neighborhood_app.data import AppSettings, NeighborhoodData, create_repository
from neighborhood_app.geocoding import lookup_census_tract
from neighborhood_app.ui import (
    apply_styles,
    cumulative_percent_from_log_change,
    format_currency,
    format_integer,
    format_percent,
    format_signed_percent,
    format_square_miles,
    indexed_value_from_log_change,
    metric_card,
    place_label,
    reference_amount_for_display,
    safe_float,
    selected_geoid_from_map_event,
    selected_rank_from_table_event,
    selected_state_from_map_event,
    status_badge,
    tract_browser_label,
)

APP_ROOT = Path(__file__).resolve().parent
DATA_SCIENCE_ASSET_ROOT = APP_ROOT / "assets" / "data_science"

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
    return cast(dict[str, Any], rows.iloc[0].to_dict()) if not rows.empty else {}


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
    history_reference = reference_amount_for_display(
        profile.get("median_owner_occupied_value_estimate")
    )
    st.plotly_chart(
        hpi_history_figure(data.history, reference_value=history_reference),
        width="stretch",
        key="overview_hpi_history",
        config={"displayModeBar": False},
    )
    st.caption(
        f"The left axis is observed FHFA tract HPI. The right axis is display-only dollar context: "
        f"it anchors the latest observed HPI point to the ACS median owner-occupied value "
        f"({format_currency(history_reference)}) and scales earlier index values proportionally. "
        "It is not a record of local sale prices, an individual-home value, or a multifamily "
        "measure. Missing annual HPI observations are not interpolated."
    )


def render_forecast_status(data: NeighborhoodData) -> None:
    """Render both model forecasts with plain-language context and optional detail."""

    profile = data.profile
    st.subheader("Housing market forecast")
    if data.forecasts.empty:
        reason_labels = {
            "not_in_model_ready_cohort": (
                "The tract does not have the complete FHFA history and point-in-time features "
                "required by both forecasting models."
            ),
            "both_model_predictions_not_published": (
                "A complete pair of model results was not published for this tract."
            ),
            "No availability record was published": (
                "No forecast availability record was published for this tract."
            ),
        }
        if not data.forecast_release:
            boundary_title = "Forecast data is not loaded in this app mode."
            boundary_text = (
                "The local sample demonstrates the interface but does not include the production "
                "forecast release."
            )
        else:
            reasons = (
                data.forecast_availability["availability_reason"].dropna().astype(str).unique()
                if not data.forecast_availability.empty
                else ["No availability record was published"]
            )
            boundary_title = "Model forecasts are not available for this tract."
            boundary_text = " ".join(reason_labels.get(reason, reason) for reason in reasons)
        st.markdown(
            f"""
            <div class="model-boundary">
              <strong>{boundary_title}</strong><br>
              {boundary_text} This is a data-availability limit, not a decision to hide a model
              because it performed poorly.
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
            status_badge("FHFA history available", available=bool(profile.get("has_fhfa_history"))),
            status_badge(
                "Complete forecast inputs", available=bool(profile.get("forecast_candidate"))
            ),
        ]
        st.markdown(" ".join(readiness), unsafe_allow_html=True)
        st.caption(
            "The neighborhood profile and any observed HPI history remain available on the "
            "Overview tab. The app does not replace a missing model forecast with a baseline."
        )
        return

    forecast_as_of_year = int(data.forecasts["forecast_origin_year"].max())
    st.markdown(
        f"""
        <div class="model-boundary">
          <strong>Two model views of tract-level single-family HPI change from
          {forecast_as_of_year}.</strong><br>
          Every published linear and gradient-boosted-tree result is shown. Model evaluation does
          not remove a forecast from this page.
        </div>
        """,
        unsafe_allow_html=True,
    )
    model_labels = {
        "regularized_linear": "Regularized linear",
        "gradient_boosted_trees": "Gradient-boosted trees",
    }
    horizons = sorted(data.forecasts["horizon_years"].astype(int).unique())
    cards = st.columns(len(horizons))
    for card, horizon_years in zip(cards, horizons, strict=True):
        with card:
            horizon_rows = data.forecasts.loc[
                data.forecasts["horizon_years"] == horizon_years
            ].sort_values("model_name")
            target_end_year = int(horizon_rows["target_end_year"].iloc[0])
            st.markdown(f"#### {horizon_years}-year outlook · through {target_end_year}")
            for _, row in horizon_rows.iterrows():
                cumulative_change = cumulative_percent_from_log_change(
                    row["prediction_cumulative_log_change"]
                )
                lower_change = cumulative_percent_from_log_change(
                    row["prediction_lower_cumulative_log_change"]
                )
                upper_change = cumulative_percent_from_log_change(
                    row["prediction_upper_cumulative_log_change"]
                )
                metric_card(
                    model_labels.get(str(row["model_name"]), str(row["model_name"])),
                    format_signed_percent(cumulative_change),
                    (
                        f"{format_percent(row['prediction_annualized_change_pct'])} average per "
                        f"year · range {format_signed_percent(lower_change)} to "
                        f"{format_signed_percent(upper_change)}"
                    ),
                )

    st.markdown("#### Compare the model estimates")
    st.plotly_chart(
        forecast_interval_figure(data.forecasts),
        width="stretch",
        key="supervised_forecast_intervals",
        config={"displayModeBar": False},
    )
    st.caption(
        "Bars show estimated total HPI change through each target year. Thin lines show each "
        "model's calibrated range. The gold diamond is the state-trend baseline for context. "
        "None of these values is an individual-home appraisal."
    )

    st.markdown("#### Put the HPI forecast in dollar context")
    default_reference = reference_amount_for_display(
        profile.get("median_owner_occupied_value_estimate")
    )
    reference_value = st.number_input(
        "Reference amount for illustration",
        min_value=50_000,
        max_value=5_000_000,
        value=int(round(float(default_reference) / 1_000) * 1_000),
        step=10_000,
        help=(
            "The starting value defaults to the ACS median owner-occupied value when available. "
            "It is not a model input."
        ),
        key=f"forecast_reference_value_{profile.get('geoid_2020', 'selected')}",
    )
    translated_rows = []
    for _, row in data.forecasts.sort_values(["horizon_years", "model_name"]).iterrows():
        lower_amount = format_currency(
            indexed_value_from_log_change(
                reference_value, row["prediction_lower_cumulative_log_change"]
            )
        )
        upper_amount = format_currency(
            indexed_value_from_log_change(
                reference_value, row["prediction_upper_cumulative_log_change"]
            )
        )
        translated_rows.append(
            {
                "Horizon": f"{int(row['horizon_years'])} year",
                "Model": model_labels.get(str(row["model_name"]), str(row["model_name"])),
                "Estimated market change": format_signed_percent(
                    cumulative_percent_from_log_change(row["prediction_cumulative_log_change"])
                ),
                "Illustrative end amount": format_currency(
                    indexed_value_from_log_change(
                        reference_value, row["prediction_cumulative_log_change"]
                    )
                ),
                "Illustrative 90% model range": f"{lower_amount} to {upper_amount}",
            }
        )
    st.dataframe(pd.DataFrame(translated_rows), hide_index=True, width="stretch")
    st.caption(
        "The point amount applies the model's cumulative tract-HPI change to the reference amount. "
        "The range applies that same dollar translation to the model's lower and upper 90% "
        "split-conformal bounds. It does not change the underlying model result."
    )

    with st.expander("How is the 90% model range calculated?"):
        st.markdown(
            "Each frozen model and forecast horizon has its own range. The model was scored on "
            "a reserved historical calibration period, and the finite-sample 90th percentile of "
            "its absolute tract-level errors became the amount added to and subtracted from the "
            "current point forecast. The dollar range above simply applies those HPI bounds to "
            "the selected reference amount. It reflects historical model error, not uncertainty "
            "about an individual property, and it cannot account for every future shock."
        )
        calibration_rows = (
            data.forecasts.drop_duplicates(["model_name", "horizon_years"])
            .sort_values(["horizon_years", "model_name"])
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Horizon": f"{int(row['horizon_years'])} year",
                        "Model": model_labels.get(str(row["model_name"]), str(row["model_name"])),
                        "Calibration tracts": format_integer(
                            row["calibration_observation_count"]
                        ),
                        "Target coverage": f"{float(row['nominal_coverage']):.0%}",
                    }
                    for _, row in calibration_rows.iterrows()
                ]
            ),
            hide_index=True,
            width="stretch",
        )

    with st.expander("How did the models perform in later testing?"):
        evaluation_rows = []
        evaluation = data.forecasts.drop_duplicates(["model_name", "horizon_years"]).sort_values(
            ["horizon_years", "model_name"]
        )
        for _, row in evaluation.iterrows():
            warning_labels = {
                "insufficient_later_period_observations": "Limited later-period sample",
                "worse_than_zero_change_mae": "Did not beat zero change",
                "interval_coverage_below_threshold": "Range coverage was below the project target",
            }
            warning_reasons = str(row.get("evaluation_warning_reason", "")).split(";")
            status = "Met the project checks"
            if not bool(row["meets_evaluation_thresholds"]):
                status = "; ".join(
                    warning_labels[reason]
                    for reason in warning_reasons
                    if reason in warning_labels
                ) or "Shown with an evaluation note"
            evaluation_rows.append(
                {
                    "Horizon": f"{int(row['horizon_years'])} year",
                    "Model": model_labels.get(str(row["model_name"]), str(row["model_name"])),
                    "Later-period MAE": f"{float(row['model_mae_log_change']):.3f}",
                    "Zero-change MAE": f"{float(row['zero_change_mae_log_change']):.3f}",
                    "Interval coverage": f"{float(row['empirical_interval_coverage']):.1%}",
                    "Evaluation note": status,
                }
            )
        st.dataframe(pd.DataFrame(evaluation_rows), hide_index=True, width="stretch")
        st.caption(
            "These checks describe later-period performance. They do not determine which model "
            "results are displayed above. Lower MAE is better."
        )

    first = data.forecasts.sort_values("horizon_years").iloc[0]
    with st.expander("What information influences the models?"):
        st.write(str(first["driver_summary"]))
        st.caption(
            "This is a global model finding, not a causal explanation for the selected tract. "
            "Historical analogues are a separate source of evidence."
        )
    st.caption(
        f"Forecast release {data.forecast_release.get('serving_release_id', 'unavailable')} · "
        "regularized linear and gradient-boosted trees · "
        f"nominal interval coverage {float(first['nominal_coverage']):.0%}"
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
            feature_gap_figure(cast(Mapping[str, Any], selected_match)),
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
            - **Forecasts:** regularized-linear and gradient-boosted-tree point estimates and
              model-specific calibrated intervals at one and three years where the tract is
              model-ready. Evaluation warnings remain visible when a model misses a benchmark.
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
            "Forecast release": data.forecast_release.get("serving_release_id"),
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


def _science_figure(file_name: str, caption: str) -> None:
    """Render one reviewed, source-generated analytical figure with its evidence caption."""

    figure_path = DATA_SCIENCE_ASSET_ROOT / file_name
    if not figure_path.exists():
        st.warning(f"The reviewed figure asset is unavailable: {file_name}")
        return
    st.image(str(figure_path), width="stretch")
    st.caption(caption)


def render_data_science_results() -> None:
    """Walk through the implemented data, forecast, and similarity evidence."""

    st.subheader("Data Science Results")
    st.markdown(
        "This page explains the analytical work behind the neighborhood screens. The forecast "
        "and historical analogue system answer different questions: the forecast estimates a "
        "future FHFA single-family HPI change, while analogues retrieve earlier communities that "
        "looked similar and show what happened to them afterward. Neither is a property valuation "
        "or a measure of neighborhood quality."
    )

    foundation_tab, forecasting_tab, similarity_tab = st.tabs(
        ["Data foundation", "Forecasting", "Historical analogues"]
    )
    with foundation_tab:
        st.markdown("### A longitudinal panel with an explicit geography boundary")
        st.markdown(
            "The pipeline combines annual FHFA tract HPI, 2010-2024 ACS five-year releases, and "
            "Census geography. Census redesigned many tracts in 2020, so records on either side "
            "of that change cannot all be treated as the same neighborhood. Analyses crossing "
            "the redesign use a conservative 59,607-tract stable cohort. Current profiles can "
            "use the broader 2020 tract universe. This preserves more current coverage without "
            "inventing historical continuity."
        )
        _science_figure(
            "01_tract_vintage_coverage.png",
            "Project-generated EDA figure. The stable cohort is the valid pre/post-2020 "
            "comparison subset, not a claim that other current tracts do not exist. Reproduced "
            "by the visual EDA workflow.",
        )
        st.info(
            "Why it matters: a complete national download is not the same as a complete modeling "
            "sample. Geography continuity, FHFA history, and feature availability narrow the "
            "tracts that can support a model result."
        )

    with forecasting_tab:
        st.markdown("### Comparing the two supervised forecasting models")
        st.markdown(
            "The forecast target is cumulative change in the FHFA single-family tract HPI. "
            "The project fits two models at each horizon: L2-regularized linear regression gives "
            "an interpretable additive benchmark, while gradient-boosted trees can learn nonlinear "
            "relationships and interactions. Zero change, persistence, recent growth, county "
            "trend, and state trend remain simple comparison baselines; none replaces either "
            "supervised model in the application."
        )
        validation_scorecard = pd.read_csv(
            DATA_SCIENCE_ASSET_ROOT / "forecast_validation_mae.csv"
        )
        st.plotly_chart(
            forecast_validation_comparison_figure(validation_scorecard),
            width="stretch",
            key="forecast_validation_model_comparison",
            config={"displayModeBar": False},
        )
        st.caption(
            "Validation MAE compares every method on the same cumulative-log-change target. "
            "Lower is better. The two colored supervised models are the project forecasts; trend "
            "and persistence methods are reference points."
        )
        st.markdown(
            "On validation data, gradient-boosted trees had the lower MAE of the two project "
            "models at both horizons: 0.0733 versus 0.0766 at one year, and 0.0807 versus 0.1033 "
            "at three years. The state-trend baseline was strongest at three years in this "
            "development period, which is useful context about the difficulty of the task—not a "
            "reason to redefine the baseline as the model."
        )
        comparison_table = validation_scorecard.loc[
            validation_scorecard["model_name"].isin(
                ["regularized_linear", "gradient_boosted_trees"]
            )
        ].copy()
        comparison_table["Model"] = comparison_table["model_name"].map(
            {
                "regularized_linear": "Regularized linear",
                "gradient_boosted_trees": "Gradient-boosted trees",
            }
        )
        comparison_table["Horizon"] = comparison_table["horizon_years"].map(
            lambda value: f"{int(value)} year"
        )
        comparison_table["Validation MAE"] = comparison_table["mae_log_change"].map(
            lambda value: f"{value:.4f}"
        )
        st.dataframe(
            comparison_table[["Horizon", "Model", "Validation MAE"]],
            hide_index=True,
            width="stretch",
        )
        st.info(
            "Model evaluation does not end with the validation ranking. Each supervised model is "
            "calibrated and evaluated separately on later outcomes using MAE, RMSE, signed error, "
            "tail error, interval coverage, and performance slices. Weak results stay visible "
            "with warnings instead of being replaced by a state or county trend."
        )
        _science_figure(
            "02_forecast_validation_vs_locked_mae.png",
            "The later-period evaluation keeps both supervised models visible at both horizons. "
            "Zero change and state trend are comparison baselines only. Generated by the final "
            "forecast evaluation workflow.",
        )
        st.markdown(
            "In the later period, one-year MAE was 0.0599 for gradient-boosted trees and 0.0632 "
            "for regularized linear regression. Zero change reached 0.0627 and state trend "
            "reached 0.0592, so the nonlinear model remained competitive while the linear model "
            "received a visible warning for trailing zero change. At three years, the two project "
            "models reached 0.0980 and 0.1087, clearly improving on zero change at 0.1566 and "
            "state trend at 0.2943."
        )
        _science_figure(
            "03_forecast_interval_coverage.png",
            "Observed coverage is checked separately for every model-horizon pair. One-year "
            "coverage is close to the nominal 90%; wider three-year intervals are conservative. "
            "A warning does not remove the corresponding forecast.",
        )
        _science_figure(
            "04_forecast_observed_vs_predicted.png",
            "Mean observed and predicted change makes the direction of later-period error visible. "
            "These bars summarize evaluation outcomes and are not current tract forecasts.",
        )

    with similarity_tab:
        st.markdown("### Retrieving earlier communities, not predicting with a black box")
        st.markdown(
            "For a selected tract today, the system standardizes twelve housing, demographic, "
            "economic, and market-history features using training data only. Weighted Euclidean "
            "distance then retrieves ten distinct earlier tracts whose later outcomes were "
            "already known. The selected tract itself, future information, and locked forecast "
            "test periods are excluded from the candidate pool."
        )
        _science_figure(
            "05_similarity_workflow.png",
            "The complete similarity sequence, from current features through time-safe retrieval "
            "and observed later outcomes. Generated by the similarity communication workflow.",
        )
        st.markdown(
            "Weighted standardized matching was retained over PCA because it was easier to "
            "explain feature by feature and had lower validation error at both horizons. Small "
            "weight changes preserved most top-ten matches. Removing an entire feature family "
            "changed the question enough to produce different neighborhoods, so those ablations "
            "are treated as model variants rather than minor instability."
        )
        _science_figure(
            "06_similarity_stability_and_selection.png",
            "Overlap and Jaccard measures test whether modest modeling changes preserve the "
            "neighbor list. The right-hand comparison supports weighted matching over PCA.",
        )
        _science_figure(
            "07_analogue_outcome_utility.png",
            "Analogue outcomes beat zero change, but the strongest forecast comparator performs "
            "better. That result fixes the product role: analogues provide historical evidence, "
            "not the primary forecast.",
        )
        _science_figure(
            "08_current_analogue_coverage.png",
            "The approved method returns ten matches for 46,719 of 85,528 current tracts at each "
            "supported horizon. Every other tract retains an explicit unavailable reason.",
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
    total_tracts = format_integer(state_row["tract_count"])
    analogue_tracts = format_integer(state_row["analogue_ready_tract_count"])
    forecast_tracts = format_integer(state_row.get("forecast_ready_tract_count"))
    forecast_3_year_tracts = format_integer(
        state_row.get("forecast_3_year_ready_tract_count")
    )
    st.markdown(f"**{state_row['state_name']} selected** · {total_tracts} current tracts")
    state_coverage = st.columns(3)
    with state_coverage[0]:
        metric_card("Analogues available", analogue_tracts, f"of {total_tracts} tracts")
    with state_coverage[1]:
        metric_card("1-year forecasts", forecast_tracts, f"of {total_tracts} tracts")
    with state_coverage[2]:
        metric_card(
            "3-year forecasts",
            forecast_3_year_tracts,
            f"of {total_tracts} tracts",
        )
    counties = load_counties(current_state)
    if counties.empty:
        st.warning("No counties were returned for the selected state.")
        return
    county_records = counties.to_dict(orient="records")
    county_labels = {
        (
            f"{row['county_name']} · {int(row['tract_count']):,} tracts · "
            f"{int(row['analogue_ready_tract_count']):,} analogues · "
            f"{int(row.get('forecast_ready_tract_count', 0)):,} one-year forecasts · "
            f"{int(row.get('forecast_3_year_ready_tract_count', 0)):,} three-year forecasts"
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
    st.caption(
        "Click a point to open that neighborhood. The basemap provides familiar place and road "
        "labels; the selected neighborhood's exact tract outline appears after it opens."
    )
    tract_event = st.plotly_chart(
        county_tract_browser_map_figure(tracts, str(profile.get("geoid_2020", ""))),
        width="stretch",
        key=f"county_tract_browser_{county_geoid}",
        config={"displayModeBar": False},
        on_select="rerun",
        selection_mode="points",
    )
    clicked_tract = selected_geoid_from_map_event(tract_event)
    if clicked_tract and clicked_tract != str(profile.get("geoid_2020", "")):
        st.session_state["selected_geoid"] = clicked_tract
        st.session_state.pop("selected_area_name", None)
        st.session_state.pop("selected_area_geoid", None)
        st.rerun()
    tract_records = cast(list[dict[str, Any]], tracts.to_dict(orient="records"))
    tract_labels = {tract_browser_label(row): str(row["geoid_2020"]) for row in tract_records}
    st.caption(
        "Prefer the map or address finder when you do not know a tract number. The list retains "
        "county, state, population, and model status for an accessible text alternative."
    )
    tract_label = st.selectbox(
        "Or choose a neighborhood from the list",
        options=list(tract_labels),
        key=f"browse_tract_{county_geoid}",
    )
    if st.button("Open this neighborhood", key=f"open_browse_{county_geoid}"):
        st.session_state["selected_geoid"] = tract_labels[tract_label]
        st.session_state.pop("selected_area_name", None)
        st.session_state.pop("selected_area_geoid", None)
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
        if settings.data_mode == "live":
            with st.expander("Find a neighborhood by address (recommended)", expanded=True):
                st.caption(
                    "The address is sent to the public U.S. Census Geocoder to identify its 2020 "
                    "tract. It is not written to this project's tables."
                )
                with st.form("address_lookup"):
                    address_text = st.text_input(
                        "Street address",
                        placeholder="123 Main St, Ann Arbor, MI 48104",
                    )
                    address_submitted = st.form_submit_button(
                        "Locate neighborhood",
                        width="stretch",
                    )
                if address_submitted:
                    try:
                        with st.spinner("Matching the address to Census geography…"):
                            address_match = lookup_census_tract(address_text)
                            supported = search_places(address_match.geoid_2020)
                        if supported.empty:
                            st.warning(
                                "The address matched a Census tract outside the application's "
                                "supported 50-state and Washington, D.C. release."
                            )
                        else:
                            st.session_state["selected_geoid"] = address_match.geoid_2020
                            st.session_state["selected_area_name"] = address_match.area_name
                            st.session_state["selected_area_geoid"] = address_match.geoid_2020
                            st.success(f"Matched to {address_match.display_label}")
                    except (LookupError, RuntimeError, ValueError) as error:
                        st.warning(str(error))
        else:
            st.caption("Address lookup is available in the live Databricks application.")
        with st.form("place_search"):
            search_text = st.text_input(
                "Search by county or state (tract ID optional)",
                value=st.session_state.get("place_search_text", "Autauga"),
                placeholder="Oakland County or Michigan",
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
            st.session_state.pop("selected_area_name", None)
            st.session_state.pop("selected_area_geoid", None)
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
        st.info(
            "Forecast availability is separate from the historical-analogue horizon control. "
            "Model-ready tracts provide both regularized-linear and gradient-boosted-tree results "
            "at one and three years; evaluation warnings do not hide a model output."
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
    area_name = ""
    if str(st.session_state.get("selected_area_geoid", "")) == selected_geoid:
        area_name = str(st.session_state.get("selected_area_name", "")).strip()
    place_heading = f"{profile['county_name']}, {profile['state_abbreviation']}"
    if area_name:
        place_heading = f"{area_name} · {place_heading}"
    st.markdown(
        f'<div class="place-title">{place_heading} · {profile["tract_name"]}</div>'
        f'<div class="place-subtitle">2020 Census tract {profile["geoid_2020"]} · current ACS '
        f"release {profile.get('acs_release_year', '—')}</div>",
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
                st.session_state.pop("selected_area_name", None)
                st.session_state.pop("selected_area_geoid", None)
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

    overview_tab, forecast_tab, analogue_tab, science_tab, methods_tab = st.tabs(
        [
            "Overview",
            "Forecast",
            "Historical analogues",
            "Data Science Results",
            "Methods & limitations",
        ]
    )
    with overview_tab:
        render_overview(data)
    with forecast_tab:
        render_forecast_status(data)
    with analogue_tab:
        render_analogues(data, horizon_years)
    with science_tab:
        render_data_science_results()
    with methods_tab:
        render_methods(data)


main()

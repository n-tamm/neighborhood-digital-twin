# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Render similarity communication figures
# MAGIC
# MAGIC This job turns governed analogue evaluation and serving tables into five versioned figures.
# MAGIC It does not refit the representation, retrieve new matches, inspect locked temporal tests,
# MAGIC or treat historical outcomes as causal forecasts.

# COMMAND ----------

import sys
from datetime import UTC, datetime
from pathlib import Path


def _add_repository_source() -> None:
    """Make the deployed repository package importable by this notebook."""

    for candidate in [Path.cwd(), *Path.cwd().parents]:
        source_root = candidate / "src"
        if (source_root / "neighborhood_twin").exists():
            sys.path.insert(0, str(source_root))
            return
    raise RuntimeError("Could not locate the repository src directory")


_add_repository_source()

# COMMAND ----------

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import PercentFormatter
from plotly.subplots import make_subplots
from pyspark.sql import functions
from shapely import wkb

from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.similarity_visuals import (
    DEFAULT_CASE_HORIZON_YEARS,
    DEFAULT_CASE_QUERY_GEOID,
    DEFAULT_CASE_TOP_K,
    SIMILARITY_FIGURE_SPECS,
    figure_spec,
    validate_case_records,
    validate_figure_manifest_records,
    validate_selection_methods,
)

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("silver_schema", "neighborhood_twin_silver", "Silver schema")
dbutils.widgets.text("evaluation_schema", "neighborhood_twin_evaluation", "Evaluation schema")
dbutils.widgets.text("serving_schema", "neighborhood_twin_serving", "Serving schema")
dbutils.widgets.text(
    "stability_table", "historical_analogue_stability_summary", "Stability evidence"
)
dbutils.widgets.text(
    "selection_scorecard_table",
    "historical_analogue_selection_scorecard",
    "Selection scorecard",
)
dbutils.widgets.text("tree_scale_table", "analogue_tree_scale_benchmark", "Tree scale evidence")
dbutils.widgets.text("release_manifest_table", "serving_release_manifest", "Serving manifest")
dbutils.widgets.text("availability_table", "serving_analogue_availability_current", "Availability")
dbutils.widgets.text("match_table", "serving_analogue_match_current", "Current matches")
dbutils.widgets.text(
    "explanation_table", "serving_analogue_explanation_current", "Match explanations"
)
dbutils.widgets.text(
    "trajectory_table", "serving_analogue_trajectory_current", "Observed trajectories"
)
dbutils.widgets.text(
    "geometry_table", "silver_tract_display_geometry_2020", "Display-only tract geometry"
)
dbutils.widgets.text(
    "figure_volume", "similarity_evaluation_figures", "Similarity figure volume"
)
dbutils.widgets.text(
    "figure_manifest_table",
    "similarity_evaluation_figure_manifest",
    "Similarity figure manifest",
)
dbutils.widgets.text("case_query_geoid", DEFAULT_CASE_QUERY_GEOID, "Case-study query GEOID")
dbutils.widgets.text(
    "case_horizon_years", str(DEFAULT_CASE_HORIZON_YEARS), "Case-study outcome horizon"
)
dbutils.widgets.text("case_top_k", str(DEFAULT_CASE_TOP_K), "Case-study match count")

catalog = dbutils.widgets.get("catalog").strip()
silver_schema = dbutils.widgets.get("silver_schema").strip()
evaluation_schema = dbutils.widgets.get("evaluation_schema").strip()
serving_schema = dbutils.widgets.get("serving_schema").strip()
stability_table = dbutils.widgets.get("stability_table").strip()
selection_scorecard_table = dbutils.widgets.get("selection_scorecard_table").strip()
tree_scale_table = dbutils.widgets.get("tree_scale_table").strip()
release_manifest_table = dbutils.widgets.get("release_manifest_table").strip()
availability_table = dbutils.widgets.get("availability_table").strip()
match_table = dbutils.widgets.get("match_table").strip()
explanation_table = dbutils.widgets.get("explanation_table").strip()
trajectory_table = dbutils.widgets.get("trajectory_table").strip()
geometry_table = dbutils.widgets.get("geometry_table").strip()
figure_volume = dbutils.widgets.get("figure_volume").strip()
figure_manifest_table = dbutils.widgets.get("figure_manifest_table").strip()
case_query_geoid = dbutils.widgets.get("case_query_geoid").strip()
case_horizon_years = int(dbutils.widgets.get("case_horizon_years"))
case_top_k = int(dbutils.widgets.get("case_top_k"))
if len(case_query_geoid) != 11 or not case_query_geoid.isdigit():
    raise ValueError("The case-study GEOID must contain exactly eleven digits")
if case_horizon_years not in {1, 3} or case_top_k != 10:
    raise ValueError("The communication contract supports horizons 1 or 3 and exactly ten matches")

# COMMAND ----------


def _single_string(frame, column: str, label: str) -> str:
    """Return one nonempty lineage value or stop publication."""

    values = [str(row[column]) for row in frame.select(column).distinct().collect()]
    if len(values) != 1 or not values[0]:
        raise RuntimeError(f"{label} must contain exactly one current {column}")
    return values[0]


stability = spark.table(qualified_name(catalog, evaluation_schema, stability_table))
scorecard = spark.table(qualified_name(catalog, evaluation_schema, selection_scorecard_table))
tree_scale = spark.table(qualified_name(catalog, evaluation_schema, tree_scale_table))
release_manifest = spark.table(
    qualified_name(catalog, serving_schema, release_manifest_table)
)
availability_all = spark.table(qualified_name(catalog, serving_schema, availability_table))
matches_all = spark.table(qualified_name(catalog, serving_schema, match_table))
explanations_all = spark.table(qualified_name(catalog, serving_schema, explanation_table))
trajectories_all = spark.table(qualified_name(catalog, serving_schema, trajectory_table))
geometry = spark.table(qualified_name(catalog, silver_schema, geometry_table))

audit_run_id = _single_string(stability, "analogue_audit_run_id", "Stability table")
selection_run_id = _single_string(
    scorecard, "analogue_selection_run_id", "Selection scorecard"
)
tree_run_id = _single_string(tree_scale, "analogue_tree_run_id", "Tree scale table")

complete_releases = (
    release_manifest.where(
        (functions.col("serving_schema_version") == "1.1.0")
        & (functions.col("release_status") == "validated")
    )
    .groupBy("serving_release_id", "serving_built_at_utc")
    .agg(functions.countDistinct("table_name").alias("manifest_table_count"))
    .where(functions.col("manifest_table_count") == 5)
    .orderBy(functions.col("serving_built_at_utc").desc())
)
release_row = complete_releases.first()
if release_row is None:
    raise RuntimeError("No complete schema-1.1 analogue serving release is available")
serving_release_id = str(release_row["serving_release_id"])
availability = availability_all.where(
    functions.col("serving_release_id") == serving_release_id
)
matches = matches_all.where(functions.col("serving_release_id") == serving_release_id)
explanations = explanations_all.where(
    functions.col("serving_release_id") == serving_release_id
)
trajectories = trajectories_all.where(
    functions.col("serving_release_id") == serving_release_id
)

# COMMAND ----------

build_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
built_at_utc = datetime.now(UTC).isoformat()
spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{evaluation_schema}`.`{figure_volume}`")
figure_directory = (
    Path("/Volumes")
    / catalog
    / evaluation_schema
    / figure_volume
    / f"build_id={build_id}"
)
figure_directory.mkdir(parents=True, exist_ok=False)

TEXT = "#24323D"
MUTED = "#607480"
GRID = "#DCE5E9"
NAVY = "#24527A"
TEAL = "#2A7F76"
GOLD = "#D79A2B"
ORANGE = "#C96D3A"
PURPLE = "#7562A8"
LIGHT = "#EFF4F6"

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": GRID,
        "axes.labelcolor": TEXT,
        "axes.titlecolor": TEXT,
        "axes.titleweight": "semibold",
        "font.size": 10,
        "text.color": TEXT,
        "xtick.color": TEXT,
        "ytick.color": TEXT,
    }
)

manifest_records: list[dict[str, object]] = []


def _manifest_record(sequence: int, path: Path) -> dict[str, object]:
    """Build one lineage-complete manifest row after a figure exists on disk."""

    spec = figure_spec(sequence)
    return {
        "similarity_figure_build_id": build_id,
        "similarity_figure_built_at_utc": built_at_utc,
        "figure_sequence": sequence,
        "figure_file_name": spec.file_name,
        "figure_title": spec.title,
        "figure_purpose": spec.purpose,
        "figure_path": str(path),
        "byte_size": path.stat().st_size,
        "source_analogue_audit_run_id": audit_run_id,
        "source_analogue_selection_run_id": selection_run_id,
        "source_analogue_tree_run_id": tree_run_id,
        "source_serving_release_id": serving_release_id,
        "case_query_geoid_2020": case_query_geoid,
        "case_horizon_years": case_horizon_years,
    }


def save_matplotlib(sequence: int, figure) -> None:
    """Save one Matplotlib figure and stage its manifest row."""

    path = figure_directory / figure_spec(sequence).file_name
    figure.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    manifest_records.append(_manifest_record(sequence, path))


def add_note(figure, note: str) -> None:
    """Add a consistent interpretation and lineage note below a figure."""

    figure.text(0.01, 0.012, note, ha="left", va="bottom", fontsize=8.3, color=MUTED)


def clean_axis(axis, *, grid_axis: str = "y") -> None:
    """Apply the shared restrained axis treatment."""

    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis=grid_axis, color=GRID, linewidth=0.8)
    axis.set_axisbelow(True)


# COMMAND ----------

# Figure 1: method flow
figure, axis = plt.subplots(figsize=(15, 8.2))
axis.set_xlim(0, 15)
axis.set_ylim(0, 8)
axis.axis("off")
stages = [
    (
        0.4,
        4.75,
        "1  Point-in-time state",
        (
            "Community scale\nOccupancy and tenure\nHousing structure\n"
            "Affordability\nRecent market trajectory"
        ),
        NAVY,
    ),
    (
        4.0,
        4.75,
        "2  Training-only fit",
        "Median imputation\nStandardization\nEqual family influence\nNo future information",
        TEAL,
    ),
    (
        7.6,
        4.75,
        "3  Time-safe candidates",
        (
            "Earlier tract-year states\nOutcome known by query year\n"
            "Locked test excluded\nQuery tract excluded"
        ),
        PURPLE,
    ),
    (
        11.2,
        4.75,
        "4  Exact retrieval",
        (
            "KD-tree search\nWeighted Euclidean distance\n"
            "Ten distinct communities\nRanked nearest first"
        ),
        ORANGE,
    ),
    (
        4.0,
        1.0,
        "5  Explain and look forward",
        (
            "Shared and different feature families\nObserved later FHFA path\n"
            "Descriptive outcome range\nCoverage warnings"
        ),
        GOLD,
    ),
    (
        8.0,
        1.0,
        "6  Application evidence",
        (
            "Earlier places that looked similar\nWhat happened afterward\n"
            "Secondary context beside forecast\nNever a causal or buy/sell claim"
        ),
        NAVY,
    ),
]
for x, y, title, body, color in stages:
    width = 3.25 if y > 4 else 3.7
    box = FancyBboxPatch(
        (x, y),
        width,
        2.25,
        boxstyle="round,pad=0.03,rounding_size=0.12",
        facecolor="white",
        edgecolor=color,
        linewidth=2,
    )
    axis.add_patch(box)
    axis.text(x + 0.18, y + 1.85, title, fontsize=11.5, fontweight="bold", color=color)
    axis.text(x + 0.18, y + 1.55, body, fontsize=9.4, va="top", linespacing=1.35)
for start, end in ((3.65, 4.0), (7.25, 7.6), (10.85, 11.2)):
    axis.annotate(
        "",
        xy=(end, 5.88),
        xytext=(start, 5.88),
        arrowprops={"arrowstyle": "-|>", "color": MUTED, "lw": 1.8},
    )
axis.annotate(
    "",
    xy=(5.85, 3.25),
    xytext=(12.8, 4.75),
    arrowprops={"arrowstyle": "-|>", "color": MUTED, "lw": 1.8},
)
axis.annotate(
    "",
    xy=(8.0, 2.12),
    xytext=(7.7, 2.12),
    arrowprops={"arrowstyle": "-|>", "color": MUTED, "lw": 1.8},
)
axis.text(
    0.4,
    7.55,
    "How a current neighborhood is matched with earlier communities",
    fontsize=19,
    fontweight="bold",
)
axis.text(
    0.4,
    7.18,
    (
        "The method retrieves historical evidence; it does not assume that the selected tract "
        "will repeat it."
    ),
    fontsize=11,
    color=MUTED,
)
add_note(
    figure,
    "Governed workflow used by jobs 601-604 and 700. Training-only preprocessing and time-safe "
    "outcomes prevent future information from entering retrieval.",
)
save_matplotlib(1, figure)

# COMMAND ----------

# Figure 2: stability and representation choice
stability_pdf = stability.select(
    "perturbation_kind", "top_k_overlap_share", "top_three_retention_share"
).toPandas()
overall_scorecard = scorecard.where(functions.col("slice_name") == "overall")
available_methods = [
    str(row["prediction_method"])
    for row in overall_scorecard.select("prediction_method").distinct().collect()
]
validate_selection_methods(available_methods)
scorecard_pdf = overall_scorecard.select(
    "horizon_years", "prediction_method", "mae_log_change"
).toPandas()

kind_order = [
    "small_weight_change",
    "candidate_uniqueness",
    "pca_component_count",
    "family_ablation",
]
kind_labels = [
    "Small weight\nchanges",
    "Distinct-tract\nrule",
    "PCA dimension\nchanges",
    "Remove one\nfeature family",
]
figure, axes = plt.subplots(1, 2, figsize=(15, 6.8), gridspec_kw={"width_ratios": [1.15, 0.85]})
box_values = [
    stability_pdf.loc[stability_pdf["perturbation_kind"] == kind, "top_k_overlap_share"].to_numpy()
    for kind in kind_order
]
box = axes[0].boxplot(
    box_values,
    tick_labels=kind_labels,
    patch_artist=True,
    widths=0.58,
    showfliers=False,
    medianprops={"color": TEXT, "linewidth": 1.8},
)
for patch, color in zip(box["boxes"], [TEAL, NAVY, PURPLE, ORANGE], strict=True):
    patch.set_facecolor(color)
    patch.set_alpha(0.84)
axes[0].set_ylim(0, 1.03)
axes[0].yaxis.set_major_formatter(PercentFormatter(1.0))
axes[0].set_ylabel("Share of the original top ten retained")
axes[0].set_title("Minor weight changes are stable; removing a family is not")
clean_axis(axes[0])
axes[0].text(
    0.02,
    0.03,
    "Ablations and PCA changes are stress tests,\nnot equivalent small perturbations.",
    transform=axes[0].transAxes,
    fontsize=8.5,
    color=MUTED,
)

method_order = [
    "analogue_inverse_distance_weighted_standardized",
    "analogue_inverse_distance_pca",
]
method_labels = ["Weighted standardized", "PCA"]
horizons = [1, 3]
x_positions = np.arange(len(horizons))
for index, (method, label, color) in enumerate(
    zip(method_order, method_labels, [NAVY, TEAL], strict=True)
):
    values = [
        float(
            scorecard_pdf.loc[
                (scorecard_pdf["prediction_method"] == method)
                & (scorecard_pdf["horizon_years"] == horizon),
                "mae_log_change",
            ].iloc[0]
        )
        for horizon in horizons
    ]
    bars = axes[1].bar(
        x_positions + (-0.19 if index == 0 else 0.19),
        values,
        width=0.38,
        label=label,
        color=color,
    )
    axes[1].bar_label(bars, fmt="%.3f", padding=3, fontsize=9)
axes[1].set_xticks(x_positions, ["1-year outcome", "3-year outcome"])
axes[1].set_ylabel("Mean absolute cumulative log-change error")
axes[1].set_title("Weighted matching also performs better than PCA")
axes[1].legend(frameon=False, loc="upper left")
clean_axis(axes[1])
figure.suptitle(
    "Weighted standardized matching is the most defensible application default",
    fontsize=17,
    fontweight="bold",
    y=0.99,
)
add_note(
    figure,
    "Validation evidence only. Lower MAE is better. Stability shows neighbor-list sensitivity; "
    "it does not prove that matches are true causal peers.",
)
figure.subplots_adjust(bottom=0.18, wspace=0.28)
save_matplotlib(2, figure)

# COMMAND ----------

# Figure 3: later-outcome utility
utility_methods = [
    "zero_change",
    "state_current_trend",
    "regularized_linear",
    "analogue_median_weighted_standardized",
    "analogue_inverse_distance_weighted_standardized",
]
utility_labels = [
    "Zero change",
    "State trend",
    "Regularized linear",
    "Analogue median",
    "Analogue distance-weighted",
]
utility_colors = ["#9AA6AC", TEAL, NAVY, GOLD, ORANGE]
figure, axis = plt.subplots(figsize=(13.5, 7))
width = 0.15
for index, (method, label, color) in enumerate(
    zip(utility_methods, utility_labels, utility_colors, strict=True)
):
    values = [
        float(
            scorecard_pdf.loc[
                (scorecard_pdf["prediction_method"] == method)
                & (scorecard_pdf["horizon_years"] == horizon),
                "mae_log_change",
            ].iloc[0]
        )
        for horizon in horizons
    ]
    offset = (index - 2) * width
    bars = axis.bar(x_positions + offset, values, width=width, color=color, label=label)
    axis.bar_label(bars, fmt="%.3f", padding=2, fontsize=8, rotation=90)
axis.set_xticks(x_positions, ["1-year later outcome", "3-year later outcome"])
axis.set_ylabel("Mean absolute cumulative log-change error")
axis.set_title("Analogues beat zero change, but not the stronger forecast comparators")
axis.legend(frameon=False, ncol=3, loc="upper left")
axis.set_ylim(0, max(scorecard_pdf["mae_log_change"].astype(float)) * 1.08)
clean_axis(axis)
axis.text(
    0.99,
    0.96,
    "Lower is better",
    transform=axis.transAxes,
    ha="right",
    va="top",
    fontsize=9,
    color=MUTED,
)
add_note(
    figure,
    "Expanded validation queries from job 602; identical rows are used for every method. "
    "Historical "
    "analogues remain descriptive context and a secondary estimate, not the primary forecast.",
)
figure.subplots_adjust(bottom=0.16)
save_matplotlib(3, figure)

# COMMAND ----------

# Figure 4: current national coverage
coverage_pdf = (
    availability.groupBy("horizon_years", "availability_reason")
    .count()
    .orderBy("horizon_years", "availability_reason")
    .toPandas()
)
reason_order = [
    "available",
    "model_ready_market_features_unavailable",
    "fhfa_history_unavailable",
    "insufficient_current_similarity_features",
    "current_acs_unavailable",
]
reason_labels = {
    "available": "Available",
    "model_ready_market_features_unavailable": "Market features unavailable",
    "fhfa_history_unavailable": "FHFA history unavailable",
    "insufficient_current_similarity_features": "Similarity features unavailable",
    "current_acs_unavailable": "Current ACS profile unavailable",
}
reason_colors = {
    "available": TEAL,
    "model_ready_market_features_unavailable": GOLD,
    "fhfa_history_unavailable": ORANGE,
    "insufficient_current_similarity_features": PURPLE,
    "current_acs_unavailable": "#9AA6AC",
}
figure, axis = plt.subplots(figsize=(13.5, 6.8))
left = np.zeros(2)
totals = []
for horizon in horizons:
    totals.append(
        int(coverage_pdf.loc[coverage_pdf["horizon_years"] == horizon, "count"].sum())
    )
for reason in reason_order:
    values = np.array(
        [
            int(
                coverage_pdf.loc[
                    (coverage_pdf["horizon_years"] == horizon)
                    & (coverage_pdf["availability_reason"] == reason),
                    "count",
                ].iloc[0]
            )
            for horizon in horizons
        ]
    )
    bars = axis.barh(
        ["1-year analogues", "3-year analogues"],
        values,
        left=left,
        color=reason_colors[reason],
        label=reason_labels[reason],
        height=0.52,
    )
    if reason == "available":
        for bar, value, total in zip(bars, values, totals, strict=True):
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_y() + bar.get_height() / 2,
                f"{value:,}\n({value / total:.1%})",
                ha="center",
                va="center",
                color="white",
                fontweight="bold",
            )
    left += values
axis.set_xlabel("Canonical current census tracts")
axis.set_title("About 55% of current tracts support the full historical analogue method")
axis.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.16))
axis.xaxis.set_major_formatter(lambda value, _position: f"{value / 1000:,.0f}k")
clean_axis(axis, grid_axis="x")
axis.text(
    0.99,
    0.50,
    "The same current representation supports both horizons,\nso their eligibility counts match.",
    transform=axis.transAxes,
    ha="right",
    va="center",
    fontsize=9,
    color=MUTED,
    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.94, "pad": 4},
)
add_note(
    figure,
    "The application retains all 85,528 tract-horizon availability rows and must show the stored "
    "reason when a complete result is unavailable. It must not silently switch methods.",
)
figure.subplots_adjust(bottom=0.25)
save_matplotlib(4, figure)

# COMMAND ----------

# Figure 5: governed Michigan case study
case_matches_frame = matches.where(
    (functions.col("query_geoid_2020") == case_query_geoid)
    & (functions.col("horizon_years") == case_horizon_years)
).orderBy("match_rank")
case_explanations_frame = explanations.where(
    (functions.col("query_geoid_2020") == case_query_geoid)
    & (functions.col("horizon_years") == case_horizon_years)
).orderBy("match_rank")
case_trajectories_frame = trajectories.where(
    (functions.col("query_geoid_2020") == case_query_geoid)
    & (functions.col("horizon_years") == case_horizon_years)
).orderBy("match_rank", "trajectory_year_offset")

case_matches = [row.asDict(recursive=True) for row in case_matches_frame.collect()]
case_explanations = [row.asDict(recursive=True) for row in case_explanations_frame.collect()]
case_trajectories = [row.asDict(recursive=True) for row in case_trajectories_frame.collect()]
validate_case_records(
    case_matches,
    case_explanations,
    case_trajectories,
    horizon_years=case_horizon_years,
    top_k=case_top_k,
)

case_geoids = [case_query_geoid, *[str(row["candidate_geoid_2020"]) for row in case_matches]]
geometry_rows = geometry.where(functions.col("geoid_2020").isin(case_geoids)).select(
    "geoid_2020", "geometry_wkb"
).collect()
centroids = {}
for row in geometry_rows:
    shape = wkb.loads(bytes(row["geometry_wkb"]))
    point = shape.representative_point()
    centroids[str(row["geoid_2020"])] = (float(point.x), float(point.y))
if set(centroids) != set(case_geoids):
    raise RuntimeError("The case-study map is missing one or more display-only tract geometries")

query_row = case_matches[0]
query_label = (
    f"{query_row['query_county_name']}, {query_row['query_state_abbreviation']} "
    f"({query_row['query_tract_name']})"
)
case_figure = make_subplots(
    rows=2,
    cols=2,
    specs=[[{"type": "geo"}, {"type": "xy"}], [{"type": "xy", "colspan": 2}, None]],
    column_widths=[0.58, 0.42],
    row_heights=[0.48, 0.52],
    horizontal_spacing=0.08,
    vertical_spacing=0.15,
    subplot_titles=(
        "Ten matches span ten states",
        "Closest match: feature-family gaps",
        "Observed FHFA paths after each historical match",
    ),
)

query_lon, query_lat = centroids[case_query_geoid]
case_figure.add_trace(
    go.Scattergeo(
        lon=[query_lon],
        lat=[query_lat],
        text=[f"Selected: {query_label}"],
        mode="markers",
        marker={"size": 16, "color": "#C43C39", "symbol": "star", "line": {"width": 1}},
        name="Selected neighborhood",
        hovertemplate="%{text}<extra></extra>",
    ),
    row=1,
    col=1,
)
candidate_lons = [centroids[str(row["candidate_geoid_2020"])][0] for row in case_matches]
candidate_lats = [centroids[str(row["candidate_geoid_2020"])][1] for row in case_matches]
candidate_text = [
    (
        f"#{row['match_rank']} {row['candidate_county_name']}, "
        f"{row['candidate_state_abbreviation']}<br>"
        f"Origin {row['candidate_origin_year']}"
    )
    for row in case_matches
]
case_figure.add_trace(
    go.Scattergeo(
        lon=candidate_lons,
        lat=candidate_lats,
        mode="markers+text",
        text=[str(row["match_rank"]) for row in case_matches],
        textposition="top center",
        marker={
            "size": 10,
            "color": [int(row["match_rank"]) for row in case_matches],
            "colorscale": "Blues",
            "reversescale": True,
            "showscale": False,
            "line": {"width": 0.8, "color": "white"},
        },
        name="Historical matches",
        hovertemplate="%{customdata}<extra></extra>",
        customdata=candidate_text,
    ),
    row=1,
    col=1,
)

top_explanation = case_explanations[0]
family_fields = [
    ("community_scale_mean_absolute_standardized_gap", "Community scale"),
    ("occupancy_tenure_mean_absolute_standardized_gap", "Occupancy and tenure"),
    ("housing_structure_mean_absolute_standardized_gap", "Housing structure"),
    ("affordability_mean_absolute_standardized_gap", "Affordability"),
    ("market_trajectory_mean_absolute_standardized_gap", "Recent market trajectory"),
]
family_fields = sorted(family_fields, key=lambda item: float(top_explanation[item[0]]))
case_figure.add_trace(
    go.Bar(
        x=[float(top_explanation[field]) for field, _label in family_fields],
        y=[label for _field, label in family_fields],
        orientation="h",
        marker={"color": [TEAL, "#62A69E", GOLD, ORANGE, PURPLE]},
        text=[f"{float(top_explanation[field]):.2f}" for field, _label in family_fields],
        textposition="outside",
        name="Mean standardized gap",
        hovertemplate="%{y}: %{x:.3f}<extra></extra>",
    ),
    row=1,
    col=2,
)

path_matrix = []
for match in case_matches:
    rank = int(match["match_rank"])
    path = [row for row in case_trajectories if int(row["match_rank"]) == rank]
    offsets = [int(row["trajectory_year_offset"]) for row in path]
    changes = [
        None
        if row["trajectory_cumulative_change_pct"] is None
        else float(row["trajectory_cumulative_change_pct"])
        for row in path
    ]
    path_matrix.append([np.nan if value is None else value for value in changes])
    case_figure.add_trace(
        go.Scatter(
            x=offsets,
            y=changes,
            mode="lines+markers",
            connectgaps=False,
            line={"width": 2.6 if rank == 1 else 1.2, "color": NAVY if rank == 1 else "#A7BAC4"},
            marker={"size": 6 if rank == 1 else 4},
            opacity=1.0 if rank == 1 else 0.68,
            name=f"#{rank} {match['candidate_state_abbreviation']}",
            legendgroup="paths",
            showlegend=rank == 1,
            hovertemplate=(
                f"#{rank} {match['candidate_county_name']}, {match['candidate_state_abbreviation']}"
                "<br>Elapsed year %{x}<br>Cumulative change %{y:.1f}%<extra></extra>"
            ),
        ),
        row=2,
        col=1,
    )
median_path = np.nanmedian(np.asarray(path_matrix, dtype=float), axis=0)
case_figure.add_trace(
    go.Scatter(
        x=list(range(case_horizon_years + 1)),
        y=median_path,
        mode="lines+markers",
        line={"width": 3.2, "color": TEXT, "dash": "dash"},
        marker={"size": 7},
        name="Median of ten matches",
        hovertemplate="Elapsed year %{x}<br>Median cumulative change %{y:.1f}%<extra></extra>",
    ),
    row=2,
    col=1,
)

case_figure.update_geos(
    scope="usa",
    projection_type="albers usa",
    showland=True,
    landcolor="#F2F5F6",
    showsubunits=True,
    subunitcolor="white",
    showlakes=True,
    lakecolor="white",
    bgcolor="white",
    row=1,
    col=1,
)
case_figure.update_xaxes(
    title_text="Years after the historical match",
    tickmode="linear",
    dtick=1,
    gridcolor="#E2E8EB",
    row=2,
    col=1,
)
case_figure.update_yaxes(
    title_text="Cumulative FHFA HPI change (%)", gridcolor="#E2E8EB", row=2, col=1
)
case_figure.update_xaxes(title_text="Mean absolute standardized gap", row=1, col=2)
case_figure.update_layout(
    title={
        "text": (
            f"Historical analogues for {query_label}<br>"
            "<sup>Selected because it has ten state-diverse matches, complete three-year paths, "
            "and no query-side imputation</sup>"
        ),
        "x": 0.02,
        "xanchor": "left",
    },
    template="plotly_white",
    height=980,
    width=1600,
    margin={"l": 70, "r": 45, "t": 120, "b": 95},
    font={"family": "Arial", "size": 13, "color": TEXT},
    legend={"orientation": "h", "y": -0.08, "x": 0.5, "xanchor": "center"},
    annotations=[
        *list(case_figure.layout.annotations),
        {
            "text": (
                "Observed historical paths, not forecasts. Smaller feature gaps mean closer model "
                "inputs; they do not identify causal drivers."
            ),
            "x": 0,
            "y": -0.12,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "xanchor": "left",
            "font": {"size": 11, "color": MUTED},
        },
    ],
)
case_path = figure_directory / figure_spec(5).file_name
case_figure.write_image(case_path, width=1600, height=980, scale=1.5)
manifest_records.append(_manifest_record(5, case_path))

# COMMAND ----------

validate_figure_manifest_records(manifest_records)
manifest_name = qualified_name(catalog, evaluation_schema, figure_manifest_table)
manifest = spark.createDataFrame(manifest_records).withColumn(
    "similarity_figure_built_at_utc",
    functions.to_timestamp("similarity_figure_built_at_utc"),
)
(
    manifest.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(manifest_name)
)
published = spark.table(manifest_name)
if published.count() != len(SIMILARITY_FIGURE_SPECS):
    raise RuntimeError("Published similarity manifest does not contain five figures")
if published.select("similarity_figure_build_id").distinct().count() != 1:
    raise RuntimeError("Published similarity manifest contains multiple build IDs")
display(published.orderBy("figure_sequence"))
print(f"Published five similarity communication figures for build {build_id}.")

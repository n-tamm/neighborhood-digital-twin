# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Render report-ready EDA figures
# MAGIC
# MAGIC Figures are rendered from governed gold summaries and approved display geometry. PNGs are
# MAGIC stored in a versioned Unity Catalog volume directory, and a Delta manifest records their
# MAGIC paths and intended interpretation. The maps are descriptive and use display-only geometry.

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

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize
from matplotlib.patches import Patch
from matplotlib.patches import Polygon as MatplotlibPolygon
from shapely import wkb
from shapely.geometry import MultiPolygon, Polygon

from neighborhood_twin.data.databricks import qualified_name

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("silver_schema", "neighborhood_twin_silver", "Silver schema")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("figure_volume", "eda_figures", "EDA figure volume")
dbutils.widgets.text("figure_manifest_table", "gold_eda_figure_manifest", "Figure manifest")
dbutils.widgets.text("pilot_state_fips", "04,26,42", "Pilot state FIPS codes")

catalog = dbutils.widgets.get("catalog").strip()
silver_schema = dbutils.widgets.get("silver_schema").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
figure_volume = dbutils.widgets.get("figure_volume").strip()
figure_manifest_table = dbutils.widgets.get("figure_manifest_table").strip()
pilot_states = tuple(
    item.strip() for item in dbutils.widgets.get("pilot_state_fips").split(",") if item.strip()
)

TEAL = "#287271"
DARK_BLUE = "#264653"
GOLD = "#E9C46A"
ORANGE = "#F4A261"
RED = "#E76F51"
GRAY = "#D5D8DC"
TEXT = "#263238"

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#B0BEC5",
        "axes.labelcolor": TEXT,
        "axes.titlecolor": TEXT,
        "axes.titlesize": 13,
        "axes.titleweight": "semibold",
        "font.size": 10,
        "text.color": TEXT,
        "xtick.color": TEXT,
        "ytick.color": TEXT,
        "grid.color": "#ECEFF1",
        "grid.linewidth": 0.8,
    }
)

# COMMAND ----------

build_row = (
    spark.table(f"{catalog}.{gold_schema}.gold_eda_housing_coverage")
    .select("visual_eda_build_id", "visual_eda_built_at_utc")
    .first()
)
if build_row is None:
    raise RuntimeError("Visual EDA summaries must be built before figures are rendered")
build_id = str(build_row["visual_eda_build_id"])
built_at_utc = build_row["visual_eda_built_at_utc"]

spark.sql(
    f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{gold_schema}`.`{figure_volume}`"
)
figure_directory = (
    Path("/Volumes") / catalog / gold_schema / figure_volume / f"build_id={build_id}"
)
figure_directory.mkdir(parents=True, exist_ok=True)

manifest_records = []


def save_figure(order: int, name: str, title: str, purpose: str, figure: object) -> None:
    """Save one versioned PNG and append its lineage to the manifest records."""

    file_path = figure_directory / f"{order:02d}_{name}.png"
    figure.savefig(file_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    byte_size = file_path.stat().st_size
    if byte_size < 10_000:
        raise RuntimeError(
            f"Rendered figure is unexpectedly small: {file_path} ({byte_size} bytes)"
        )
    manifest_records.append(
        {
            "figure_order": order,
            "figure_name": name,
            "figure_title": title,
            "figure_purpose": purpose,
            "file_path": str(file_path),
            "file_format": "png",
            "byte_size": byte_size,
            "visual_eda_build_id": build_id,
            "visual_eda_built_at_utc": built_at_utc,
            "manifest_created_at_utc": datetime.now(UTC),
        }
    )


def clean_axis(axis: object, *, grid_axis: str = "y") -> None:
    """Apply the shared minimal axis and grid treatment to a chart."""

    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis=grid_axis)
    axis.set_axisbelow(True)


def add_source_note(figure: object, text: str) -> None:
    """Add a small source or interpretation note below a figure."""

    figure.text(0.01, 0.005, text, ha="left", va="bottom", fontsize=8, color="#607D8B")

# COMMAND ----------

# Pipeline attrition
coverage = spark.table(f"{catalog}.{gold_schema}.gold_eda_state_coverage")
totals = coverage.groupBy().sum().first().asDict()
labels = [
    "Canonical tracts",
    "Current ACS profile",
    "Similarity candidates",
    "FHFA history",
    "Forecast candidates",
]
values = [
    int(totals["sum(canonical_tract_count)"]),
    int(totals["sum(current_acs_tract_count)"]),
    int(totals["sum(similarity_candidate_count)"]),
    int(totals["sum(fhfa_history_tract_count)"]),
    int(totals["sum(forecast_candidate_count)"]),
]
figure, axis = plt.subplots(figsize=(10, 5.6))
bars = axis.barh(labels[::-1], values[::-1], color=[RED, ORANGE, TEAL, GOLD, DARK_BLUE])
axis.set_title("Current national data availability narrows most at FHFA coverage")
axis.set_xlabel("Census tracts")
axis.xaxis.set_major_formatter(lambda value, _position: f"{value / 1000:,.0f}k")
for bar, value in zip(bars, values[::-1], strict=True):
    axis.text(value + 900, bar.get_y() + bar.get_height() / 2, f"{value:,}", va="center")
axis.set_xlim(0, max(values) * 1.16)
clean_axis(axis, grid_axis="x")
add_source_note(
    figure,
    "Source: governed current gold profiles. Candidate counts are availability "
    "screens, not final model samples.",
)
save_figure(
    1,
    "pipeline_attrition",
    "Current national pipeline attrition",
    "Shows where source and eligibility requirements reduce the current tract universe.",
    figure,
)

# COMMAND ----------

# Housing composition coverage
housing = (
    spark.table(f"{catalog}.{gold_schema}.gold_eda_housing_coverage")
    .orderBy("housing_composition_band_order")
    .toPandas()
)
housing = housing[housing["housing_composition_band_order"] <= 5]
x = np.arange(len(housing))
width = 0.36
figure, axis = plt.subplots(figsize=(11, 6))
axis.bar(
    x - width / 2,
    housing["fhfa_history_share"] * 100,
    width,
    label="Any FHFA history",
    color=TEAL,
)
axis.bar(
    x + width / 2,
    housing["forecast_candidate_share"] * 100,
    width,
    label="Current forecast candidate",
    color=ORANGE,
)
axis.set_xticks(x, housing["housing_composition_band"], rotation=18, ha="right")
axis.set_ylabel("Share of current-ACS tracts")
axis.set_ylim(0, 100)
axis.set_title("FHFA and forecast coverage rise with single-family housing share")
axis.legend(frameon=False, ncol=2, loc="upper left")
clean_axis(axis)
figure.subplots_adjust(bottom=0.28)
add_source_note(
    figure,
    "Housing bands use the ACS share of attached and detached single-family units. "
    "FHFA is a single-family price index.",
)
save_figure(
    2,
    "housing_composition_coverage",
    "Housing composition and FHFA coverage",
    "Tests whether single-family target availability varies with tract housing composition.",
    figure,
)

# COMMAND ----------

# Included versus excluded current-ACS tracts
comparison = (
    spark.table(f"{catalog}.{gold_schema}.gold_eda_cohort_comparison")
    .orderBy("standardized_mean_difference")
    .toPandas()
)
comparison["display_name"] = comparison["feature_name"].str.replace("_estimate", "").str.replace(
    "_", " "
)
figure, axis = plt.subplots(figsize=(10, 7))
colors = [TEAL if value >= 0 else RED for value in comparison["standardized_mean_difference"]]
axis.barh(comparison["display_name"], comparison["standardized_mean_difference"], color=colors)
axis.axvline(0, color="#455A64", linewidth=1)
axis.axvline(-0.2, color="#B0BEC5", linewidth=0.8, linestyle="--")
axis.axvline(0.2, color="#B0BEC5", linewidth=0.8, linestyle="--")
axis.set_xlabel(
    "Standardized mean difference: forecast candidates minus excluded tracts"
)
axis.set_title("Forecast availability is associated with observable community differences")
clean_axis(axis, grid_axis="x")
add_source_note(
    figure,
    "Comparison includes tracts with a current ACS profile. Differences describe "
    "selection into FHFA-based forecasting, not causal effects.",
)
save_figure(
    3,
    "forecast_included_excluded_comparison",
    "Forecast candidates versus excluded current-ACS tracts",
    "Shows whether the forecast-eligible population is observably different from "
    "excluded communities.",
    figure,
)

# COMMAND ----------

# Temporal HPI behavior
temporal = (
    spark.table(f"{catalog}.{gold_schema}.gold_eda_hpi_temporal")
    .where("observation_year >= 1990")
    .orderBy("scope_code", "observation_year")
    .toPandas()
)
scope_order = ["US", *pilot_states]
figure, axes = plt.subplots(2, 2, figsize=(13, 8), sharex=True, sharey=True)
for axis, scope_code in zip(axes.ravel(), scope_order, strict=True):
    subset = temporal[temporal["scope_code"] == scope_code]
    axis.fill_between(
        subset["observation_year"].astype(float),
        subset["p10_annual_change_pct"].astype(float),
        subset["p90_annual_change_pct"].astype(float),
        color=GOLD,
        alpha=0.35,
        label="10th–90th percentile",
    )
    axis.plot(
        subset["observation_year"],
        subset["median_annual_change_pct"],
        color=DARK_BLUE,
        linewidth=2,
        label="Median",
    )
    axis.axhline(0, color="#78909C", linewidth=0.8)
    axis.set_title(str(subset["scope_label"].iloc[0]))
    clean_axis(axis)
for axis in axes[:, 0]:
    axis.set_ylabel("Annual HPI change (%)")
for axis in axes[-1, :]:
    axis.set_xlabel("Observation year")
handles, legend_labels = axes[0, 0].get_legend_handles_labels()
figure.legend(
    handles,
    legend_labels,
    frameon=False,
    ncol=2,
    loc="upper center",
    bbox_to_anchor=(0.5, 0.945),
)
figure.suptitle(
    "Housing-price changes vary substantially across time and states",
    y=0.985,
    fontsize=15,
)
figure.tight_layout(rect=(0, 0.04, 1, 0.91))
add_source_note(
    figure,
    "Source: FHFA annual tract HPI. Shaded ranges summarize available tracts and "
    "do not correct for changing coverage.",
)
save_figure(
    4,
    "hpi_temporal_behavior",
    "FHFA annual HPI behavior over time",
    "Shows time variation and regional differences that forecasting splits and "
    "baselines must address.",
    figure,
)

# COMMAND ----------

# ACS uncertainty
uncertainty = (
    spark.table(f"{catalog}.{gold_schema}.gold_eda_acs_measure_quality")
    .orderBy("p90_relative_margin_of_error", ascending=False)
    .limit(12)
    .toPandas()
    .sort_values("p90_relative_margin_of_error")
)
uncertainty["display_name"] = uncertainty["measure_name"].str.replace("_", " ")
figure, axis = plt.subplots(figsize=(10, 7))
axis.barh(
    uncertainty["display_name"],
    uncertainty["p90_relative_margin_of_error"] * 100,
    color=ORANGE,
    label="90th percentile",
)
axis.scatter(
    uncertainty["median_relative_margin_of_error"] * 100,
    uncertainty["display_name"],
    color=DARK_BLUE,
    s=28,
    zorder=3,
    label="Median",
)
axis.set_xlabel("Relative margin of error (%)")
axis.set_title("Small housing categories have high ACS sampling uncertainty")
axis.legend(frameon=False, loc="lower right")
clean_axis(axis, grid_axis="x")
add_source_note(
    figure,
    "Relative MOE is the published 90% margin of error divided by the absolute "
    "estimate; near-zero estimates can produce large ratios.",
)
save_figure(
    5,
    "acs_measurement_uncertainty",
    "ACS measurement uncertainty by measure",
    "Identifies feature families that may be too noisy without aggregation or "
    "uncertainty handling.",
    figure,
)

# COMMAND ----------

# Map helpers and geometry collection
def polygon_patches(geometry: object) -> list[MatplotlibPolygon]:
    """Convert a polygon or multipolygon into Matplotlib exterior patches."""

    polygons = [geometry] if isinstance(geometry, Polygon) else list(geometry.geoms)
    return [
        MatplotlibPolygon(np.asarray(polygon.exterior.coords), closed=True)
        for polygon in polygons
        if not polygon.is_empty
    ]


profile_for_maps = spark.table(
    f"{catalog}.{gold_schema}.gold_tract_profile_current"
).select(
    "geoid_2020",
    "state_fips",
    "state_abbreviation",
    "forecast_candidate",
    "latest_hpi_annual_change_pct",
)
display_geometry = spark.table(
    f"{catalog}.{silver_schema}.silver_canonical_tract_2020"
).select("geoid_2020", "display_geometry_wkb")

geometry_rows = (
    profile_for_maps.join(display_geometry, "geoid_2020", "inner")
    .where(f"state_fips IN ({','.join(repr(code) for code in pilot_states)})")
    .where("display_geometry_wkb IS NOT NULL")
    .select(
        "state_fips",
        "state_abbreviation",
        "display_geometry_wkb",
        "forecast_candidate",
        "latest_hpi_annual_change_pct",
    )
    .collect()
)

map_records = []
for row in geometry_rows:
    geometry = wkb.loads(bytes(row["display_geometry_wkb"]))
    if not isinstance(geometry, (Polygon, MultiPolygon)):
        continue
    map_records.append(
        (
            row["state_fips"],
            row["state_abbreviation"],
            polygon_patches(geometry),
            bool(row["forecast_candidate"]),
            row["latest_hpi_annual_change_pct"],
        )
    )

state_labels = {
    code: next(record[1] for record in map_records if record[0] == code)
    for code in pilot_states
}

# Forecast coverage maps
figure, axes = plt.subplots(1, len(pilot_states), figsize=(15, 6))
for axis, state_fips in zip(axes, pilot_states, strict=True):
    included_patches = []
    excluded_patches = []
    for record_state, _abbr, patches, candidate, _change in map_records:
        if record_state != state_fips:
            continue
        (included_patches if candidate else excluded_patches).extend(patches)
    if excluded_patches:
        axis.add_collection(
            PatchCollection(
                excluded_patches,
                facecolor=GRAY,
                edgecolor="white",
                linewidth=0.08,
            )
        )
    if included_patches:
        axis.add_collection(
            PatchCollection(
                included_patches,
                facecolor=TEAL,
                edgecolor="white",
                linewidth=0.08,
            )
        )
    axis.autoscale_view()
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title(state_labels[state_fips])
figure.legend(
    handles=[
        Patch(facecolor=TEAL, label="Forecast candidate"),
        Patch(facecolor=GRAY, label="Excluded or unavailable"),
    ],
    frameon=False,
    ncol=2,
    loc="upper center",
    bbox_to_anchor=(0.5, 0.91),
)
figure.suptitle("Forecast eligibility varies within each pilot state", y=0.97, fontsize=15)
figure.subplots_adjust(top=0.84, bottom=0.1, wspace=0.12)
add_source_note(
    figure,
    "Display-only Census geometry. Eligibility requires current ACS and sufficient "
    "recent FHFA history; it is not a forecast result.",
)
save_figure(
    6,
    "forecast_candidate_maps",
    "Forecast eligibility in the pilot states",
    "Maps within-state gaps in current forecast eligibility for Arizona, Michigan, "
    "and Pennsylvania.",
    figure,
)

# Latest HPI change maps
available_changes = np.asarray(
    [float(record[4]) for record in map_records if record[4] is not None], dtype=float
)
lower, upper = np.quantile(available_changes, [0.05, 0.95])
limit = max(abs(lower), abs(upper), 1.0)
normalizer = Normalize(vmin=-limit, vmax=limit)
cmap = plt.get_cmap("RdYlBu")
figure, axes = plt.subplots(1, len(pilot_states), figsize=(15, 6))
for axis, state_fips in zip(axes, pilot_states, strict=True):
    colored_patches = []
    values_for_patches = []
    missing_patches = []
    for record_state, _abbr, patches, _candidate, change in map_records:
        if record_state != state_fips:
            continue
        if change is None:
            missing_patches.extend(patches)
        else:
            colored_patches.extend(patches)
            values_for_patches.extend([float(change)] * len(patches))
    if missing_patches:
        axis.add_collection(
            PatchCollection(
                missing_patches,
                facecolor=GRAY,
                edgecolor="white",
                linewidth=0.05,
            )
        )
    collection = PatchCollection(
        colored_patches,
        cmap=cmap,
        norm=normalizer,
        edgecolor="white",
        linewidth=0.05,
    )
    collection.set_array(np.asarray(values_for_patches))
    axis.add_collection(collection)
    axis.autoscale_view()
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title(state_labels[state_fips])
colorbar = figure.colorbar(collection, ax=list(axes), shrink=0.72, pad=0.02)
colorbar.set_label("Latest annual HPI change (%)")
figure.suptitle("Recent tract-level HPI changes are spatially uneven", y=0.98, fontsize=15)
add_source_note(
    figure,
    "Display-only Census geometry. Color scale is symmetric and clipped to the "
    "pilot-state 5th and 95th percentiles; gray indicates no usable FHFA value.",
)
save_figure(
    7,
    "latest_hpi_change_maps",
    "Latest annual HPI change in the pilot states",
    "Shows spatial variation in the latest available FHFA annual change without "
    "implying causality.",
    figure,
)

# COMMAND ----------

manifest = spark.createDataFrame(manifest_records)
manifest_name = qualified_name(catalog, gold_schema, figure_manifest_table)
(
    manifest.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(manifest_name)
)
if manifest.count() != 7 or manifest.where("byte_size < 10000").count() != 0:
    raise RuntimeError("Figure manifest did not reconcile to seven nonempty PNG files")

display(manifest.orderBy("figure_order"))
print(f"Published seven figures and {manifest_name} for visual EDA build {build_id}.")

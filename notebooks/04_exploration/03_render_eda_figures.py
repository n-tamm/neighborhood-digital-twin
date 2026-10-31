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
from collections import defaultdict
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
from matplotlib.colors import Normalize, TwoSlopeNorm
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.patches import Polygon as MatplotlibPolygon
from pyspark.sql import functions as spark_functions
from shapely import union_all, wkb
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

spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{gold_schema}`.`{figure_volume}`")
figure_directory = Path("/Volumes") / catalog / gold_schema / figure_volume / f"build_id={build_id}"
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
comparison["display_name"] = (
    comparison["feature_name"].str.replace("_estimate", "").str.replace("_", " ")
)
figure, axis = plt.subplots(figsize=(10, 7))
colors = [TEAL if value >= 0 else RED for value in comparison["standardized_mean_difference"]]
axis.barh(comparison["display_name"], comparison["standardized_mean_difference"], color=colors)
axis.axvline(0, color="#455A64", linewidth=1)
axis.axvline(-0.2, color="#B0BEC5", linewidth=0.8, linestyle="--")
axis.axvline(0.2, color="#B0BEC5", linewidth=0.8, linestyle="--")
axis.set_xlabel("Standardized mean difference: forecast candidates minus excluded tracts")
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

# Historical tract-vintage coverage
eligible_coverage = (
    spark.table(f"{catalog}.{gold_schema}.gold_historical_tract_coverage")
    .groupBy("acs_release_year")
    .agg(
        spark_functions.max("release_source_tract_count").alias("source_tract_count"),
        spark_functions.sum("canonical_tract_count").alias("eligible_tract_count"),
    )
    .orderBy("acs_release_year")
    .toPandas()
)
eligible_coverage["excluded_tract_count"] = (
    eligible_coverage["source_tract_count"] - eligible_coverage["eligible_tract_count"]
)
years = eligible_coverage["acs_release_year"].astype(float)
eligible = eligible_coverage["eligible_tract_count"].astype(float)
excluded = eligible_coverage["excluded_tract_count"].astype(float)
figure, axis = plt.subplots(figsize=(11, 6))
axis.fill_between(years, 0, eligible, color=TEAL, alpha=0.9, label="Usable canonical tracts")
axis.fill_between(
    years,
    eligible,
    eligible + excluded,
    color=GRAY,
    alpha=0.9,
    label="Excluded changed or unsupported tracts",
)
axis.axvline(2019.5, color="#546E7A", linewidth=1, linestyle="--")
axis.annotate(
    "2020 tract geography begins",
    xy=(2020, float((eligible + excluded).max()) * 0.92),
    xytext=(2016.4, float((eligible + excluded).max()) * 1.04),
    arrowprops={"arrowstyle": "->", "color": "#546E7A"},
    color="#455A64",
)
axis.set_title("The longitudinal tract universe expands after the 2020 geography change")
axis.set_xlabel("ACS five-year release")
axis.set_ylabel("Source tracts")
axis.yaxis.set_major_formatter(lambda value, _position: f"{value / 1000:,.0f}k")
axis.legend(frameon=False, loc="lower right")
clean_axis(axis)
add_source_note(
    figure,
    "Pre-2020 releases retain only conservative stable 2010-to-2020 tract mappings. "
    "The larger 2020-vintage universe is not a balanced continuation of the earlier panel.",
)
save_figure(
    6,
    "tract_vintage_coverage",
    "Historical tract coverage across the 2010 and 2020 vintages",
    "Makes the governed geography break and its effect on longitudinal sample size explicit.",
    figure,
)

# COMMAND ----------

# Model-feature completeness
feature_completeness = (
    spark.table(f"{catalog}.{gold_schema}.gold_model_readiness_summary")
    .where("summary_group = 'feature_missingness'")
    .select("dimension_value", "non_null_rate")
    .orderBy("non_null_rate")
    .limit(15)
    .toPandas()
    .sort_values("non_null_rate", ascending=True)
)
feature_completeness["display_name"] = (
    feature_completeness["dimension_value"]
    .str.replace("_estimate", "", regex=False)
    .str.replace("_pct", "", regex=False)
    .str.replace("_", " ", regex=False)
)
figure, axis = plt.subplots(figsize=(10, 7.5))
axis.barh(
    feature_completeness["display_name"],
    feature_completeness["non_null_rate"] * 100,
    color=TEAL,
)
axis.axvline(95, color=GOLD, linewidth=1.2, linestyle="--", label="95% complete")
axis.set_xlim(80, 100.5)
axis.set_xlabel("Available model-feature rows (%)")
axis.set_title("The least-complete model inputs are still broadly available")
axis.legend(frameon=False, loc="lower right")
clean_axis(axis, grid_axis="x")
add_source_note(
    figure,
    "Completeness is measured on the point-in-time feature table before training-fitted "
    "imputation. Complete-case filtering is not used.",
)
save_figure(
    7,
    "model_feature_completeness",
    "Lowest model-feature completeness rates",
    "Surfaces which approved predictors drive imputation and possible coverage sensitivity.",
    figure,
)

# COMMAND ----------

# Independent forecast-origin years by horizon and split role
split_origins = (
    spark.table(f"{catalog}.{gold_schema}.gold_model_split_assignment")
    .where("temporal_role IN ('training', 'validation', 'calibration', 'locked_temporal_test')")
    .groupBy("horizon_years", "temporal_role")
    .agg(spark_functions.countDistinct("forecast_origin_year").alias("origin_year_count"))
    .toPandas()
)
role_order = ["training", "validation", "calibration", "locked_temporal_test"]
role_labels = ["Training", "Validation", "Calibration", "Locked test"]
horizon_order = [1, 3, 5]
origin_matrix = np.zeros((len(horizon_order), len(role_order)))
for horizon_index, horizon in enumerate(horizon_order):
    for role_index, role in enumerate(role_order):
        match = split_origins[
            (split_origins["horizon_years"] == horizon) & (split_origins["temporal_role"] == role)
        ]
        if not match.empty:
            origin_matrix[horizon_index, role_index] = float(match["origin_year_count"].iloc[0])
figure, axis = plt.subplots(figsize=(9, 5.2))
image = axis.imshow(origin_matrix, cmap="cividis", vmin=0, vmax=max(10, origin_matrix.max()))
for row_index in range(origin_matrix.shape[0]):
    for column_index in range(origin_matrix.shape[1]):
        value = int(origin_matrix[row_index, column_index])
        axis.text(
            column_index,
            row_index,
            str(value),
            ha="center",
            va="center",
            color=TEXT if value >= 5 else "white",
            fontweight="semibold",
        )
axis.set_xticks(range(len(role_labels)), role_labels)
axis.set_yticks(range(len(horizon_order)), [f"{horizon}-year" for horizon in horizon_order])
axis.set_title("Longer horizons have few independent training periods")
axis.set_xlabel("Frozen split role")
axis.set_ylabel("Forecast horizon")
colorbar = figure.colorbar(image, ax=axis, shrink=0.8, pad=0.03)
colorbar.set_label("Distinct forecast-origin years")
add_source_note(
    figure,
    "Rows repeat across tracts, but the displayed origin-year count is the relevant temporal "
    "evidence. Locked-test outcomes remain unopened during development.",
)
save_figure(
    8,
    "model_split_origin_years",
    "Independent forecast-origin years by horizon and split",
    "Shows why one year is primary, three years secondary, and five years exploratory.",
    figure,
)

# COMMAND ----------


# Map helpers and geometry collection
def polygon_patches(geometry: object) -> list[MatplotlibPolygon]:
    """Convert polygonal Shapely geometry into Matplotlib exterior patches."""

    if isinstance(geometry, Polygon):
        polygons = [geometry]
    elif isinstance(geometry, MultiPolygon):
        polygons = list(geometry.geoms)
    elif hasattr(geometry, "geoms"):
        polygons = [part for part in geometry.geoms if isinstance(part, Polygon)]
    else:
        polygons = []
    return [
        MatplotlibPolygon(np.asarray(polygon.exterior.coords), closed=True)
        for polygon in polygons
        if not polygon.is_empty
    ]


def format_map_axis(axis: object, title: str) -> None:
    """Apply a consistent frameless geographic panel treatment."""

    axis.autoscale_view()
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title(title, pad=8)


target_change = spark_functions.exp(spark_functions.col("target_cumulative_log_change")) - 1
period_changes = (
    spark.table(f"{catalog}.{gold_schema}.gold_forecast_target_historical")
    .where(spark_functions.col("target_is_observed"))
    .where(
        (
            (spark_functions.col("forecast_origin_year") == 2020)
            & (spark_functions.col("horizon_years") == 5)
        )
        | (
            (spark_functions.col("forecast_origin_year") == 2024)
            & (spark_functions.col("horizon_years") == 1)
        )
    )
    .groupBy("geoid_2020")
    .agg(
        spark_functions.max(
            spark_functions.when(
                (spark_functions.col("forecast_origin_year") == 2020)
                & (spark_functions.col("horizon_years") == 5),
                target_change * 100,
            )
        ).alias("hpi_change_2020_2025_pct"),
        spark_functions.max(
            spark_functions.when(
                (spark_functions.col("forecast_origin_year") == 2024)
                & (spark_functions.col("horizon_years") == 1),
                target_change * 100,
            )
        ).alias("hpi_change_2024_2025_pct"),
    )
)
profile_for_maps = (
    spark.table(f"{catalog}.{gold_schema}.gold_tract_profile_current")
    .select(
        "geoid_2020",
        "state_fips",
        "state_abbreviation",
        "state_name",
        "county_geoid",
        "county_name",
        "forecast_candidate",
    )
    .join(period_changes, "geoid_2020", "left")
)
display_geometry = spark.table(f"{catalog}.{silver_schema}.silver_canonical_tract_2020").select(
    "geoid_2020", "display_geometry_wkb"
)

geometry_rows = (
    profile_for_maps.join(display_geometry, "geoid_2020", "inner")
    .where(f"state_fips IN ({','.join(repr(code) for code in pilot_states)})")
    .where("display_geometry_wkb IS NOT NULL")
    .select(
        "state_fips",
        "state_abbreviation",
        "state_name",
        "county_geoid",
        "county_name",
        "display_geometry_wkb",
        "forecast_candidate",
        "hpi_change_2020_2025_pct",
        "hpi_change_2024_2025_pct",
    )
    .collect()
)

map_records = []
for row in geometry_rows:
    geometry = wkb.loads(bytes(row["display_geometry_wkb"]))
    if not isinstance(geometry, (Polygon, MultiPolygon)):
        continue
    map_records.append(
        {
            "state_fips": row["state_fips"],
            "state_abbreviation": row["state_abbreviation"],
            "state_name": row["state_name"],
            "county_geoid": row["county_geoid"],
            "county_name": row["county_name"],
            "geometry": geometry,
            "forecast_candidate": bool(row["forecast_candidate"]),
            "hpi_change_2020_2025_pct": row["hpi_change_2020_2025_pct"],
            "hpi_change_2024_2025_pct": row["hpi_change_2024_2025_pct"],
        }
    )

state_abbreviations = {
    code: next(
        str(record["state_abbreviation"]) for record in map_records if record["state_fips"] == code
    )
    for code in pilot_states
}
state_names = {
    code: next(
        str(record["state_name"]) for record in map_records if record["state_fips"] == code
    )
    for code in pilot_states
}

county_tract_geometries = defaultdict(list)
county_candidates = defaultdict(list)
county_five_year_changes = defaultdict(list)
county_recent_changes = defaultdict(list)
county_states = {}
county_names = {}
for record in map_records:
    county_geoid = str(record["county_geoid"])
    county_tract_geometries[county_geoid].append(record["geometry"])
    county_candidates[county_geoid].append(float(record["forecast_candidate"]))
    if record["hpi_change_2020_2025_pct"] is not None:
        county_five_year_changes[county_geoid].append(
            float(record["hpi_change_2020_2025_pct"])
        )
    if record["hpi_change_2024_2025_pct"] is not None:
        county_recent_changes[county_geoid].append(
            float(record["hpi_change_2024_2025_pct"])
        )
    county_states[county_geoid] = str(record["state_fips"])
    county_names[county_geoid] = str(record["county_name"])

county_records = []
for county_geoid, tract_geometries in county_tract_geometries.items():
    five_year_changes = county_five_year_changes[county_geoid]
    recent_changes = county_recent_changes[county_geoid]
    county_records.append(
        {
            "county_geoid": county_geoid,
            "county_name": county_names[county_geoid],
            "state_fips": county_states[county_geoid],
            "geometry": union_all(tract_geometries),
            "forecast_candidate_share": float(np.mean(county_candidates[county_geoid])),
            "median_hpi_change_2020_2025_pct": (
                float(np.median(five_year_changes)) if five_year_changes else None
            ),
            "median_hpi_change_2024_2025_pct": (
                float(np.median(recent_changes)) if recent_changes else None
            ),
        }
    )


def add_county_outlines(axis: object, state_fips: str) -> None:
    """Draw dissolved county boundaries over a tract-level map."""

    outlines = [
        patch
        for record in county_records
        if record["state_fips"] == state_fips
        for patch in polygon_patches(record["geometry"])
    ]
    if outlines:
        axis.add_collection(
            PatchCollection(
                outlines,
                facecolor="none",
                edgecolor="#FFFFFF",
                linewidth=0.35,
                alpha=0.85,
            )
        )


def metric_values(records: list[dict[str, object]], metric: str) -> np.ndarray:
    """Return finite numeric values for one map or summary metric."""

    return np.asarray(
        [
            float(record[metric])
            for record in records
            if record[metric] is not None and np.isfinite(float(record[metric]))
        ],
        dtype=float,
    )


def robust_linear_normalizer(values: np.ndarray) -> Normalize:
    """Create a shared linear scale clipped to the central 90 percent of values."""

    lower, upper = np.quantile(values, [0.05, 0.95])
    if upper <= lower:
        upper = lower + 1.0
    return Normalize(vmin=float(lower), vmax=float(upper), clip=True)


def robust_zero_centered_normalizer(values: np.ndarray) -> TwoSlopeNorm:
    """Create a symmetric zero-centered scale from robust change limits."""

    lower, upper = np.quantile(values, [0.05, 0.95])
    limit = max(abs(float(lower)), abs(float(upper)), 1.0)
    return TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit)


def draw_choropleth(
    axis: object,
    records: list[dict[str, object]],
    *,
    state_fips: str,
    metric: str,
    cmap: str,
    normalizer: object,
    county_outlines: bool,
    polygon_edges: bool = False,
) -> None:
    """Draw one state panel with shared scaling and explicit missing-data treatment."""

    colored_patches = []
    colored_values = []
    missing_patches = []
    for record in records:
        if record["state_fips"] != state_fips:
            continue
        patches = polygon_patches(record["geometry"])
        value = record[metric]
        if value is None:
            missing_patches.extend(patches)
        else:
            colored_patches.extend(patches)
            colored_values.extend([float(value)] * len(patches))
    if missing_patches:
        axis.add_collection(
            PatchCollection(
                missing_patches,
                facecolor="#E5E7EB",
                edgecolor="#FFFFFF" if polygon_edges else "none",
                linewidth=0.35 if polygon_edges else 0,
            )
        )
    if colored_patches:
        collection = PatchCollection(
            colored_patches,
            cmap=cmap,
            norm=normalizer,
            edgecolor="#FFFFFF" if polygon_edges else "none",
            linewidth=0.35 if polygon_edges else 0,
        )
        collection.set_array(np.asarray(colored_values))
        axis.add_collection(collection)
    if county_outlines:
        add_county_outlines(axis, state_fips)
    format_map_axis(axis, "")


def add_map_header(figure: object, title: str, subtitle: str) -> None:
    """Add a consistent left-aligned title and analytical subtitle."""

    figure.text(0.035, 0.965, title, ha="left", va="top", fontsize=18, fontweight="semibold")
    figure.text(0.035, 0.925, subtitle, ha="left", va="top", fontsize=10.5, color="#546E7A")


# Forecast coverage maps with a quantitative sidebar
coverage_by_state = {
    state_fips: float(
        np.mean(
            [
                float(record["forecast_candidate"])
                for record in map_records
                if record["state_fips"] == state_fips
            ]
        )
    )
    for state_fips in pilot_states
}
figure = plt.figure(figsize=(16, 7))
grid = GridSpec(
    1,
    4,
    figure=figure,
    width_ratios=[1.1, 1.1, 1.1, 0.78],
    left=0.035,
    right=0.97,
    top=0.82,
    bottom=0.13,
    wspace=0.07,
)
for column_index, state_fips in enumerate(pilot_states):
    axis = figure.add_subplot(grid[0, column_index])
    included_patches = []
    excluded_patches = []
    state_records = [record for record in map_records if record["state_fips"] == state_fips]
    for record in state_records:
        target = included_patches if record["forecast_candidate"] else excluded_patches
        target.extend(polygon_patches(record["geometry"]))
    axis.add_collection(
        PatchCollection(excluded_patches, facecolor="#E5E7EB", edgecolor="none")
    )
    axis.add_collection(PatchCollection(included_patches, facecolor=TEAL, edgecolor="none"))
    add_county_outlines(axis, state_fips)
    format_map_axis(axis, state_names[state_fips])
    axis.text(
        0.5,
        -0.025,
        f"{coverage_by_state[state_fips]:.0%} eligible  •  {len(state_records):,} tracts",
        transform=axis.transAxes,
        ha="center",
        va="top",
        fontsize=9,
        color="#546E7A",
    )
summary_axis = figure.add_subplot(grid[0, 3])
positions = np.arange(len(pilot_states))[::-1]
shares = np.asarray([coverage_by_state[code] for code in pilot_states])
summary_axis.barh(positions, shares * 100, height=0.48, color=TEAL)
summary_axis.set_yticks(positions, [state_abbreviations[code] for code in pilot_states])
summary_axis.set_xlim(0, 100)
summary_axis.set_xlabel("Eligible tracts (%)")
summary_axis.set_title("Coverage at a glance", loc="left", pad=12)
for position, share in zip(positions, shares, strict=True):
    summary_axis.text(share * 100 + 2, position, f"{share:.0%}", va="center", fontweight="semibold")
summary_axis.spines[["top", "right", "left"]].set_visible(False)
summary_axis.grid(axis="x")
summary_axis.set_axisbelow(True)
summary_axis.legend(
    handles=[
        Patch(facecolor=TEAL, label="Current forecast candidate"),
        Patch(facecolor="#E5E7EB", label="Unavailable"),
    ],
    frameon=False,
    loc="lower left",
    bbox_to_anchor=(-0.04, -0.28),
)
add_map_header(
    figure,
    "Forecast coverage is broad in Michigan, but more selective in Arizona and Pennsylvania",
    (
        "Eligibility requires a current ACS profile and sufficient recent FHFA history; "
        "it is not a model result."
    ),
)
add_source_note(
    figure,
    (
        "Source: current gold tract profile and display-only Census geometry. "
        "White lines show county boundaries."
    ),
)
save_figure(
    9,
    "forecast_candidate_maps",
    "Forecast eligibility in the pilot states",
    "Combines tract maps with a state coverage summary to show where the forecast can speak.",
    figure,
)

# Five-year housing-market movement compared with the latest annual change
five_year_metric = "hpi_change_2020_2025_pct"
recent_metric = "hpi_change_2024_2025_pct"
five_year_values = metric_values(map_records, five_year_metric)
recent_values = metric_values(map_records, recent_metric)
five_year_normalizer = robust_linear_normalizer(five_year_values)
recent_normalizer = robust_zero_centered_normalizer(recent_values)
five_year_cmap = "YlGnBu"
recent_cmap = "BrBG"

figure = plt.figure(figsize=(16, 10.5))
grid = GridSpec(
    2,
    4,
    figure=figure,
    width_ratios=[1, 1, 1, 0.08],
    left=0.065,
    right=0.94,
    top=0.84,
    bottom=0.09,
    hspace=0.08,
    wspace=0.05,
)
for column_index, state_fips in enumerate(pilot_states):
    state_records = [record for record in map_records if record["state_fips"] == state_fips]
    top_axis = figure.add_subplot(grid[0, column_index])
    draw_choropleth(
        top_axis,
        map_records,
        state_fips=state_fips,
        metric=five_year_metric,
        cmap=five_year_cmap,
        normalizer=five_year_normalizer,
        county_outlines=True,
    )
    top_values = metric_values(state_records, five_year_metric)
    top_axis.set_title(state_names[state_fips], pad=8, fontsize=13, fontweight="semibold")
    top_axis.text(
        0.02,
        0.02,
        f"Median {np.median(top_values):.1f}%  •  {len(top_values):,} observed tracts",
        transform=top_axis.transAxes,
        fontsize=8.5,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.9,
        },
    )
    bottom_axis = figure.add_subplot(grid[1, column_index])
    draw_choropleth(
        bottom_axis,
        map_records,
        state_fips=state_fips,
        metric=recent_metric,
        cmap=recent_cmap,
        normalizer=recent_normalizer,
        county_outlines=True,
    )
    bottom_values = metric_values(state_records, recent_metric)
    bottom_axis.text(
        0.02,
        0.02,
        f"Median {np.median(bottom_values):+.1f}%  •  {len(bottom_values):,} observed tracts",
        transform=bottom_axis.transAxes,
        fontsize=8.5,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.9,
        },
    )
five_colorbar_axis = figure.add_subplot(grid[0, 3])
five_colorbar = figure.colorbar(
    plt.cm.ScalarMappable(norm=five_year_normalizer, cmap=five_year_cmap),
    cax=five_colorbar_axis,
)
five_colorbar.set_label("Cumulative HPI change (%)")
recent_colorbar_axis = figure.add_subplot(grid[1, 3])
recent_colorbar = figure.colorbar(
    plt.cm.ScalarMappable(norm=recent_normalizer, cmap=recent_cmap),
    cax=recent_colorbar_axis,
)
recent_colorbar.set_label("Annual HPI change (%)")
figure.text(
    0.025,
    0.63,
    "CUMULATIVE\n2020–2025",
    ha="center",
    va="center",
    rotation=90,
    fontsize=9,
    fontweight="semibold",
    color="#455A64",
)
figure.text(
    0.025,
    0.28,
    "LATEST YEAR\n2024–2025",
    ha="center",
    va="center",
    rotation=90,
    fontsize=9,
    fontweight="semibold",
    color="#455A64",
)
add_map_header(
    figure,
    "Five-year housing gains were broad, while the latest year is more uneven",
    (
        "The same tract geography and shared color scale are used across Arizona, "
        "Michigan, and Pennsylvania."
    ),
)
add_source_note(
    figure,
    (
        "Source: FHFA annual tract HPI, observed endpoints only. Scales are clipped to "
        "pilot-state 5th–95th percentiles; gray means an endpoint is unavailable. "
        "Maps are descriptive, not causal."
    ),
)
save_figure(
    10,
    "hpi_change_2020_2025_maps",
    "Tract HPI change from 2020 to 2025 and in the latest year",
    "Contrasts the cumulative post-2020 housing-market pattern with the latest annual momentum.",
    figure,
)

# COMMAND ----------

# County trend story: maps, paired comparison, and computed takeaways
county_five_values = metric_values(county_records, "median_hpi_change_2020_2025_pct")
county_five_normalizer = robust_linear_normalizer(county_five_values)
state_colors = {pilot_states[0]: ORANGE, pilot_states[1]: TEAL, pilot_states[2]: DARK_BLUE}

figure = plt.figure(figsize=(16, 10.5))
grid = GridSpec(
    2,
    4,
    figure=figure,
    height_ratios=[1.08, 0.92],
    width_ratios=[1, 1, 1, 0.78],
    left=0.045,
    right=0.97,
    top=0.84,
    bottom=0.10,
    hspace=0.24,
    wspace=0.10,
)
for column_index, state_fips in enumerate(pilot_states):
    axis = figure.add_subplot(grid[0, column_index])
    draw_choropleth(
        axis,
        county_records,
        state_fips=state_fips,
        metric="median_hpi_change_2020_2025_pct",
        cmap=five_year_cmap,
        normalizer=county_five_normalizer,
        county_outlines=False,
        polygon_edges=True,
    )
    state_counties = [record for record in county_records if record["state_fips"] == state_fips]
    values = metric_values(state_counties, "median_hpi_change_2020_2025_pct")
    axis.set_title(
        f"{state_names[state_fips]}\nMedian county change: {np.median(values):.1f}%",
        pad=8,
        fontsize=12,
        fontweight="semibold",
    )
legend_axis = figure.add_subplot(grid[0, 3])
legend_axis.axis("off")
colorbar_axis = legend_axis.inset_axes([0.10, 0.64, 0.76, 0.08])
county_colorbar = figure.colorbar(
    plt.cm.ScalarMappable(norm=county_five_normalizer, cmap=five_year_cmap),
    cax=colorbar_axis,
    orientation="horizontal",
)
county_colorbar.set_label("County median cumulative HPI change (%)", labelpad=8)
legend_axis.text(0.10, 0.48, "2020–2025", fontsize=13, fontweight="semibold")
legend_axis.text(
    0.10,
    0.34,
    (
        "Each county is colored by the\n"
        "median tract change. Gray marks\n"
        "insufficient observed endpoints."
    ),
    fontsize=9,
    color="#546E7A",
    linespacing=1.4,
)

scatter_axis = figure.add_subplot(grid[1, :3])
paired_counties = [
    record
    for record in county_records
    if record["median_hpi_change_2020_2025_pct"] is not None
    and record["median_hpi_change_2024_2025_pct"] is not None
]
for state_fips in pilot_states:
    state_counties = [record for record in paired_counties if record["state_fips"] == state_fips]
    scatter_axis.scatter(
        [record["median_hpi_change_2020_2025_pct"] for record in state_counties],
        [record["median_hpi_change_2024_2025_pct"] for record in state_counties],
        s=38,
        alpha=0.78,
        color=state_colors[state_fips],
        edgecolor="white",
        linewidth=0.4,
        label=state_abbreviations[state_fips],
    )
scatter_axis.axhline(0, color="#90A4AE", linewidth=1, linestyle="--")
pilot_five_median = float(
    np.median([record["median_hpi_change_2020_2025_pct"] for record in paired_counties])
)
scatter_axis.axvline(pilot_five_median, color="#CFD8DC", linewidth=1, linestyle="--")
scatter_axis.text(
    pilot_five_median,
    scatter_axis.get_ylim()[1],
    "  Pilot-state county median",
    va="top",
    fontsize=8,
    color="#607D8B",
)
notable_records = []
for _key, selector in (
    ("highest five-year", lambda record: record["median_hpi_change_2020_2025_pct"]),
    ("strongest latest", lambda record: record["median_hpi_change_2024_2025_pct"]),
    ("weakest latest", lambda record: -record["median_hpi_change_2024_2025_pct"]),
):
    selected = max(paired_counties, key=selector)
    if selected not in notable_records:
        notable_records.append(selected)
for record in notable_records:
    scatter_axis.annotate(
        f"{record['county_name']}, {state_abbreviations[str(record['state_fips'])]}",
        (
            float(record["median_hpi_change_2020_2025_pct"]),
            float(record["median_hpi_change_2024_2025_pct"]),
        ),
        xytext=(6, 6),
        textcoords="offset points",
        fontsize=7.5,
        color="#455A64",
    )
scatter_axis.set_title("County gains since 2020 do not determine current momentum", loc="left")
scatter_axis.set_xlabel("Median tract HPI change, 2020–2025 (%)")
scatter_axis.set_ylabel("Median tract HPI change, 2024–2025 (%)")
scatter_axis.legend(frameon=False, ncol=3, loc="upper left")
clean_axis(scatter_axis, grid_axis="both")

insight_axis = figure.add_subplot(grid[1, 3])
insight_axis.axis("off")
insight_axis.text(0, 0.98, "STATE MEDIANS", va="top", fontsize=10, fontweight="semibold")
line_y = 0.86
for state_fips in pilot_states:
    state_counties = [record for record in paired_counties if record["state_fips"] == state_fips]
    five_median = float(
        np.median([record["median_hpi_change_2020_2025_pct"] for record in state_counties])
    )
    recent_median = float(
        np.median([record["median_hpi_change_2024_2025_pct"] for record in state_counties])
    )
    insight_axis.add_line(
        Line2D(
            [0, 0.08],
            [line_y + 0.01, line_y + 0.01],
            color=state_colors[state_fips],
            linewidth=4,
        )
    )
    insight_axis.text(
        0.12,
        line_y,
        f"{state_names[state_fips]}\n{five_median:.1f}% five-year  •  {recent_median:+.1f}% latest",
        va="center",
        fontsize=8.5,
        linespacing=1.35,
    )
    line_y -= 0.18
cooled_count = sum(
    float(record["median_hpi_change_2024_2025_pct"]) < 0 for record in paired_counties
)
insight_axis.text(0, 0.28, "WHAT TO NOTICE", fontsize=10, fontweight="semibold")
insight_axis.text(
    0,
    0.20,
    (
        f"{cooled_count} of {len(paired_counties)} counties had a\n"
        "negative median change in the latest\n"
        "year despite the broader five-year gains."
    ),
    va="top",
    fontsize=8.5,
    color="#546E7A",
    linespacing=1.4,
)
add_map_header(
    figure,
    "Five-year gains do not imply the same current momentum",
    (
        "County medians reduce tract-level noise, while the paired view shows where "
        "recent movement diverges from the post-2020 pattern."
    ),
)
add_source_note(
    figure,
    (
        "Source: FHFA annual tract HPI. County shapes are dissolved from display-only "
        "tract geometry; county values are medians of observed tract changes and are "
        "not spatial-model inputs."
    ),
)
save_figure(
    11,
    "county_hpi_trend_story",
    "County HPI change from 2020 to 2025 and latest-year momentum",
    (
        "Pairs county maps with a quantitative comparison so the geographic view "
        "communicates a testable trend rather than standing alone."
    ),
    figure,
)

# COMMAND ----------

# State rollup grouped by Census region
state_rollup = (
    spark.table(f"{catalog}.{gold_schema}.gold_eda_state_coverage")
    .join(
        spark.table(f"{catalog}.{silver_schema}.silver_geography_state").select(
            "state_fips", "region_name"
        ),
        "state_fips",
        "inner",
    )
    .select(
        "state_abbreviation",
        "state_name",
        "region_name",
        "forecast_candidate_share",
    )
    .toPandas()
)
region_order = ["Northeast", "Midwest", "South", "West"]
figure, axes = plt.subplots(2, 2, figsize=(13, 10))
for axis, region in zip(axes.ravel(), region_order, strict=True):
    subset = state_rollup[state_rollup["region_name"] == region].sort_values(
        "forecast_candidate_share"
    )
    positions = np.arange(len(subset))
    values = subset["forecast_candidate_share"].astype(float) * 100
    axis.hlines(positions, 0, values, color="#CFD8DC", linewidth=2)
    axis.scatter(values, positions, color=TEAL, s=34, zorder=3)
    axis.set_yticks(positions, subset["state_abbreviation"])
    axis.set_xlim(0, 100)
    axis.set_title(region)
    axis.set_xlabel("Forecast-candidate share (%)")
    clean_axis(axis, grid_axis="x")
figure.suptitle(
    "Forecast coverage varies across states in every Census region", y=0.995, fontsize=15
)
figure.tight_layout(rect=(0, 0.04, 1, 0.97))
add_source_note(
    figure,
    "State shares aggregate current tract eligibility. They describe target availability and "
    "history depth, not expected housing-market performance.",
)
save_figure(
    12,
    "state_forecast_coverage",
    "State-level forecast coverage by Census region",
    "Adds a national state rollup and shows that model reach differs within every region.",
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
if manifest.count() != 12 or manifest.where("byte_size < 10000").count() != 0:
    raise RuntimeError("Figure manifest did not reconcile to twelve nonempty PNG files")

display(manifest.orderBy("figure_order"))
print(f"Published twelve figures and {manifest_name} for visual EDA build {build_id}.")

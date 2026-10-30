# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Render model-evaluation figures
# MAGIC
# MAGIC This workflow turns governed forecast and similarity scorecards into versioned analytical
# MAGIC figures. It does not select a champion, open locked tests, or calculate metrics from an
# MAGIC application sample. Every figure is tied to the source model run IDs in a manifest.

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
from matplotlib.ticker import PercentFormatter
from pyspark.sql import functions  # type: ignore[import-not-found]

from neighborhood_twin.data.databricks import qualified_name

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text(
    "evaluation_schema", "neighborhood_twin_evaluation", "Model-evaluation schema"
)
dbutils.widgets.text("scorecard_table", "forecast_baseline_scorecard", "Forecast scorecard")
dbutils.widgets.text(
    "similarity_summary_table", "similarity_baseline_summary", "Similarity diagnostics"
)
dbutils.widgets.text(
    "figure_volume", "model_evaluation_figures", "Model-evaluation figure volume"
)
dbutils.widgets.text(
    "figure_manifest_table",
    "model_evaluation_figure_manifest",
    "Evaluation figure manifest",
)

catalog = dbutils.widgets.get("catalog").strip()
evaluation_schema = dbutils.widgets.get("evaluation_schema").strip()
scorecard_table = dbutils.widgets.get("scorecard_table").strip()
similarity_summary_table = dbutils.widgets.get("similarity_summary_table").strip()
figure_volume = dbutils.widgets.get("figure_volume").strip()
manifest_table = dbutils.widgets.get("figure_manifest_table").strip()

scorecard = spark.table(qualified_name(catalog, evaluation_schema, scorecard_table))
similarity_summary = spark.table(
    qualified_name(catalog, evaluation_schema, similarity_summary_table)
)

forecast_run_ids = [
    str(row["forecast_run_id"])
    for row in scorecard.select("forecast_run_id").distinct().collect()
]
similarity_run_ids = [
    str(row["similarity_run_id"])
    for row in similarity_summary.select("similarity_run_id").distinct().collect()
]
if len(forecast_run_ids) != 1 or len(similarity_run_ids) != 1:
    raise RuntimeError("Evaluation figures require exactly one current forecast and similarity run")

forecast_run_id = forecast_run_ids[0]
similarity_run_id = similarity_run_ids[0]
build_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
built_at_utc = datetime.now(UTC).isoformat()
figure_directory = (
    Path("/Volumes")
    / catalog
    / evaluation_schema
    / figure_volume
    / f"build_id={build_id}"
)
figure_directory.mkdir(parents=True, exist_ok=False)

# COMMAND ----------

TEXT = "#263238"
MUTED = "#607D8B"
GRID = "#CFD8DC"
MODEL_COLORS = {
    "zero_change": "#9E9E9E",
    "latest_change_persistence": "#8D6E63",
    "recent_three_year_mean": "#FFB300",
    "county_current_trend": "#5E35B1",
    "state_current_trend": "#00897B",
    "regularized_linear": "#1565C0",
}
MODEL_LABELS = {
    "zero_change": "Zero change",
    "latest_change_persistence": "Latest-change persistence",
    "recent_three_year_mean": "Recent 3-year mean",
    "county_current_trend": "County trend",
    "state_current_trend": "State trend",
    "regularized_linear": "Regularized linear",
}

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": GRID,
        "axes.labelcolor": TEXT,
        "axes.titlecolor": TEXT,
        "xtick.color": TEXT,
        "ytick.color": TEXT,
        "font.size": 10,
        "axes.titleweight": "semibold",
    }
)

manifest_rows: list[dict[str, object]] = []


def add_source_note(figure: object, note: str) -> None:
    """Add a consistent interpretation note below a Matplotlib figure."""

    figure.text(0.01, 0.01, note, ha="left", va="bottom", fontsize=8.5, color=MUTED)


def save_figure(sequence: int, stem: str, title: str, purpose: str, figure: object) -> None:
    """Save one checked PNG and add its lineage to the pending manifest."""

    file_name = f"{sequence:02d}_{stem}.png"
    path = figure_directory / file_name
    figure.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    size = path.stat().st_size
    if size < 10_000:
        raise RuntimeError(f"Evaluation figure appears incomplete: {path} ({size} bytes)")
    manifest_rows.append(
        {
            "evaluation_build_id": build_id,
            "evaluation_built_at_utc": built_at_utc,
            "figure_sequence": sequence,
            "figure_file_name": file_name,
            "figure_title": title,
            "figure_purpose": purpose,
            "figure_path": str(path),
            "byte_size": size,
            "source_forecast_run_id": forecast_run_id,
            "source_similarity_run_id": similarity_run_id,
        }
    )


def rows_as_dicts(frame: object) -> list[dict[str, object]]:
    """Collect a deliberately small evaluation summary as plain dictionaries."""

    return [row.asDict(recursive=True) for row in frame.collect()]


def grouped_metric_figure(
    rows: list[dict[str, object]],
    *,
    metric: str,
    ylabel: str,
    title: str,
) -> object:
    """Build a grouped horizon-by-model bar chart from overall scorecard rows."""

    horizons = sorted({int(row["horizon_years"]) for row in rows})
    models = [model for model in MODEL_LABELS if any(row["model_name"] == model for row in rows)]
    figure, axis = plt.subplots(figsize=(12, 6.5))
    width = 0.82 / len(models)
    x_positions = np.arange(len(horizons))
    for index, model in enumerate(models):
        values = []
        for horizon in horizons:
            match = next(
                row
                for row in rows
                if row["model_name"] == model and int(row["horizon_years"]) == horizon
            )
            values.append(float(match[metric]))
        offset = (index - (len(models) - 1) / 2) * width
        axis.bar(
            x_positions + offset,
            values,
            width=width,
            label=MODEL_LABELS[model],
            color=MODEL_COLORS[model],
        )
    axis.set_xticks(x_positions, [f"{horizon}-year" for horizon in horizons])
    axis.set_xlabel("Forecast horizon")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.7)
    axis.set_axisbelow(True)
    axis.legend(ncol=3, frameon=False, loc="upper left")
    figure.subplots_adjust(bottom=0.15)
    return figure


overall_rows = rows_as_dicts(
    scorecard.where("slice_name = 'overall'").orderBy("horizon_years", "model_name")
)

# COMMAND ----------

figure = grouped_metric_figure(
    overall_rows,
    metric="mae_log_change",
    ylabel="Mean absolute cumulative log-change error",
    title="Simple geographic trends remain competitive with the linear model",
)
add_source_note(
    figure,
    "Validation-only results on identical governed rows. Lower is better; locked temporal tests "
    "remain unopened.",
)
save_figure(
    1,
    "forecast_mae_by_horizon",
    "Forecast validation MAE by model and horizon",
    "Compares primary point-forecast accuracy against every declared baseline.",
    figure,
)

# COMMAND ----------

figure, axis = plt.subplots(figsize=(11, 6.2))
for model in MODEL_LABELS:
    if model == "zero_change":
        continue
    model_rows = sorted(
        (row for row in overall_rows if row["model_name"] == model),
        key=lambda row: int(row["horizon_years"]),
    )
    axis.plot(
        [int(row["horizon_years"]) for row in model_rows],
        [float(row["mae_skill_vs_zero_change"]) for row in model_rows],
        marker="o",
        linewidth=2,
        label=MODEL_LABELS[model],
        color=MODEL_COLORS[model],
    )
axis.axhline(0, color=TEXT, linewidth=1)
axis.yaxis.set_major_formatter(PercentFormatter(1.0))
axis.set_xticks([1, 3, 5], ["1-year", "3-year", "5-year"])
axis.set_xlabel("Forecast horizon")
axis.set_ylabel("MAE improvement over zero-change baseline")
axis.set_title("Baseline skill must stay positive across the intended horizon")
axis.grid(color=GRID, linewidth=0.7, alpha=0.7)
axis.legend(frameon=False, ncol=2)
add_source_note(
    figure,
    "Skill equals one minus model MAE divided by zero-change MAE. Positive values improve on the "
    "reference; this is not a locked-test result.",
)
save_figure(
    2,
    "forecast_skill_vs_zero",
    "Forecast MAE skill relative to zero change",
    "Shows whether each method earns improvement over a transparent reference forecast.",
    figure,
)

# COMMAND ----------

selected_rows = [
    row
    for row in overall_rows
    if row["model_name"] in {"state_current_trend", "regularized_linear"}
]
figure, axes = plt.subplots(1, 2, figsize=(13, 5.8))
for axis, metric, ylabel, subtitle in (
    (
        axes[0],
        "mean_error_annualized_change_pct",
        "Mean signed annualized error (percentage points)",
        "Bias: positive means underprediction",
    ),
    (
        axes[1],
        "p90_absolute_error_log_change",
        "90th-percentile absolute log-change error",
        "Tail error: lower is better",
    ),
):
    horizons = [1, 3, 5]
    x_positions = np.arange(len(horizons))
    for index, model in enumerate(("state_current_trend", "regularized_linear")):
        values = [
            float(
                next(
                    row[metric]
                    for row in selected_rows
                    if row["model_name"] == model and int(row["horizon_years"]) == horizon
                )
            )
            for horizon in horizons
        ]
        axis.bar(
            x_positions + (-0.18 if index == 0 else 0.18),
            values,
            width=0.36,
            label=MODEL_LABELS[model],
            color=MODEL_COLORS[model],
        )
    axis.axhline(0, color=TEXT, linewidth=0.8)
    axis.set_xticks(x_positions, [f"{horizon}-year" for horizon in horizons])
    axis.set_ylabel(ylabel)
    axis.set_title(subtitle)
    axis.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.7)
    axis.set_axisbelow(True)
axes[0].legend(frameon=False)
figure.suptitle("Average accuracy can hide systematic bias and large misses", fontsize=15, y=0.98)
add_source_note(
    figure,
    "The state-trend baseline is shown beside the regularized linear model because it is the "
    "strongest simple multi-horizon comparator in the first validation run.",
)
save_figure(
    3,
    "forecast_bias_and_tail_error",
    "Forecast bias and tail-error diagnostics",
    "Checks systematic under- or overprediction and error severity beyond mean accuracy.",
    figure,
)

# COMMAND ----------

geography_rows = rows_as_dicts(
    scorecard.where("slice_name = 'evaluation_geography'").orderBy(
        "horizon_years", "model_name", "slice_value"
    )
)
row_labels = []
matrix_rows = []
for horizon in (1, 3, 5):
    for model in ("state_current_trend", "regularized_linear"):
        current = [
            row
            for row in geography_rows
            if int(row["horizon_years"]) == horizon and row["model_name"] == model
        ]
        values = {str(row["slice_value"]): float(row["mae_log_change"]) for row in current}
        if {"development_states", "held_out_state"}.issubset(values):
            row_labels.append(f"{MODEL_LABELS[model]} · {horizon}y")
            matrix_rows.append([values["development_states"], values["held_out_state"]])
matrix = np.asarray(matrix_rows)
figure, axis = plt.subplots(figsize=(8.5, 7))
image = axis.imshow(matrix, cmap="magma_r", aspect="auto")
for row_index in range(matrix.shape[0]):
    for column_index in range(matrix.shape[1]):
        value = matrix[row_index, column_index]
        axis.text(
            column_index,
            row_index,
            f"{value:.3f}",
            ha="center",
            va="center",
            color="white" if value > np.nanmedian(matrix) else TEXT,
            fontweight="semibold",
        )
axis.set_xticks([0, 1], ["Development states", "Held-out states"])
axis.set_yticks(range(len(row_labels)), row_labels)
axis.set_title("Geographic transfer should be compared on the same validation periods")
colorbar = figure.colorbar(image, ax=axis, shrink=0.8, pad=0.03)
colorbar.set_label("Mean absolute cumulative log-change error")
add_source_note(
    figure,
    "Held-out states are deterministic regional transfer checks. They are not the locked temporal "
    "test and should not be used alone to choose a model.",
)
save_figure(
    4,
    "forecast_geographic_transfer",
    "Forecast accuracy in development and held-out states",
    "Surfaces whether performance transfers beyond the states used for model fitting.",
    figure,
)

# COMMAND ----------

housing_rows = rows_as_dicts(
    scorecard.where(
        "slice_name = 'housing_composition_band' AND horizon_years = 1 "
        "AND model_name IN ('state_current_trend', 'regularized_linear')"
    )
)
housing_order = [
    "Under 25%",
    "25% to under 50%",
    "50% to under 75%",
    "75% or more",
    "Missing",
]
available_bands = [
    band for band in housing_order if any(row["slice_value"] == band for row in housing_rows)
]
figure, axis = plt.subplots(figsize=(11, 6.2))
x_positions = np.arange(len(available_bands))
for index, model in enumerate(("state_current_trend", "regularized_linear")):
    values = [
        float(
            next(
                row["mae_log_change"]
                for row in housing_rows
                if row["model_name"] == model and row["slice_value"] == band
            )
        )
        for band in available_bands
    ]
    axis.bar(
        x_positions + (-0.19 if index == 0 else 0.19),
        values,
        width=0.38,
        label=MODEL_LABELS[model],
        color=MODEL_COLORS[model],
    )
axis.set_xticks(x_positions, available_bands)
axis.set_xlabel("Single-family share of tract housing units")
axis.set_ylabel("One-year mean absolute log-change error")
axis.set_title("FHFA forecast errors must be interpreted with housing composition")
axis.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.7)
axis.set_axisbelow(True)
axis.legend(frameon=False)
add_source_note(
    figure,
    "FHFA tract HPI covers a filtered single-family market. Housing-composition slices expose "
    "where that target represents a smaller share of the neighborhood housing stock.",
)
save_figure(
    5,
    "forecast_housing_composition",
    "One-year forecast accuracy by housing composition",
    "Checks whether a single-family housing target behaves differently across tract housing mixes.",
    figure,
)

# COMMAND ----------

similarity_rows = rows_as_dicts(similarity_summary.orderBy("representation_name"))
figure, axes = plt.subplots(1, 2, figsize=(13, 5.8))
for index, row in enumerate(similarity_rows):
    label = "Standardized raw" if row["representation_name"] == "standardized_raw" else "PCA"
    axes[0].plot(
        [float(row["p10_similarity_distance"]), float(row["p90_similarity_distance"])],
        [index, index],
        color=MUTED,
        linewidth=2,
    )
    axes[0].plot(
        [float(row["p25_similarity_distance"]), float(row["p75_similarity_distance"])],
        [index, index],
        color="#1565C0",
        linewidth=8,
        solid_capstyle="butt",
    )
    axes[0].scatter(
        float(row["median_similarity_distance"]), index, color=TEXT, s=40, zorder=3
    )
axes[0].set_yticks(range(len(similarity_rows)), [
    "Standardized raw" if row["representation_name"] == "standardized_raw" else "PCA"
    for row in similarity_rows
])
axes[0].set_xlabel("Representation-specific distance")
axes[0].set_title("Returned-distance spread")
axes[0].grid(axis="x", color=GRID, linewidth=0.7, alpha=0.7)

metric_labels = ["Cross-state", "Same-county", "Raw/PCA overlap"]
x_positions = np.arange(len(metric_labels))
width = 0.36
for index, row in enumerate(similarity_rows):
    label = "Standardized raw" if row["representation_name"] == "standardized_raw" else "PCA"
    values = [
        float(row["cross_state_match_share"]),
        float(row["same_county_match_share"]),
        float(row["mean_raw_pca_top_k_overlap_share"]),
    ]
    axes[1].bar(
        x_positions + (-width / 2 if index == 0 else width / 2),
        values,
        width=width,
        label=label,
        color="#1565C0" if row["representation_name"] == "standardized_raw" else "#00897B",
    )
axes[1].set_xticks(x_positions, metric_labels)
axes[1].set_ylim(0, 1)
axes[1].yaxis.set_major_formatter(PercentFormatter(1.0))
axes[1].set_ylabel("Share")
axes[1].set_title("Geographic reach and representation agreement")
axes[1].grid(axis="y", color=GRID, linewidth=0.7, alpha=0.7)
axes[1].legend(frameon=False)
figure.suptitle("Similarity diagnostics describe behavior, not match usefulness", fontsize=15)
add_source_note(
    figure,
    "Distances are comparable only within a representation. Historical outcome utility, retrieval "
    "stability, and human case review remain required before application release.",
)
save_figure(
    6,
    "similarity_representation_diagnostics",
    "Similarity representation diagnostics",
    "Compares distance spread, geographic reach, and neighbor-list agreement across "
    "representations.",
    figure,
)

# COMMAND ----------

temporal_rows = rows_as_dicts(
    scorecard.where(
        "slice_name = 'forecast_origin_year' "
        "AND model_name IN ('state_current_trend', 'regularized_linear')"
    ).orderBy("horizon_years", "slice_value", "model_name")
)
figure, axes = plt.subplots(1, 3, figsize=(15, 5.5), sharey=True)
for axis, horizon in zip(axes, (1, 3, 5), strict=True):
    horizon_rows = [row for row in temporal_rows if int(row["horizon_years"]) == horizon]
    for model in ("state_current_trend", "regularized_linear"):
        model_rows = sorted(
            (row for row in horizon_rows if row["model_name"] == model),
            key=lambda row: int(str(row["slice_value"])),
        )
        axis.plot(
            [int(str(row["slice_value"])) for row in model_rows],
            [float(row["mae_log_change"]) for row in model_rows],
            marker="o",
            linewidth=2,
            color=MODEL_COLORS[model],
            label=MODEL_LABELS[model],
        )
    origins = sorted({int(str(row["slice_value"])) for row in horizon_rows})
    axis.set_xticks(origins)
    axis.set_title(f"{horizon}-year horizon · {len(origins)} origin(s)")
    axis.set_xlabel("Forecast-origin year")
    axis.grid(color=GRID, linewidth=0.7, alpha=0.7)
axes[0].set_ylabel("Mean absolute cumulative log-change error")
axes[0].legend(frameon=False)
figure.suptitle("Few validation origins limit claims about temporal stability", fontsize=15, y=0.98)
add_source_note(
    figure,
    "Each point summarizes many tracts but only one independent forecast-origin year. The locked "
    "test origin remains unopened and is not shown.",
)
save_figure(
    7,
    "forecast_temporal_stability",
    "Forecast accuracy by independent validation origin",
    "Makes the limited temporal evidence visible instead of treating tract rows as independent "
    "years.",
    figure,
)

# COMMAND ----------

if len(manifest_rows) != 7:
    raise RuntimeError(f"Expected seven model-evaluation figures, found {len(manifest_rows)}")
manifest_name = qualified_name(catalog, evaluation_schema, manifest_table)
manifest = spark.createDataFrame(manifest_rows).withColumn(
    "evaluation_built_at_utc", functions.to_timestamp("evaluation_built_at_utc")
)
(
    manifest.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(manifest_name)
)
if spark.table(manifest_name).count() != 7:
    raise RuntimeError("Published model-evaluation manifest does not contain seven figures")
display(spark.table(manifest_name).orderBy("figure_sequence"))
print(f"Published seven model-evaluation figures for build {build_id}.")

# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Render final forecast evaluation figures
# MAGIC
# MAGIC These figures compare regularized linear regression and gradient-boosted trees at both
# MAGIC horizons. They show validation, later-period evaluation, and interval behavior without
# MAGIC selecting a simple trend baseline as the project model or hiding a weak model result.

# COMMAND ----------

import sys
from datetime import UTC, datetime
from pathlib import Path


def _add_repository_source() -> None:
    """Make the deployed repository package importable by this notebook."""

    for candidate in (Path.cwd(), *Path.cwd().parents):
        source_root = candidate / "src"
        if (source_root / "neighborhood_twin").is_dir():
            sys.path.insert(0, str(source_root))
            return
    raise RuntimeError("Could not locate the repository src directory")


_add_repository_source()

# COMMAND ----------

import matplotlib.pyplot as plt
import numpy as np
from pyspark.sql import functions

from neighborhood_twin.data.databricks import qualified_name

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("model_schema", "neighborhood_twin_model", "Model schema")
dbutils.widgets.text("evaluation_schema", "neighborhood_twin_evaluation", "Evaluation schema")
dbutils.widgets.text("selection_table", "forecast_model_selection", "Model selection")
dbutils.widgets.text(
    "locked_prediction_table", "forecast_locked_test_prediction", "Locked predictions"
)
dbutils.widgets.text(
    "evaluation_threshold_table",
    "forecast_evaluation_threshold",
    "Evaluation thresholds",
)
dbutils.widgets.text("figure_volume", "model_evaluation_figures", "Evaluation figure volume")
dbutils.widgets.text(
    "figure_manifest_table",
    "forecast_final_evaluation_figure_manifest",
    "Figure manifest",
)

catalog = dbutils.widgets.get("catalog").strip()
model_schema = dbutils.widgets.get("model_schema").strip()
evaluation_schema = dbutils.widgets.get("evaluation_schema").strip()
selection_table = dbutils.widgets.get("selection_table").strip()
locked_prediction_table = dbutils.widgets.get("locked_prediction_table").strip()
evaluation_threshold_table = dbutils.widgets.get("evaluation_threshold_table").strip()
figure_volume = dbutils.widgets.get("figure_volume").strip()
manifest_table = dbutils.widgets.get("figure_manifest_table").strip()

selection = spark.table(qualified_name(catalog, model_schema, selection_table))
locked = spark.table(qualified_name(catalog, model_schema, locked_prediction_table))
gate = spark.table(qualified_name(catalog, evaluation_schema, evaluation_threshold_table))
run_ids = {row[0] for row in gate.select("forecast_final_run_id").distinct().collect()}
if len(run_ids) != 1:
    raise RuntimeError("Final forecast figures require exactly one finalization run")
forecast_final_run_id = next(iter(run_ids))
horizons = tuple(sorted(int(row[0]) for row in gate.select("horizon_years").distinct().collect()))
if horizons != (1, 3):
    raise RuntimeError(f"Expected one- and three-year horizons; found {horizons}")

# COMMAND ----------

generated_at = datetime.now(UTC)
build_id = generated_at.strftime("forecast-final-%Y%m%dT%H%M%S%fZ")
spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{evaluation_schema}`.`{figure_volume}`")
figure_directory = (
    Path("/Volumes")
    / catalog
    / evaluation_schema
    / figure_volume
    / "final_forecast"
    / f"build_id={build_id}"
)
figure_directory.mkdir(parents=True, exist_ok=False)

NAVY, BLUE, TEAL = "#17324D", "#3776AB", "#2A9D8F"
AMBER, RED, MUTED, GRID = "#E9A23B", "#C94C4C", "#5F6B76", "#D8DEE4"
plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": GRID,
        "axes.labelcolor": NAVY,
        "axes.titlecolor": NAVY,
        "xtick.color": NAVY,
        "ytick.color": NAVY,
        "font.size": 10,
    }
)
manifest_rows = []


def save_figure(
    sequence: int, stem: str, title: str, purpose: str, note: str, figure: object
) -> None:
    """Save one checked PNG and register it in the manifest."""

    file_name = f"{sequence:02d}_{stem}.png"
    path = figure_directory / file_name
    figure.text(0.01, 0.01, note, ha="left", va="bottom", fontsize=8.2, color=MUTED)
    figure.savefig(path, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    if path.stat().st_size < 10_000:
        raise RuntimeError(f"Forecast evaluation figure appears incomplete: {path}")
    manifest_rows.append(
        (
            build_id,
            sequence,
            file_name,
            title,
            purpose,
            str(path),
            forecast_final_run_id,
            generated_at.isoformat(),
        )
    )


selection_by_key = {
    (str(row["model_name"]), int(row["horizon_years"])): row.asDict()
    for row in selection.where(
        functions.col("forecast_final_run_id") == forecast_final_run_id
    ).collect()
}
gate_by_key = {
    (str(row["model_name"]), int(row["horizon_years"])): row.asDict()
    for row in gate.where(functions.col("forecast_final_run_id") == forecast_final_run_id).collect()
}
locked_means = {
    (str(row["model_name"]), int(row["horizon_years"])): row.asDict()
    for row in locked.groupBy("model_name", "horizon_years")
    .agg(
        functions.avg("target_cumulative_log_change").alias("mean_observed"),
        functions.avg("prediction_cumulative_log_change").alias("mean_prediction"),
    )
    .collect()
}
model_names = ("regularized_linear", "gradient_boosted_trees")
model_labels = {
    "regularized_linear": "Regularized linear",
    "gradient_boosted_trees": "Gradient-boosted trees",
}
expected_keys = {(model_name, horizon) for model_name in model_names for horizon in horizons}
if set(selection_by_key) != expected_keys or set(gate_by_key) != expected_keys:
    raise RuntimeError("Final figures require both supervised models at both horizons")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Development evidence versus later-period evaluation

# COMMAND ----------

figure, axes = plt.subplots(1, len(horizons), figsize=(14.2, 6.6), sharey=False)
for axis, horizon in zip(axes, horizons, strict=True):
    values = [
        selection_by_key[("regularized_linear", horizon)]["validation_mae_log_change"],
        gate_by_key[("regularized_linear", horizon)]["model_mae_log_change"],
        selection_by_key[("gradient_boosted_trees", horizon)]["validation_mae_log_change"],
        gate_by_key[("gradient_boosted_trees", horizon)]["model_mae_log_change"],
        gate_by_key[("regularized_linear", horizon)]["zero_change_mae_log_change"],
        gate_by_key[("regularized_linear", horizon)]["state_trend_mae_log_change"],
    ]
    labels = [
        "Linear\nvalidation",
        "Linear\nlater period",
        "GBT\nvalidation",
        "GBT\nlater period",
        "Zero change\nlater period",
        "State trend\nlater period",
    ]
    colors = [BLUE, NAVY, TEAL, "#176C62", AMBER, MUTED]
    bars = axis.bar(np.arange(len(values)), values, color=colors, width=0.72)
    axis.bar_label(bars, fmt="%.3f", padding=3, fontsize=8.4, color=NAVY)
    axis.set_xticks(np.arange(len(labels)), labels, fontsize=8.5)
    axis.set_title(f"{horizon}-year horizon", loc="left", fontsize=12, color=NAVY)
    axis.set_ylabel("MAE in cumulative log HPI change")
    axis.grid(axis="y", color=GRID, linewidth=0.8)
    axis.set_axisbelow(True)
figure.suptitle(
    "Both supervised models remain visible across validation and later evaluation",
    x=0.07,
    y=0.98,
    ha="left",
    fontsize=17,
    color=NAVY,
)
figure.text(
    0.07,
    0.91,
    "Lower is better. Zero change and state trend are comparison baselines, not replacements.",
    color=MUTED,
    fontsize=11,
)
figure.subplots_adjust(bottom=0.22, top=0.83, wspace=0.28)
save_figure(
    1,
    "validation_vs_locked_mae",
    "Supervised-model validation and later-period error",
    "Compares both project models with development evidence and simple later-period baselines.",
    "Source: governed validation and later-period evaluation. Baselines provide context and do "
    "not replace regularized linear regression or gradient-boosted trees.",
    figure,
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Model-specific interval coverage

# COMMAND ----------

coverage_keys = [(model_name, horizon) for horizon in horizons for model_name in model_names]
coverage = [gate_by_key[key]["empirical_interval_coverage"] * 100 for key in coverage_keys]
eligible = [bool(gate_by_key[key]["meets_evaluation_thresholds"]) for key in coverage_keys]
labels = [f"{horizon}-year\n{model_labels[model_name]}" for model_name, horizon in coverage_keys]
colors = [BLUE if model_name == "regularized_linear" else TEAL for model_name, _ in coverage_keys]
figure, axis = plt.subplots(figsize=(11.5, 6.4))
bars = axis.bar(np.arange(len(coverage)), coverage, width=0.58, color=colors, zorder=2)
for bar, passed in zip(bars, eligible, strict=True):
    if not passed:
        bar.set_hatch("//")
axis.bar_label(bars, labels=[f"{value:.1f}%" for value in coverage], padding=5, color=NAVY)
axis.axhline(90, color=NAVY, linewidth=1.5, linestyle="--", label="Target coverage (90%)", zorder=1)
axis.axhline(80, color=AMBER, linewidth=1.5, linestyle=":", label="Coverage floor (80%)", zorder=1)
axis.set_xticks(np.arange(len(labels)), labels)
axis.set_ylim(0, 108)
axis.set_yticks(np.arange(0, 101, 20))
axis.set_ylabel("Observed coverage (%)")
figure.suptitle(
    "How often did forecast ranges contain the outcome?",
    x=0.10,
    y=0.955,
    ha="left",
    fontsize=17,
    color=NAVY,
)
figure.text(
    0.10,
    0.885,
    "Hatching marks a result that missed at least one evaluation check.",
    fontsize=11,
    color=MUTED,
)
axis.grid(axis="y", color=GRID, linewidth=0.8)
axis.set_axisbelow(True)
figure.legend(
    loc="upper left",
    bbox_to_anchor=(0.10, 0.85),
    ncols=2,
    frameon=False,
    borderaxespad=0,
    labelcolor=NAVY,
)
figure.subplots_adjust(left=0.10, right=0.98, bottom=0.20, top=0.76)
save_figure(
    2,
    "locked_interval_coverage",
    "Locked-test forecast interval coverage",
    "Compares interval calibration for both supervised models at both horizons.",
    "Source: model-specific split-conformal intervals calibrated on reserved origins and "
    "evaluated on later outcomes.",
    figure,
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Direction of later-period forecast error

# COMMAND ----------

figure, axes = plt.subplots(1, len(horizons), figsize=(12.5, 6.2), sharey=True)
for axis, horizon in zip(axes, horizons, strict=True):
    observed = locked_means[("regularized_linear", horizon)]["mean_observed"]
    values = [
        observed,
        locked_means[("regularized_linear", horizon)]["mean_prediction"],
        locked_means[("gradient_boosted_trees", horizon)]["mean_prediction"],
    ]
    labels = ["Observed", "Regularized\nlinear", "Gradient-boosted\ntrees"]
    bars = axis.bar(np.arange(3), values, color=[AMBER, BLUE, TEAL], width=0.62)
    axis.bar_label(bars, fmt="%.3f", padding=3, fontsize=9, color=NAVY)
    axis.set_xticks(np.arange(3), labels)
    axis.set_title(f"{horizon}-year horizon", loc="left", color=NAVY)
    axis.axhline(0, color=GRID, linewidth=1)
    axis.grid(axis="y", color=GRID, linewidth=0.8)
    axis.set_axisbelow(True)
axes[0].set_ylabel("Mean cumulative log HPI change")
figure.suptitle(
    "Mean predictions reveal the direction of each model's later-period error",
    x=0.08,
    y=0.98,
    ha="left",
    fontsize=17,
    color=NAVY,
)
figure.text(
    0.08,
    0.90,
    "Bars summarize later-period evaluation tracts; they are not current forecasts.",
    fontsize=11,
    color=MUTED,
)
figure.subplots_adjust(bottom=0.18, top=0.82, wspace=0.18)
save_figure(
    3,
    "locked_mean_observed_vs_predicted",
    "Mean observed and predicted later-period HPI change",
    "Shows the direction and practical size of each supervised model's forecast error.",
    "Source: later-period predictions from the two frozen supervised model specifications.",
    figure,
)

# COMMAND ----------

if len(manifest_rows) != 3:
    raise RuntimeError(f"Expected three final forecast figures; found {len(manifest_rows)}")
manifest_schema = (
    "figure_build_id string, figure_sequence integer, figure_file_name string, "
    "figure_title string, figure_purpose string, figure_path string, "
    "source_forecast_final_run_id string, generated_at_utc_text string"
)
manifest = (
    spark.createDataFrame(manifest_rows, manifest_schema)
    .withColumn("generated_at_utc", functions.to_timestamp("generated_at_utc_text"))
    .drop("generated_at_utc_text")
)
manifest_name = qualified_name(catalog, evaluation_schema, manifest_table)
(
    manifest.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(manifest_name)
)
if spark.table(f"{catalog}.{evaluation_schema}.{manifest_table}").count() != 3:
    raise RuntimeError("Published final forecast figure manifest does not contain three rows")
display(spark.table(manifest_name).orderBy("figure_sequence"))
print(f"Published three final forecast figures for build {build_id}.")

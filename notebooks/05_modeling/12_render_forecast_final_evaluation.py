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
# MAGIC These figures communicate the frozen validation choice, once-opened locked test, interval
# MAGIC calibration, and release decision. They do not refit or change a selected method. Failed
# MAGIC horizons remain visible so the report can distinguish development from release evidence.

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
dbutils.widgets.text("release_gate_table", "forecast_release_gate", "Release gate")
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
release_gate_table = dbutils.widgets.get("release_gate_table").strip()
figure_volume = dbutils.widgets.get("figure_volume").strip()
manifest_table = dbutils.widgets.get("figure_manifest_table").strip()

selection = spark.table(qualified_name(catalog, model_schema, selection_table))
locked = spark.table(qualified_name(catalog, model_schema, locked_prediction_table))
gate = spark.table(qualified_name(catalog, evaluation_schema, release_gate_table))
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


selection_by_horizon = {
    int(row["horizon_years"]): row.asDict()
    for row in selection.where(
        functions.col("forecast_final_run_id") == forecast_final_run_id
    ).collect()
}
gate_by_horizon = {
    int(row["horizon_years"]): row.asDict()
    for row in gate.where(functions.col("forecast_final_run_id") == forecast_final_run_id).collect()
}
locked_means = {
    int(row["horizon_years"]): row.asDict()
    for row in locked.groupBy("horizon_years")
    .agg(
        functions.avg("target_cumulative_log_change").alias("mean_observed"),
        functions.avg("prediction_cumulative_log_change").alias("mean_prediction"),
    )
    .collect()
}
x = np.arange(len(horizons))
width = 0.19

# COMMAND ----------

# MAGIC %md
# MAGIC ## Development evidence versus the locked test

# COMMAND ----------

series = (
    (
        "Champion validation",
        [selection_by_horizon[h]["validation_mae_log_change"] for h in horizons],
        BLUE,
    ),
    (
        "Champion locked test",
        [gate_by_horizon[h]["champion_mae_log_change"] for h in horizons],
        NAVY,
    ),
    (
        "Zero-change locked test",
        [gate_by_horizon[h]["zero_change_mae_log_change"] for h in horizons],
        AMBER,
    ),
    (
        "State-trend locked test",
        [gate_by_horizon[h]["state_trend_mae_log_change"] for h in horizons],
        TEAL,
    ),
)
figure, axis = plt.subplots(figsize=(11.5, 6.4))
for index, (label, values, color) in enumerate(series):
    bars = axis.bar(x + (index - 1.5) * width, values, width, label=label, color=color)
    axis.bar_label(bars, fmt="%.3f", padding=3, fontsize=8.5, color=NAVY)
axis.set_xticks(x, [f"{h}-year horizon" for h in horizons])
axis.set_ylabel("Mean absolute error in cumulative log HPI change")
figure.suptitle(
    "The three-year model did not survive the later locked test",
    x=0.125,
    y=0.98,
    ha="left",
    fontsize=17,
    color=NAVY,
)
axis.set_title(
    "Lower is better. Locked results were opened only after model choices were frozen.",
    loc="left",
    pad=9,
    fontsize=11,
    color=MUTED,
)
axis.grid(axis="y", color=GRID, linewidth=0.8)
axis.set_axisbelow(True)
axis.legend(frameon=False, ncol=2, loc="upper left")
figure.subplots_adjust(bottom=0.18, top=0.84)
save_figure(
    1,
    "validation_vs_locked_mae",
    "Validation and locked-test forecast error",
    "Tests whether each frozen horizon generalized beyond development and simple baselines.",
    "Source: governed validation selection and once-opened locked test. The three-year "
    "champion was withheld because it was worse than zero-change.",
    figure,
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Interval coverage as a release requirement

# COMMAND ----------

coverage = [gate_by_horizon[h]["empirical_interval_coverage"] * 100 for h in horizons]
eligible = [bool(gate_by_horizon[h]["release_eligible"]) for h in horizons]
figure, axis = plt.subplots(figsize=(9.8, 6.2))
bars = axis.bar(x, coverage, width=0.55, color=[TEAL if value else RED for value in eligible])
axis.bar_label(bars, labels=[f"{value:.1f}%" for value in coverage], padding=4, color=NAVY)
axis.axhline(90, color=NAVY, linewidth=1.5, linestyle="--", label="Nominal coverage (90%)")
axis.axhline(80, color=AMBER, linewidth=1.5, linestyle=":", label="Release minimum (80%)")
axis.set_xticks(
    x,
    [
        f"{h}-year\n{'Published' if eligible[index] else 'Withheld'}"
        for index, h in enumerate(horizons)
    ],
)
axis.set_ylim(0, 100)
axis.set_ylabel("Locked outcomes inside the interval")
figure.suptitle(
    "Only the one-year uncertainty interval remained calibrated",
    x=0.125,
    y=0.98,
    ha="left",
    fontsize=17,
    color=NAVY,
)
axis.set_title(
    "The application requires useful point accuracy and reliable uncertainty coverage.",
    loc="left",
    pad=9,
    fontsize=11,
    color=MUTED,
)
axis.grid(axis="y", color=GRID, linewidth=0.8)
axis.set_axisbelow(True)
axis.legend(frameon=False, loc="lower left")
figure.subplots_adjust(bottom=0.19, top=0.88)
save_figure(
    2,
    "locked_interval_coverage",
    "Locked-test forecast interval coverage",
    "Explains why the one-year horizon is published and the three-year horizon is withheld.",
    "Source: split-conformal intervals calibrated on reserved origins and evaluated once on "
    "the locked temporal test.",
    figure,
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Direction of the locked-period miss

# COMMAND ----------

observed = [locked_means[h]["mean_observed"] for h in horizons]
predicted = [locked_means[h]["mean_prediction"] for h in horizons]
figure, axis = plt.subplots(figsize=(10.5, 6.2))
observed_bars = axis.bar(x - 0.16, observed, 0.32, color=TEAL, label="Observed")
predicted_bars = axis.bar(x + 0.16, predicted, 0.32, color=BLUE, label="Predicted")
axis.bar_label(observed_bars, fmt="%.3f", padding=3, fontsize=9, color=NAVY)
axis.bar_label(predicted_bars, fmt="%.3f", padding=3, fontsize=9, color=NAVY)
axis.set_xticks(x, [f"{h}-year horizon" for h in horizons])
axis.set_ylabel("Mean cumulative log HPI change")
figure.suptitle(
    "Persisting the 2022 state trend greatly overpredicted 2022–2025",
    x=0.125,
    y=0.98,
    ha="left",
    fontsize=17,
    color=NAVY,
)
axis.set_title(
    "Bars summarize eligible locked-test tracts; they are not current forecasts.",
    loc="left",
    pad=9,
    fontsize=11,
    color=MUTED,
)
axis.axhline(0, color=GRID, linewidth=1)
axis.grid(axis="y", color=GRID, linewidth=0.8)
axis.set_axisbelow(True)
axis.legend(frameon=False, loc="upper left")
figure.subplots_adjust(bottom=0.18, top=0.84)
save_figure(
    3,
    "locked_mean_observed_vs_predicted",
    "Mean observed and predicted locked-period HPI change",
    "Shows the direction and practical size of the three-year regime failure.",
    "Source: final locked-test predictions. The three-year state-trend baseline carried an "
    "unusually strong origin-year trend forward for three years.",
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

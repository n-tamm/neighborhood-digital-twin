# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Finalize forecasts, intervals, locked tests, and current predictions
# MAGIC
# MAGIC Run this notebook only after the team freezes one champion per horizon from job 500's
# MAGIC validation evidence. It uses calibration rows to estimate a 90% absolute-residual interval,
# MAGIC opens the locked temporal tests once without retuning, and refits the same specifications
# MAGIC for the latest current-tract origin. The output remains analytical until job 701 publishes
# MAGIC a validated application-serving release.

# COMMAND ----------

import sys
from pathlib import Path, PurePosixPath


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

import mlflow
from databricks.sdk import WorkspaceClient

from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.forecast_finalization import (
    FORECAST_CALIBRATION_PREDICTION_TABLE,
    FORECAST_CURRENT_PREDICTION_TABLE,
    FORECAST_INTERVAL_TABLE,
    FORECAST_LOCKED_TEST_PREDICTION_TABLE,
    FORECAST_LOCKED_TEST_SCORECARD_TABLE,
    FORECAST_SELECTION_TABLE,
    ChampionSpecification,
    build_forecast_finalization_run,
)

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("model_schema", "neighborhood_twin_model", "Model schema")
dbutils.widgets.text(
    "evaluation_schema", "neighborhood_twin_evaluation", "Evaluation schema"
)
dbutils.widgets.text("modeling_panel_table", "gold_modeling_panel", "Modeling panel")
dbutils.widgets.text(
    "validation_scorecard_table", "forecast_baseline_scorecard", "Validation scorecard"
)
dbutils.widgets.text("selection_table", FORECAST_SELECTION_TABLE, "Selection output")
dbutils.widgets.text(
    "calibration_prediction_table",
    FORECAST_CALIBRATION_PREDICTION_TABLE,
    "Calibration prediction output",
)
dbutils.widgets.text("interval_table", FORECAST_INTERVAL_TABLE, "Interval calibration output")
dbutils.widgets.text(
    "locked_test_prediction_table",
    FORECAST_LOCKED_TEST_PREDICTION_TABLE,
    "Locked-test prediction output",
)
dbutils.widgets.text(
    "locked_test_scorecard_table",
    FORECAST_LOCKED_TEST_SCORECARD_TABLE,
    "Locked-test scorecard output",
)
dbutils.widgets.text(
    "current_prediction_table",
    FORECAST_CURRENT_PREDICTION_TABLE,
    "Current prediction output",
)
dbutils.widgets.text(
    "champions",
    "1:gradient_boosted_trees,3:state_current_trend",
    "Frozen horizon:model mapping",
)
dbutils.widgets.text("linear_reg_param", "0.05", "Regularized-linear L2 parameter")
dbutils.widgets.text(
    "gbt_parameters", "1:2:50,3:4:30", "Horizon:maxDepth:maxIter mapping"
)
dbutils.widgets.text("interval_coverage", "0.90", "Nominal interval coverage")
dbutils.widgets.text(
    "mlflow_experiment",
    "/Shared/neighborhood-digital-twin/forecast-finalization",
    "MLflow experiment",
)


def _parse_champions(value: str) -> dict[int, str]:
    """Parse a comma-separated horizon:model mapping."""

    result = {}
    for item in value.split(","):
        horizon, model_name = item.strip().split(":", 1)
        result[int(horizon)] = model_name.strip()
    if not result:
        raise ValueError("champions must not be empty")
    return result


def _parse_gbt_parameters(value: str) -> dict[int, tuple[int, int]]:
    """Parse a comma-separated horizon:maxDepth:maxIter mapping."""

    result = {}
    for item in value.split(","):
        horizon, depth, iterations = item.strip().split(":")
        result[int(horizon)] = (int(depth), int(iterations))
    return result


catalog = dbutils.widgets.get("catalog").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
model_schema = dbutils.widgets.get("model_schema").strip()
evaluation_schema = dbutils.widgets.get("evaluation_schema").strip()
panel_table = dbutils.widgets.get("modeling_panel_table").strip()
validation_scorecard_table = dbutils.widgets.get("validation_scorecard_table").strip()
selection_table = dbutils.widgets.get("selection_table").strip()
calibration_prediction_table = dbutils.widgets.get("calibration_prediction_table").strip()
interval_table = dbutils.widgets.get("interval_table").strip()
locked_test_prediction_table = dbutils.widgets.get("locked_test_prediction_table").strip()
locked_test_scorecard_table = dbutils.widgets.get("locked_test_scorecard_table").strip()
current_prediction_table = dbutils.widgets.get("current_prediction_table").strip()
champions = _parse_champions(dbutils.widgets.get("champions"))
gbt_parameters = _parse_gbt_parameters(dbutils.widgets.get("gbt_parameters"))
reg_param = float(dbutils.widgets.get("linear_reg_param"))
coverage = float(dbutils.widgets.get("interval_coverage"))
experiment_path = dbutils.widgets.get("mlflow_experiment").strip()

expected_tables = (
    selection_table,
    calibration_prediction_table,
    interval_table,
    locked_test_prediction_table,
    locked_test_scorecard_table,
    current_prediction_table,
)
contract_tables = (
    FORECAST_SELECTION_TABLE,
    FORECAST_CALIBRATION_PREDICTION_TABLE,
    FORECAST_INTERVAL_TABLE,
    FORECAST_LOCKED_TEST_PREDICTION_TABLE,
    FORECAST_LOCKED_TEST_SCORECARD_TABLE,
    FORECAST_CURRENT_PREDICTION_TABLE,
)
if expected_tables != contract_tables:
    raise ValueError("Forecast finalization table names are fixed by the output contract")

specifications = tuple(
    ChampionSpecification(
        horizon_years=horizon,
        model_name=model_name,
        reg_param=reg_param,
        gbt_max_depth=gbt_parameters.get(horizon, (4, 50))[0],
        gbt_max_iter=gbt_parameters.get(horizon, (4, 50))[1],
    )
    for horizon, model_name in sorted(champions.items())
)
panel = spark.table(qualified_name(catalog, gold_schema, panel_table))
validation_scorecard = spark.table(
    qualified_name(catalog, evaluation_schema, validation_scorecard_table)
)

# COMMAND ----------


def ensure_experiment_parent(experiment: str) -> None:
    """Create the shared Workspace folder required by a nested MLflow experiment path."""

    if not experiment.startswith("/"):
        raise ValueError("The Databricks MLflow experiment path must be absolute")
    WorkspaceClient().workspace.mkdirs(str(PurePosixPath(experiment).parent))


ensure_experiment_parent(experiment_path)
mlflow.set_experiment(experiment_path)
with mlflow.start_run(run_name="frozen-forecast-finalization") as active_run:
    mlflow.log_params(
        {
            "champions": dbutils.widgets.get("champions"),
            "gbt_parameters": dbutils.widgets.get("gbt_parameters"),
            "linear_reg_param": reg_param,
            "interval_method": "split_conformal_absolute_residual",
            "interval_nominal_coverage": coverage,
            "locked_test_policy": "opened_once_after_frozen_selection_and_calibration_method",
            "training_label_rule": "target_end_year_strictly_before_prediction_origin",
        }
    )
    result = build_forecast_finalization_run(
        panel,
        validation_scorecard,
        specifications,
        coverage=coverage,
        run_id=active_run.info.run_id,
    )
    overall = result.locked_test_scorecard.where("slice_name = 'overall'").collect()
    for row in overall:
        stem = f"locked_h{row['horizon_years']}"
        mlflow.log_metric(f"{stem}_mae", float(row["mae_log_change"]))
        mlflow.log_metric(f"{stem}_rmse", float(row["rmse_log_change"]))
        mlflow.log_metric(
            f"{stem}_empirical_interval_coverage",
            float(row["empirical_interval_coverage"]),
        )
        mlflow.log_metric(
            f"{stem}_mean_interval_width_annualized_pct_points",
            float(row["mean_interval_width_annualized_pct_points"]),
        )

# COMMAND ----------

outputs = (
    (result.selection, model_schema, selection_table),
    (result.calibration_predictions, model_schema, calibration_prediction_table),
    (result.intervals, evaluation_schema, interval_table),
    (result.locked_test_predictions, model_schema, locked_test_prediction_table),
    (result.locked_test_scorecard, evaluation_schema, locked_test_scorecard_table),
    (result.current_predictions, model_schema, current_prediction_table),
)
for frame, schema, table in outputs:
    (
        frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(qualified_name(catalog, schema, table))
    )

display(result.selection.orderBy("horizon_years"))
display(result.intervals.orderBy("horizon_years"))
display(result.locked_test_scorecard.where("slice_name = 'overall'").orderBy("horizon_years"))
print(f"Forecast finalization run: {result.run_id}")

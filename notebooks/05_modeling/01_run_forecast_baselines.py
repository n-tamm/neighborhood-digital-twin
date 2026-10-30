# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Forecasting baseline workflow
# MAGIC
# MAGIC This development workflow fits five fixed forecasting baselines and one regularized linear
# MAGIC model against the governed split contract. It publishes validation predictions and sliced
# MAGIC scorecards only. Locked temporal test rows remain closed, and calibration rows are reserved
# MAGIC for later interval work.

# COMMAND ----------

import sys
from pathlib import Path, PurePosixPath


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

import mlflow
from databricks.sdk import WorkspaceClient

from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.forecasting import (
    FORECAST_PREDICTION_TABLE,
    FORECAST_SCORECARD_TABLE,
    LINEAR_FEATURE_COLUMNS,
    build_forecast_baseline_run,
)

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("model_schema", "neighborhood_twin_model", "Model-output schema")
dbutils.widgets.text(
    "evaluation_schema", "neighborhood_twin_evaluation", "Model-evaluation schema"
)
dbutils.widgets.text("modeling_panel_table", "gold_modeling_panel", "Modeling panel")
dbutils.widgets.text("prediction_table", FORECAST_PREDICTION_TABLE, "Prediction output")
dbutils.widgets.text("scorecard_table", FORECAST_SCORECARD_TABLE, "Scorecard output")
dbutils.widgets.text("reg_param", "0.05", "L2 regularization parameter")
dbutils.widgets.text(
    "mlflow_experiment", "/Shared/neighborhood-digital-twin/forecast-baselines", "MLflow experiment"
)

catalog = dbutils.widgets.get("catalog").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
model_schema = dbutils.widgets.get("model_schema").strip()
evaluation_schema = dbutils.widgets.get("evaluation_schema").strip()
panel_table = dbutils.widgets.get("modeling_panel_table").strip()
prediction_table = dbutils.widgets.get("prediction_table").strip()
scorecard_table = dbutils.widgets.get("scorecard_table").strip()
reg_param = float(dbutils.widgets.get("reg_param"))
experiment_path = dbutils.widgets.get("mlflow_experiment").strip()

panel = spark.table(qualified_name(catalog, gold_schema, panel_table))

# COMMAND ----------


def ensure_experiment_parent(experiment: str) -> None:
    """Create the shared Workspace folder required by a nested MLflow experiment path."""

    if not experiment.startswith("/"):
        raise ValueError("The Databricks MLflow experiment path must be absolute")
    WorkspaceClient().workspace.mkdirs(str(PurePosixPath(experiment).parent))


ensure_experiment_parent(experiment_path)
mlflow.set_experiment(experiment_path)
with mlflow.start_run(run_name="interpretable-forecast-baselines") as active_run:
    mlflow.log_params(
        {
            "target": "target_cumulative_log_change",
            "evaluation_role": "validation",
            "locked_test_access": "prohibited",
            "reg_param": reg_param,
            "linear_feature_count": len(LINEAR_FEATURE_COLUMNS),
            "linear_features": ",".join(LINEAR_FEATURE_COLUMNS),
        }
    )
    result = build_forecast_baseline_run(
        panel,
        run_id=active_run.info.run_id,
        reg_param=reg_param,
    )
    overall = (
        result.scorecard.where("slice_name = 'overall'")
        .select(
            "model_name",
            "horizon_years",
            "mae_log_change",
            "rmse_log_change",
            "mean_error_log_change",
            "p90_absolute_error_log_change",
            "r_squared",
            "mae_skill_vs_zero_change",
        )
        .collect()
    )
    for row in overall:
        metric_stem = f"{row['model_name']}_h{row['horizon_years']}"
        mlflow.log_metric(f"{metric_stem}_mae", float(row["mae_log_change"]))
        mlflow.log_metric(f"{metric_stem}_rmse", float(row["rmse_log_change"]))
        mlflow.log_metric(f"{metric_stem}_mean_error", float(row["mean_error_log_change"]))
        mlflow.log_metric(
            f"{metric_stem}_p90_absolute_error",
            float(row["p90_absolute_error_log_change"]),
        )
        if row["r_squared"] is not None:
            mlflow.log_metric(f"{metric_stem}_r_squared", float(row["r_squared"]))
        if row["mae_skill_vs_zero_change"] is not None:
            mlflow.log_metric(
                f"{metric_stem}_mae_skill_vs_zero_change",
                float(row["mae_skill_vs_zero_change"]),
            )

# COMMAND ----------

prediction_name = qualified_name(catalog, model_schema, prediction_table)
scorecard_name = qualified_name(catalog, evaluation_schema, scorecard_table)
(
    result.predictions.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(prediction_name)
)
(
    result.scorecard.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(scorecard_name)
)

if spark.table(prediction_name).where("temporal_role <> 'validation'").limit(1).count():
    raise RuntimeError("Published predictions contain rows outside the validation role")
if spark.table(scorecard_name).where("observation_count <= 0").limit(1).count():
    raise RuntimeError("Published scorecard contains an empty evaluation slice")

display(
    spark.table(scorecard_name)
    .where("slice_name = 'overall'")
    .orderBy("horizon_years", "mae_log_change")
)
print(f"Published validation predictions to {prediction_name}.")
print(f"Published validation scorecards to {scorecard_name}.")
print(f"MLflow run: {result.run_id}")

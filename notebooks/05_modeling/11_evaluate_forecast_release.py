# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Evaluate both supervised forecast models
# MAGIC
# MAGIC This workflow does not select, replace, or refit a model. It evaluates regularized linear
# MAGIC regression and gradient-boosted trees separately at each horizon. The threshold fields
# MAGIC record whether each result has at least 1,000 observations, beats zero change on MAE, and
# MAGIC attains interval coverage no more than ten percentage points below nominal. Results that
# MAGIC miss a threshold remain available with a warning; a baseline never replaces either model.

# COMMAND ----------

import sys
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

from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.forecast_finalization import (
    FORECAST_LOCKED_TEST_PREDICTION_TABLE,
    FORECAST_LOCKED_TEST_SCORECARD_TABLE,
)
from neighborhood_twin.forecast_release import (
    FORECAST_EVALUATION_THRESHOLD_TABLE,
    ForecastEvaluationPolicy,
    build_forecast_evaluation_thresholds,
    validate_forecast_evaluation_thresholds,
)

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("model_schema", "neighborhood_twin_model", "Model schema")
dbutils.widgets.text("evaluation_schema", "neighborhood_twin_evaluation", "Evaluation schema")
dbutils.widgets.text(
    "locked_prediction_table",
    FORECAST_LOCKED_TEST_PREDICTION_TABLE,
    "Locked-test predictions",
)
dbutils.widgets.text(
    "locked_scorecard_table",
    FORECAST_LOCKED_TEST_SCORECARD_TABLE,
    "Locked-test scorecard",
)
dbutils.widgets.text(
    "evaluation_threshold_table",
    FORECAST_EVALUATION_THRESHOLD_TABLE,
    "Evaluation threshold output",
)
dbutils.widgets.text("minimum_observation_count", "1000", "Minimum locked rows")
dbutils.widgets.text(
    "interval_coverage_tolerance",
    "0.10",
    "Allowed shortfall from nominal interval coverage",
)

catalog = dbutils.widgets.get("catalog").strip()
model_schema = dbutils.widgets.get("model_schema").strip()
evaluation_schema = dbutils.widgets.get("evaluation_schema").strip()
locked_prediction_table = dbutils.widgets.get("locked_prediction_table").strip()
locked_scorecard_table = dbutils.widgets.get("locked_scorecard_table").strip()
evaluation_threshold_table = dbutils.widgets.get("evaluation_threshold_table").strip()
if (
    locked_prediction_table,
    locked_scorecard_table,
    evaluation_threshold_table,
) != (
    FORECAST_LOCKED_TEST_PREDICTION_TABLE,
    FORECAST_LOCKED_TEST_SCORECARD_TABLE,
    FORECAST_EVALUATION_THRESHOLD_TABLE,
):
    raise ValueError("Forecast evaluation table names are fixed by the output contract")

locked_predictions = spark.table(qualified_name(catalog, model_schema, locked_prediction_table))
locked_scorecard = spark.table(qualified_name(catalog, evaluation_schema, locked_scorecard_table))
expected_horizons = tuple(
    sorted(int(row[0]) for row in locked_predictions.select("horizon_years").distinct().collect())
)
policy = ForecastEvaluationPolicy(
    minimum_observation_count=int(dbutils.widgets.get("minimum_observation_count")),
    interval_coverage_tolerance=float(dbutils.widgets.get("interval_coverage_tolerance")),
)

# COMMAND ----------

evaluation_thresholds = build_forecast_evaluation_thresholds(
    locked_predictions,
    locked_scorecard,
    policy=policy,
)
validate_forecast_evaluation_thresholds(evaluation_thresholds, expected_horizons)
(
    evaluation_thresholds.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(qualified_name(catalog, evaluation_schema, evaluation_threshold_table))
)

display(evaluation_thresholds.orderBy("horizon_years", "model_name"))
print(
    f"Published {evaluation_thresholds.count()} forecast model evaluation records to "
    f"{catalog}.{evaluation_schema}.{evaluation_threshold_table}."
)

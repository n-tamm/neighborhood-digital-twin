# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Evaluate the locked forecast release gate
# MAGIC
# MAGIC This workflow does not select or refit a model. It converts the already frozen locked-test
# MAGIC evidence from job 504 into a production decision for each horizon. A horizon must have at
# MAGIC least 1,000 locked observations, beat zero-change on MAE, and attain interval coverage no
# MAGIC more than ten percentage points below its nominal level. Failed horizons remain recorded
# MAGIC but are withheld from application serving.

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
    FORECAST_RELEASE_GATE_TABLE,
    ForecastReleaseGatePolicy,
    build_forecast_release_gate,
    validate_forecast_release_gate,
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
dbutils.widgets.text("release_gate_table", FORECAST_RELEASE_GATE_TABLE, "Release gate")
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
release_gate_table = dbutils.widgets.get("release_gate_table").strip()
if (
    locked_prediction_table,
    locked_scorecard_table,
    release_gate_table,
) != (
    FORECAST_LOCKED_TEST_PREDICTION_TABLE,
    FORECAST_LOCKED_TEST_SCORECARD_TABLE,
    FORECAST_RELEASE_GATE_TABLE,
):
    raise ValueError("Forecast release-gate table names are fixed by the output contract")

locked_predictions = spark.table(qualified_name(catalog, model_schema, locked_prediction_table))
locked_scorecard = spark.table(qualified_name(catalog, evaluation_schema, locked_scorecard_table))
expected_horizons = tuple(
    sorted(int(row[0]) for row in locked_predictions.select("horizon_years").distinct().collect())
)
policy = ForecastReleaseGatePolicy(
    minimum_observation_count=int(dbutils.widgets.get("minimum_observation_count")),
    interval_coverage_tolerance=float(dbutils.widgets.get("interval_coverage_tolerance")),
)

# COMMAND ----------

release_gate = build_forecast_release_gate(
    locked_predictions,
    locked_scorecard,
    policy=policy,
)
validate_forecast_release_gate(release_gate, expected_horizons)
(
    release_gate.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(qualified_name(catalog, evaluation_schema, release_gate_table))
)

display(release_gate.orderBy("horizon_years"))
print(
    f"Published {release_gate.count()} frozen forecast release decisions to "
    f"{catalog}.{evaluation_schema}.{release_gate_table}."
)

# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Publish current forecast serving products
# MAGIC
# MAGIC This job reads only the frozen current predictions produced by job 504. It creates a compact
# MAGIC forecast table and an explicit availability row for every current tract and horizon. The
# MAGIC shared serving manifest is appended last, so an incomplete release cannot be selected by
# MAGIC the application.

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

from pyspark.sql import functions

from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.forecast_finalization import FORECAST_CURRENT_PREDICTION_TABLE
from neighborhood_twin.forecast_serving import (
    FORECAST_SERVING_AVAILABILITY_TABLE,
    FORECAST_SERVING_CURRENT_TABLE,
    SERVING_RELEASE_MANIFEST_TABLE,
    build_forecast_availability,
    build_forecast_release_manifest,
    build_serving_forecasts,
    new_forecast_serving_release,
    validate_forecast_serving_outputs,
)

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("model_schema", "neighborhood_twin_model", "Model schema")
dbutils.widgets.text("serving_schema", "neighborhood_twin_serving", "Serving schema")
dbutils.widgets.text(
    "current_profile_table", "gold_tract_profile_current", "Current tract profile"
)
dbutils.widgets.text(
    "current_prediction_table",
    FORECAST_CURRENT_PREDICTION_TABLE,
    "Frozen current predictions",
)
dbutils.widgets.text(
    "forecast_table", FORECAST_SERVING_CURRENT_TABLE, "Serving forecast output"
)
dbutils.widgets.text(
    "availability_table",
    FORECAST_SERVING_AVAILABILITY_TABLE,
    "Serving forecast availability",
)
dbutils.widgets.text(
    "manifest_table", SERVING_RELEASE_MANIFEST_TABLE, "Shared serving manifest"
)

catalog = dbutils.widgets.get("catalog").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
model_schema = dbutils.widgets.get("model_schema").strip()
serving_schema = dbutils.widgets.get("serving_schema").strip()
current_profile_table = dbutils.widgets.get("current_profile_table").strip()
current_prediction_table = dbutils.widgets.get("current_prediction_table").strip()
forecast_table = dbutils.widgets.get("forecast_table").strip()
availability_table = dbutils.widgets.get("availability_table").strip()
manifest_table = dbutils.widgets.get("manifest_table").strip()
if (
    current_prediction_table,
    forecast_table,
    availability_table,
    manifest_table,
) != (
    FORECAST_CURRENT_PREDICTION_TABLE,
    FORECAST_SERVING_CURRENT_TABLE,
    FORECAST_SERVING_AVAILABILITY_TABLE,
    SERVING_RELEASE_MANIFEST_TABLE,
):
    raise ValueError("Forecast serving table names are fixed by the release contract")

current_profile = spark.table(qualified_name(catalog, gold_schema, current_profile_table))
current_predictions = spark.table(
    qualified_name(catalog, model_schema, current_prediction_table)
)
as_of_years = {
    int(row[0])
    for row in current_predictions.select("forecast_origin_year").distinct().collect()
}
horizons = tuple(
    sorted(
        int(row[0])
        for row in current_predictions.select("horizon_years").distinct().collect()
    )
)
readiness_ids = {
    row[0]
    for row in current_predictions.select("model_readiness_build_id").distinct().collect()
}
final_run_ids = {
    row[0]
    for row in current_predictions.select("forecast_final_run_id").distinct().collect()
}
if len(as_of_years) != 1 or len(readiness_ids) != 1 or len(final_run_ids) != 1:
    raise RuntimeError("Current predictions must contain one as-of year and one source lineage")
release = new_forecast_serving_release(
    as_of_year=next(iter(as_of_years)),
    horizons=horizons,
    model_readiness_build_id=next(iter(readiness_ids)),
    forecast_final_run_id=next(iter(final_run_ids)),
)

# COMMAND ----------

forecasts = build_serving_forecasts(current_predictions, current_profile, release).cache()
availability = build_forecast_availability(current_profile, forecasts, release).cache()
row_counts = validate_forecast_serving_outputs(forecasts, availability, release)
manifest = build_forecast_release_manifest(spark, release, row_counts)

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{serving_schema}`")
published = ((forecast_table, forecasts), (availability_table, availability))
for table, frame in published:
    raw_name = f"{catalog}.{serving_schema}.{table}"
    table_name = qualified_name(catalog, serving_schema, table)
    if spark.catalog.tableExists(raw_name) and spark.table(raw_name).where(
        functions.col("serving_release_id") == release.release_id
    ).limit(1).count():
        raise RuntimeError(f"Serving release already exists in {raw_name}")
    writer = frame.write.format("delta").mode("append")
    if not spark.catalog.tableExists(raw_name):
        writer = writer.partitionBy("serving_release_id")
    writer.saveAsTable(table_name)

# Publish the activation record last.
manifest_raw_name = f"{catalog}.{serving_schema}.{manifest_table}"
manifest_name = qualified_name(catalog, serving_schema, manifest_table)
if spark.catalog.tableExists(manifest_raw_name) and spark.table(manifest_raw_name).where(
    functions.col("serving_release_id") == release.release_id
).limit(1).count():
    raise RuntimeError(f"Serving release already exists in {manifest_raw_name}")
manifest_writer = manifest.write.format("delta").mode("append")
if not spark.catalog.tableExists(manifest_raw_name):
    manifest_writer = manifest_writer.partitionBy("serving_release_id")
manifest_writer.saveAsTable(manifest_name)

for table, expected_count in row_counts.items():
    published_count = spark.table(f"{catalog}.{serving_schema}.{table}").where(
        functions.col("serving_release_id") == release.release_id
    ).count()
    if published_count != expected_count:
        raise RuntimeError(
            f"Published count differs for {table}: "
            f"expected={expected_count}, actual={published_count}"
        )
published_manifest = spark.table(manifest_raw_name).where(
    functions.col("serving_release_id") == release.release_id
)
if published_manifest.count() != len(row_counts):
    raise RuntimeError("Forecast manifest does not contain both serving tables")

display(
    availability.groupBy("horizon_years", "availability_reason")
    .count()
    .orderBy("horizon_years", "availability_reason")
)
display(forecasts.orderBy("horizon_years", "geoid_2020").limit(20))
display(published_manifest.orderBy("table_name"))
print(f"Activated forecast serving release {release.release_id} in {serving_schema}.")

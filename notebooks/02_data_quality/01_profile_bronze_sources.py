# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Bronze source quality profile
# MAGIC
# MAGIC **Question:** Did the current bronze sources arrive with the expected grain, keys,
# MAGIC parseability, lineage, and tract coverage?
# MAGIC
# MAGIC **Inputs:** FHFA tract HPI, focused ACS five-year tract extracts, and the source
# MAGIC snapshot manifest in the configured development schema.
# MAGIC
# MAGIC **Output grain:** One row per profiling run, table, metric, and optional dimension in
# MAGIC `bronze_quality_metrics`. This is an operational quality artifact, not a modeling table.

# COMMAND ----------

import sys
from pathlib import Path


def _add_repository_source() -> None:
    """Make the repository package importable from the deployed bundle."""

    candidates = (Path.cwd(), *Path.cwd().parents)
    for candidate in candidates:
        source_root = candidate / "src"
        if (source_root / "neighborhood_twin").is_dir():
            sys.path.insert(0, str(source_root))
            return
    raise RuntimeError("Could not find src/neighborhood_twin in the deployed bundle")


_add_repository_source()

# COMMAND ----------

from pyspark.sql import functions as functions

from neighborhood_twin.validate import (
    hard_failures,
    profile_bronze_tables,
    write_quality_metrics,
)

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("bronze_schema", "neighborhood_twin_bronze", "Bronze schema")
dbutils.widgets.text("quality_schema", "neighborhood_twin_quality", "Quality schema")
dbutils.widgets.text("quality_table", "bronze_quality_metrics", "Quality metric table")

catalog = dbutils.widgets.get("catalog").strip()
bronze_schema = dbutils.widgets.get("bronze_schema").strip()
quality_schema = dbutils.widgets.get("quality_schema").strip()
quality_table = dbutils.widgets.get("quality_table").strip()

# COMMAND ----------

metrics = profile_bronze_tables(spark, catalog=catalog, schema=bronze_schema)
quality_table_name = write_quality_metrics(
    spark,
    metrics,
    catalog=catalog,
    schema=quality_schema,
    table=quality_table,
)
quality_run_id = metrics[0].quality_run_id

latest_metrics = spark.table(f"{catalog}.{quality_schema}.{quality_table}").where(
    functions.col("quality_run_id") == quality_run_id
)
status_order = (
    functions.when(functions.col("status") == "fail", 0)
    .when(functions.col("status") == "warn", 1)
    .when(functions.col("status") == "pass", 2)
    .otherwise(3)
)
display(
    latest_metrics.orderBy(
        status_order,
        "metric_group",
        "table_name",
        "metric_name",
        "dimension",
    )
)

failure_metrics = hard_failures(metrics)
warning_count = sum(metric.status == "warn" for metric in metrics)
print(
    f"Wrote {len(metrics)} metrics to {quality_table_name} for run {quality_run_id}; "
    f"failures={len(failure_metrics)}, warnings={warning_count}."
)
if failure_metrics:
    failure_names = ", ".join(
        f"{metric.table_name}:{metric.metric_name}:{metric.dimension}"
        for metric in failure_metrics
    )
    raise RuntimeError(f"Bronze quality profile found hard failures: {failure_names}")

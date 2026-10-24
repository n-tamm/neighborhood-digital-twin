# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Build the canonical 2020 tract dimension
# MAGIC
# MAGIC The relationship file defines the complete tract universe. Simplified display geometry is
# MAGIC attached when available but never determines whether a tract exists.

# COMMAND ----------

import sys
from pathlib import Path


def _add_repository_source() -> None:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        source_root = candidate / "src"
        if (source_root / "neighborhood_twin").is_dir():
            sys.path.insert(0, str(source_root))
            return
    raise RuntimeError("Could not find src/neighborhood_twin in the deployed bundle")


_add_repository_source()

# COMMAND ----------

from pyspark.sql import functions

from neighborhood_twin.canonical import prepare_canonical_build, publish_canonical_build
from neighborhood_twin.validate import hard_failures, write_quality_metrics

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("schema", "neighborhood_twin_dev", "Project schema")
dbutils.widgets.text("table", "silver_canonical_tract_2020", "Canonical tract table")
dbutils.widgets.text(
    "quality_table",
    "canonical_geography_quality_metrics",
    "Append-only canonical geography quality table",
)

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
table = dbutils.widgets.get("table").strip()
quality_table = dbutils.widgets.get("quality_table").strip()

# COMMAND ----------

build = prepare_canonical_build(spark, catalog=catalog, schema=schema, table=table)
quality_table_name = write_quality_metrics(
    spark,
    build.metrics,
    catalog=catalog,
    schema=schema,
    table=quality_table,
)
failures = hard_failures(build.metrics)
if failures:
    names = ", ".join(metric.metric_name for metric in failures)
    raise RuntimeError(f"Canonical geography checks failed before publication: {names}")

table_name = publish_canonical_build(
    build,
    catalog=catalog,
    schema=schema,
    table=table,
)
display(
    spark.table(quality_table_name)
    .where(functions.col("quality_run_id") == build.build_id)
    .orderBy("metric_group", "metric_name")
)
print(f"Published {table_name} for build {build.build_id}.")

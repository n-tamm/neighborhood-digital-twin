# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Build current analytical products
# MAGIC
# MAGIC Publishes one complete canonical tract profile plus transparent similarity,
# MAGIC forecasting, and three-state application-testing cohorts. Cohort filters do not
# MAGIC redefine the national project scope.

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

from neighborhood_twin.products import prepare_product_build, publish_product_build
from neighborhood_twin.validate import hard_failures, write_quality_metrics

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("silver_schema", "neighborhood_twin_silver", "Silver schema")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("quality_schema", "neighborhood_twin_quality", "Quality schema")
dbutils.widgets.text("demo_state_fips", "04,26,42", "Application demo state FIPS codes")
dbutils.widgets.text("quality_table", "gold_quality_metrics", "Gold quality table")

catalog = dbutils.widgets.get("catalog").strip()
silver_schema = dbutils.widgets.get("silver_schema").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
quality_schema = dbutils.widgets.get("quality_schema").strip()
demo_state_fips = dbutils.widgets.get("demo_state_fips").strip()
quality_table = dbutils.widgets.get("quality_table").strip()

# COMMAND ----------

build = prepare_product_build(
    spark,
    catalog=catalog,
    schema=gold_schema,
    silver_schema=silver_schema,
    demo_state_fips=demo_state_fips,
)
quality_table_name = write_quality_metrics(
    spark,
    build.metrics,
    catalog=catalog,
    schema=quality_schema,
    table=quality_table,
)
failures = hard_failures(build.metrics)
if failures:
    names = ", ".join(metric.metric_name for metric in failures)
    raise RuntimeError(f"Gold product checks failed before publication: {names}")

published = publish_product_build(build, catalog=catalog, schema=gold_schema)
display(
    spark.table(quality_table_name)
    .where(functions.col("quality_run_id") == build.build_id)
    .orderBy("table_name", "metric_group", "metric_name")
)
print(f"Published {len(published)} current analytical products for build {build.build_id}.")

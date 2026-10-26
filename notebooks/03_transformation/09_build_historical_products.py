# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Build historical gold products
# MAGIC
# MAGIC This job publishes explicit tract-vintage coverage, the eligible historical ACS
# MAGIC neighborhood-state panel, and direct one-, three-, and five-year FHFA targets. Pre-2020
# MAGIC ACS rows are limited to the documented stable 2010-to-2020 tract subset. Excluded rows
# MAGIC remain visible in the coverage table rather than disappearing silently.

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
    raise RuntimeError("Could not find src/neighborhood_twin in the deployed bundle")


_add_repository_source()

# COMMAND ----------

from pyspark.sql import functions

from neighborhood_twin.historical import (
    prepare_historical_build,
    publish_historical_build,
)
from neighborhood_twin.validate import hard_failures, write_quality_metrics

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("silver_schema", "neighborhood_twin_silver", "Silver schema")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("quality_schema", "neighborhood_twin_quality", "Quality schema")
dbutils.widgets.text("quality_table", "gold_quality_metrics", "Gold quality table")
dbutils.widgets.text("forecast_horizons", "1,3,5", "Forecast horizons in years")

catalog = dbutils.widgets.get("catalog").strip()
silver_schema = dbutils.widgets.get("silver_schema").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
quality_schema = dbutils.widgets.get("quality_schema").strip()
quality_table = dbutils.widgets.get("quality_table").strip()
horizons = tuple(
    int(value.strip())
    for value in dbutils.widgets.get("forecast_horizons").split(",")
    if value.strip()
)

# COMMAND ----------

build = prepare_historical_build(
    spark,
    catalog=catalog,
    silver_schema=silver_schema,
    gold_schema=gold_schema,
    horizons=horizons,
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
    names = ", ".join(
        f"{metric.table_name}:{metric.metric_name}" for metric in failures
    )
    raise RuntimeError(f"Historical gold checks failed before publication: {names}")

published = publish_historical_build(build, catalog=catalog, schema=gold_schema)

# COMMAND ----------

for table_name in published:
    print(f"Published {table_name}: {spark.table(table_name).count():,} rows")
display(
    spark.table(quality_table_name)
    .where(functions.col("quality_run_id") == build.build_id)
    .orderBy("table_name", "metric_group", "metric_name", "dimension")
)

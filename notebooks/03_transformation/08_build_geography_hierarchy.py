# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Build the valid geographic hierarchy
# MAGIC
# MAGIC This job publishes separate country, Census region, Census division, state, county, and
# MAGIC tract dimensions for the 50 states and District of Columbia. It does not force ZIP/ZCTA,
# MAGIC metro, or territory records into a hierarchy where the relationship is not valid.

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

from neighborhood_twin.geography_hierarchy import (
    prepare_geography_hierarchy_build,
    publish_geography_hierarchy_build,
)
from neighborhood_twin.validate import hard_failures, write_quality_metrics

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("silver_schema", "neighborhood_twin_silver", "Silver schema")
dbutils.widgets.text("quality_schema", "neighborhood_twin_quality", "Quality schema")
dbutils.widgets.text(
    "quality_table",
    "geography_hierarchy_quality_metrics",
    "Append-only geography hierarchy quality table",
)

catalog = dbutils.widgets.get("catalog").strip()
silver_schema = dbutils.widgets.get("silver_schema").strip()
quality_schema = dbutils.widgets.get("quality_schema").strip()
quality_table = dbutils.widgets.get("quality_table").strip()

# COMMAND ----------

build = prepare_geography_hierarchy_build(
    spark,
    catalog=catalog,
    silver_schema=silver_schema,
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
    raise RuntimeError(f"Geography hierarchy checks failed before publication: {names}")

published = publish_geography_hierarchy_build(
    build,
    catalog=catalog,
    silver_schema=silver_schema,
)
display(
    spark.table(quality_table_name)
    .where(functions.col("quality_run_id") == build.build_id)
    .orderBy("table_name", "metric_group", "metric_name")
)
print(f"Published {len(published)} geography dimensions for build {build.build_id}.")

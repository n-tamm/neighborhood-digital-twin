# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Build the Connecticut tract-vintage bridge
# MAGIC
# MAGIC Connecticut replaced its former counties with planning regions beginning in the 2022
# MAGIC data products, changing tract GEOIDs even where tract identity remained stable. This job
# MAGIC maps the unique non-water tract codes across the 2020 and 2024 TIGER vintages. Water-only
# MAGIC tracts remain explicit reconciliation exceptions and never receive demographic values.

# COMMAND ----------

import sys
from pathlib import Path


def _add_repository_source() -> None:
    candidates = (Path.cwd(), *Path.cwd().parents)
    for candidate in candidates:
        source_root = candidate / "src"
        if (source_root / "neighborhood_twin").is_dir():
            sys.path.insert(0, str(source_root))
            return
    raise RuntimeError("Could not find src/neighborhood_twin in the deployed bundle")


_add_repository_source()

# COMMAND ----------

from pyspark.sql import functions

from neighborhood_twin.connecticut import (
    prepare_connecticut_bridge_build,
    publish_connecticut_bridge_build,
)
from neighborhood_twin.validate import hard_failures, write_quality_metrics

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("schema", "neighborhood_twin_dev", "Project schema")
dbutils.widgets.text(
    "bridge_table",
    "silver_connecticut_tract_bridge_2020_2024",
    "Connecticut tract bridge",
)
dbutils.widgets.text(
    "quality_table", "geography_quality_metrics", "Append-only geography quality table"
)

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
bridge_table = dbutils.widgets.get("bridge_table").strip()
quality_table = dbutils.widgets.get("quality_table").strip()

# COMMAND ----------

build = prepare_connecticut_bridge_build(
    spark,
    catalog=catalog,
    schema=schema,
    bridge_table=bridge_table,
)
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
    raise RuntimeError(f"Connecticut bridge checks failed before publication: {names}")

published = publish_connecticut_bridge_build(
    build,
    catalog=catalog,
    schema=schema,
    bridge_table=bridge_table,
)
display(
    spark.table(quality_table_name)
    .where(functions.col("quality_run_id") == build.build_id)
    .orderBy("metric_group", "metric_name")
)
print(f"Published {published} for build {build.build_id}.")

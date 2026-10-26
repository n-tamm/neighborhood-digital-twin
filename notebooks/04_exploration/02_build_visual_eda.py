# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Build visual EDA summaries
# MAGIC
# MAGIC This job creates small governed tables for housing-composition coverage, differences
# MAGIC between current forecast candidates and excluded current-ACS tracts, and yearly FHFA
# MAGIC behavior. The separate rendering task uses these contracts to make repeatable figures.

# COMMAND ----------

import sys
from pathlib import Path


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

from pyspark.sql import functions

from neighborhood_twin.validate import hard_failures, write_quality_metrics
from neighborhood_twin.visual_exploration import (
    prepare_visual_eda_build,
    publish_visual_eda_build,
)

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("silver_schema", "neighborhood_twin_silver", "Silver schema")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("quality_schema", "neighborhood_twin_quality", "Quality schema")
dbutils.widgets.text("quality_table", "eda_readiness_quality_metrics", "EDA quality table")
dbutils.widgets.text("pilot_state_fips", "04,26,42", "Pilot state FIPS codes")

catalog = dbutils.widgets.get("catalog").strip()
silver_schema = dbutils.widgets.get("silver_schema").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
quality_schema = dbutils.widgets.get("quality_schema").strip()
quality_table = dbutils.widgets.get("quality_table").strip()
pilot_state_fips = dbutils.widgets.get("pilot_state_fips").strip()

# COMMAND ----------

build = prepare_visual_eda_build(
    spark,
    catalog=catalog,
    silver_schema=silver_schema,
    gold_schema=gold_schema,
    pilot_state_fips=pilot_state_fips,
)
quality_name = write_quality_metrics(
    spark,
    build.metrics,
    catalog=catalog,
    schema=quality_schema,
    table=quality_table,
)
failures = hard_failures(build.metrics)
if failures:
    raise RuntimeError(
        "Visual EDA checks failed before publication: "
        + ", ".join(f"{item.table_name}:{item.metric_name}" for item in failures)
    )
published = publish_visual_eda_build(build, catalog=catalog, schema=gold_schema)

# COMMAND ----------

for table_name in published:
    display(spark.table(table_name).limit(100))
display(
    spark.table(quality_name)
    .where(functions.col("quality_run_id") == build.build_id)
    .orderBy("table_name", "metric_name")
)
print(f"Published {len(published)} visual EDA summaries for build {build.build_id}.")

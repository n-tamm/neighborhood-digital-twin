# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Data-readiness and EDA checkpoint
# MAGIC
# MAGIC This notebook builds compact, reproducible summaries for national source coverage, current
# MAGIC ACS uncertainty, FHFA history depth, and one-, three-, and five-year target feasibility.
# MAGIC It is a readiness checkpoint rather than a modeling dataset or final narrative analysis.

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

from neighborhood_twin.exploration import prepare_readiness_build, publish_readiness_build
from neighborhood_twin.validate import hard_failures, write_quality_metrics

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("silver_schema", "neighborhood_twin_silver", "Silver schema")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("quality_schema", "neighborhood_twin_quality", "Quality schema")
dbutils.widgets.text("quality_table", "eda_readiness_quality_metrics", "EDA quality table")

catalog = dbutils.widgets.get("catalog").strip()
silver_schema = dbutils.widgets.get("silver_schema").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
quality_schema = dbutils.widgets.get("quality_schema").strip()
quality_table = dbutils.widgets.get("quality_table").strip()

# COMMAND ----------

build = prepare_readiness_build(
    spark,
    catalog=catalog,
    silver_schema=silver_schema,
    gold_schema=gold_schema,
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
        "EDA readiness checks failed before publication: "
        + ", ".join(f"{item.table_name}:{item.metric_name}" for item in failures)
    )
published = publish_readiness_build(build, catalog=catalog, schema=gold_schema)

# COMMAND ----------

display(spark.table(f"{catalog}.{gold_schema}.gold_eda_state_coverage").orderBy("state_fips"))
display(
    spark.table(f"{catalog}.{gold_schema}.gold_eda_acs_measure_quality").orderBy(
        "measure_order"
    )
)
display(
    spark.table(f"{catalog}.{gold_schema}.gold_eda_horizon_feasibility").orderBy(
        "state_fips", "horizon_years"
    )
)
display(
    spark.table(quality_name)
    .where(functions.col("quality_run_id") == build.build_id)
    .orderBy("table_name", "metric_name")
)
print(f"Published {len(published)} EDA readiness tables for build {build.build_id}.")

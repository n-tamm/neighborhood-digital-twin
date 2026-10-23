# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Build source-specific silver tables
# MAGIC
# MAGIC **Question:** Can the accepted bronze snapshots be converted into stable, typed,
# MAGIC human-readable source tables without hiding missing values or losing lineage?
# MAGIC
# MAGIC **Inputs:** The current FHFA and ACS bronze tables.
# MAGIC
# MAGIC **Outputs:** One FHFA tract-year table, a primary normalized ACS measure table,
# MAGIC its data dictionary, a generated wide ACS convenience table, and an append-only
# MAGIC silver quality table. This job does not harmonize tract vintages, construct modeling
# MAGIC targets, or impute unavailable values.

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

from neighborhood_twin.transform import prepare_silver_build, publish_silver_build
from neighborhood_twin.validate import hard_failures, write_quality_metrics

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("schema", "neighborhood_twin_dev", "Shared project schema")
dbutils.widgets.text(
    "fhfa_table", "silver_fhfa_tract_year", "Current FHFA silver table"
)
dbutils.widgets.text(
    "acs_table", "silver_acs_tract_year", "Current ACS silver table"
)
dbutils.widgets.text(
    "acs_measure_table",
    "silver_acs_tract_measure",
    "Normalized ACS tract-release-measure table",
)
dbutils.widgets.text(
    "acs_dictionary_table",
    "silver_acs_measure_dictionary",
    "ACS measure data dictionary",
)
dbutils.widgets.text(
    "quality_table", "silver_quality_metrics", "Append-only silver quality table"
)

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
fhfa_table = dbutils.widgets.get("fhfa_table").strip()
acs_table = dbutils.widgets.get("acs_table").strip()
acs_measure_table = dbutils.widgets.get("acs_measure_table").strip()
acs_dictionary_table = dbutils.widgets.get("acs_dictionary_table").strip()
quality_table = dbutils.widgets.get("quality_table").strip()

# COMMAND ----------

build = prepare_silver_build(
    spark,
    catalog=catalog,
    schema=schema,
    fhfa_table=fhfa_table,
    acs_table=acs_table,
    acs_measure_table=acs_measure_table,
    acs_dictionary_table=acs_dictionary_table,
)
quality_table_name = write_quality_metrics(
    spark,
    build.metrics,
    catalog=catalog,
    schema=schema,
    table=quality_table,
)

failure_metrics = hard_failures(build.metrics)
if failure_metrics:
    failure_names = ", ".join(
        f"{metric.table_name}:{metric.metric_name}:{metric.dimension}"
        for metric in failure_metrics
    )
    raise RuntimeError(f"Silver quality checks failed before publication: {failure_names}")

(
    fhfa_table_name,
    acs_table_name,
    acs_measure_table_name,
    acs_dictionary_table_name,
) = publish_silver_build(
    build,
    catalog=catalog,
    schema=schema,
    fhfa_table=fhfa_table,
    acs_table=acs_table,
    acs_measure_table=acs_measure_table,
    acs_dictionary_table=acs_dictionary_table,
)

# COMMAND ----------

latest_metrics = spark.table(f"{catalog}.{schema}.{quality_table}").where(
    functions.col("quality_run_id") == build.build_id
)
display(latest_metrics.orderBy("metric_group", "table_name", "metric_name", "dimension"))
print(
    f"Published {fhfa_table_name}, {acs_table_name}, {acs_measure_table_name}, and "
    f"{acs_dictionary_table_name}; "
    f"wrote {len(build.metrics)} checks to {quality_table_name} "
    f"for build {build.build_id}."
)

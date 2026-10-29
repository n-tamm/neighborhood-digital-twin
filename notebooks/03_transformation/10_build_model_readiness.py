# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Build model-readiness gold products
# MAGIC
# MAGIC This job converts the governed historical state and target tables into raw point-in-time
# MAGIC features, frozen temporal and geographic assignments, a joined modeling panel, and compact
# MAGIC readiness summaries. It deliberately leaves scaling, imputation, PCA, and feature selection
# MAGIC inside later training folds.

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

from neighborhood_twin.model_readiness import (
    parse_horizon_mapping,
    prepare_model_readiness_build,
    publish_model_readiness_build,
)
from neighborhood_twin.validate import hard_failures, write_quality_metrics

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("quality_schema", "neighborhood_twin_quality", "Quality schema")
dbutils.widgets.text("quality_table", "gold_quality_metrics", "Gold quality table")
dbutils.widgets.text("forecast_horizons", "1,3,5", "Forecast horizons in years")
dbutils.widgets.text(
    "locked_test_origins",
    "1:2024,3:2022,5:2020",
    "Locked temporal-test origin by horizon",
)
dbutils.widgets.text(
    "validation_origin_counts",
    "1:2,3:2,5:1",
    "Number of validation origins immediately before calibration",
)
dbutils.widgets.text(
    "geographic_holdout_seed",
    "699",
    "Seed for one deterministic holdout state per Census region",
)

catalog = dbutils.widgets.get("catalog").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
quality_schema = dbutils.widgets.get("quality_schema").strip()
quality_table = dbutils.widgets.get("quality_table").strip()
horizons = tuple(
    int(value.strip())
    for value in dbutils.widgets.get("forecast_horizons").split(",")
    if value.strip()
)
locked_test_origins = parse_horizon_mapping(
    dbutils.widgets.get("locked_test_origins"),
    label="locked_test_origins",
)
validation_origin_counts = parse_horizon_mapping(
    dbutils.widgets.get("validation_origin_counts"),
    label="validation_origin_counts",
)
geographic_holdout_seed = int(dbutils.widgets.get("geographic_holdout_seed").strip())

# COMMAND ----------

build = prepare_model_readiness_build(
    spark,
    catalog=catalog,
    gold_schema=gold_schema,
    horizons=horizons,
    locked_test_origins=locked_test_origins,
    validation_origin_counts=validation_origin_counts,
    geographic_holdout_seed=geographic_holdout_seed,
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
    raise RuntimeError(f"Model-readiness checks failed before publication: {names}")

published = publish_model_readiness_build(build, catalog=catalog, schema=gold_schema)

# COMMAND ----------

for table_name in published:
    print(f"Published {table_name}: {spark.table(table_name).count():,} rows")
display(
    spark.table(quality_table_name)
    .where(functions.col("quality_run_id") == build.build_id)
    .orderBy("table_name", "metric_group", "metric_name", "dimension")
)

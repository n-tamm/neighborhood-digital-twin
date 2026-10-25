# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Build the 2010-to-2020 tract relationship table
# MAGIC
# MAGIC **Question:** Which older tracts can be compared with 2020 tracts without hiding
# MAGIC boundary changes or treating land overlap as a population weight?
# MAGIC
# MAGIC **Inputs:** The registered official Census relationship snapshot.
# MAGIC
# MAGIC **Outputs:** A validated source-shaped bronze table, a typed silver relationship table,
# MAGIC and append-only geography quality metrics. This job does not transform ACS values or
# MAGIC claim that area shares are valid weights for medians, rates, or indexes.

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

from pyspark.sql import functions

from neighborhood_twin.data.databricks import (
    append_manifest,
    ingest_tract_relationship_bronze,
)
from neighborhood_twin.data.manifest import SourceManifest
from neighborhood_twin.geography import (
    prepare_geography_build,
    publish_geography_build,
)
from neighborhood_twin.validate import hard_failures, write_quality_metrics

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("bronze_schema", "neighborhood_twin_bronze", "Bronze schema")
dbutils.widgets.text("silver_schema", "neighborhood_twin_silver", "Silver schema")
dbutils.widgets.text("quality_schema", "neighborhood_twin_quality", "Quality schema")
dbutils.widgets.text(
    "relationship_table",
    "silver_tract_relationship_2010_2020",
    "Typed current relationship table",
)
dbutils.widgets.text(
    "quality_table",
    "geography_quality_metrics",
    "Append-only geography quality table",
)

catalog = dbutils.widgets.get("catalog").strip()
bronze_schema = dbutils.widgets.get("bronze_schema").strip()
silver_schema = dbutils.widgets.get("silver_schema").strip()
quality_schema = dbutils.widgets.get("quality_schema").strip()
relationship_table = dbutils.widgets.get("relationship_table").strip()
quality_table = dbutils.widgets.get("quality_table").strip()

# COMMAND ----------

manifest_table = f"{catalog}.{bronze_schema}.source_snapshot_manifest"
if not spark.catalog.tableExists(manifest_table):
    raise ValueError(f"Required manifest table does not exist: {manifest_table}")

manifest_row = (
    spark.table(manifest_table)
    .where(functions.col("source_id") == "census_tract_relationship_2010_2020")
    .orderBy(
        functions.to_timestamp("retrieval_timestamp_utc").desc(),
        functions.col("snapshot_id").desc(),
    )
    .select("file_path")
    .first()
)
if manifest_row is None:
    raise ValueError("No registered Census tract relationship snapshot was found")

source_path = Path(str(manifest_row["file_path"]))
sidecar_path = source_path.with_name(f"{source_path.name}.manifest.json")
manifest = SourceManifest.read_json(sidecar_path)
manifest = ingest_tract_relationship_bronze(
    spark,
    manifest,
    catalog=catalog,
    schema=bronze_schema,
)
append_manifest(spark, manifest, catalog=catalog, schema=bronze_schema)
print(f"Validated {manifest.snapshot_id}")

# COMMAND ----------

build = prepare_geography_build(
    spark,
    catalog=catalog,
    schema=silver_schema,
    bronze_schema=bronze_schema,
    relationship_table=relationship_table,
)
quality_table_name = write_quality_metrics(
    spark,
    build.metrics,
    catalog=catalog,
    schema=quality_schema,
    table=quality_table,
)
failure_metrics = hard_failures(build.metrics)
if failure_metrics:
    failure_names = ", ".join(
        f"{metric.metric_name}:{metric.dimension}" for metric in failure_metrics
    )
    raise RuntimeError(f"Geography quality checks failed before publication: {failure_names}")

relationship_table_name = publish_geography_build(
    build,
    catalog=catalog,
    schema=silver_schema,
    relationship_table=relationship_table,
)

# COMMAND ----------

latest_metrics = spark.table(f"{catalog}.{quality_schema}.{quality_table}").where(
    functions.col("quality_run_id") == build.build_id
)
display(latest_metrics.orderBy("metric_group", "metric_name", "dimension"))
print(
    f"Published {relationship_table_name}; wrote {len(build.metrics)} checks to "
    f"{quality_table_name} for build {build.build_id}."
)

# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Build simplified tract display geometry
# MAGIC
# MAGIC This job parses the registered 2020 Census 1:500,000 cartographic boundary archive.
# MAGIC Its output supports maps and identifier lookup only. It is deliberately not approved for
# MAGIC adjacency, distance, area, perimeter, or other precise spatial analysis.

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

from neighborhood_twin.data.databricks import (
    append_manifest,
    ingest_tract_display_geometry_bronze,
)
from neighborhood_twin.data.manifest import SourceManifest
from neighborhood_twin.geography import (
    prepare_display_geometry_build,
    publish_display_geometry_build,
)
from neighborhood_twin.validate import hard_failures, write_quality_metrics

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("schema", "neighborhood_twin_dev", "Project schema")
dbutils.widgets.text(
    "display_table",
    "silver_tract_display_geometry_2020",
    "Simplified application display geometry",
)
dbutils.widgets.text(
    "quality_table",
    "geography_quality_metrics",
    "Append-only geography quality table",
)

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
display_table = dbutils.widgets.get("display_table").strip()
quality_table = dbutils.widgets.get("quality_table").strip()

# COMMAND ----------

manifest_table = f"{catalog}.{schema}.source_snapshot_manifest"
manifest_row = (
    spark.table(manifest_table)
    .where(functions.col("source_id") == "census_tract_boundaries_2020")
    .orderBy(
        functions.to_timestamp("retrieval_timestamp_utc").desc(),
        functions.col("snapshot_id").desc(),
    )
    .select("file_path")
    .first()
)
if manifest_row is None:
    raise ValueError("No registered Census tract boundary snapshot was found")

source_path = Path(str(manifest_row["file_path"]))
manifest = SourceManifest.read_json(source_path.with_name(f"{source_path.name}.manifest.json"))
manifest = ingest_tract_display_geometry_bronze(
    spark,
    manifest,
    catalog=catalog,
    schema=schema,
)
append_manifest(spark, manifest, catalog=catalog, schema=schema)

# COMMAND ----------

build = prepare_display_geometry_build(
    spark,
    catalog=catalog,
    schema=schema,
    display_table=display_table,
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
    names = ", ".join(f"{metric.metric_name}:{metric.dimension}" for metric in failure_metrics)
    raise RuntimeError(f"Display geometry checks failed before publication: {names}")

display_table_name = publish_display_geometry_build(
    build,
    catalog=catalog,
    schema=schema,
    display_table=display_table,
)
display(
    spark.table(quality_table_name)
    .where(functions.col("quality_run_id") == build.build_id)
    .orderBy("metric_group", "metric_name")
)
print(f"Published {display_table_name} for build {build.build_id}.")

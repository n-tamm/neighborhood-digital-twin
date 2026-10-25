# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Organize project schemas
# MAGIC
# MAGIC This one-time, idempotent transition creates separate bronze, silver, gold, and quality
# MAGIC schemas. Existing tables are copied from the earlier shared development schema only when
# MAGIC the destination table does not already exist. The legacy schema is never changed or deleted.
# MAGIC Existing source-file paths remain valid lineage references; new acquisitions use the bronze
# MAGIC schema's managed volume.

# COMMAND ----------

import sys
from pathlib import Path


def _add_repository_source() -> None:
    candidates = [Path.cwd(), *Path.cwd().parents]
    for candidate in candidates:
        source_root = candidate / "src"
        if (source_root / "neighborhood_twin").exists():
            source_text = str(source_root)
            if source_text not in sys.path:
                sys.path.insert(0, source_text)
            return
    raise RuntimeError("Could not locate the repository src directory")


_add_repository_source()

# COMMAND ----------

from neighborhood_twin.data.databricks import ensure_data_objects, qualified_name
from neighborhood_twin.metadata import TABLE_LAYERS

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("legacy_schema", "neighborhood_twin_dev", "Previous shared schema")
dbutils.widgets.text("bronze_schema", "neighborhood_twin_bronze", "Bronze schema")
dbutils.widgets.text("silver_schema", "neighborhood_twin_silver", "Silver schema")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("quality_schema", "neighborhood_twin_quality", "Quality schema")
dbutils.widgets.text("volume", "source_snapshots", "Bronze source-snapshot volume")

catalog = dbutils.widgets.get("catalog").strip()
legacy_schema = dbutils.widgets.get("legacy_schema").strip()
bronze_schema = dbutils.widgets.get("bronze_schema").strip()
silver_schema = dbutils.widgets.get("silver_schema").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
quality_schema = dbutils.widgets.get("quality_schema").strip()
volume = dbutils.widgets.get("volume").strip()

layer_schemas = {
    "bronze": bronze_schema,
    "silver": silver_schema,
    "gold": gold_schema,
    "quality": quality_schema,
}

# COMMAND ----------

ensure_data_objects(spark, catalog=catalog, schema=bronze_schema, volume=volume)
for schema_name in (silver_schema, gold_schema, quality_schema):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema_name}`")

results = []
for table, layer in TABLE_LAYERS.items():
    source_name = f"{catalog}.{legacy_schema}.{table}"
    source_qualified_name = qualified_name(catalog, legacy_schema, table)
    target_schema = layer_schemas[layer]
    target_raw_name = f"{catalog}.{target_schema}.{table}"
    target_name = qualified_name(catalog, target_schema, table)

    if spark.catalog.tableExists(target_raw_name):
        results.append((table, layer, "already_present", spark.table(target_raw_name).count()))
        continue
    if not spark.catalog.tableExists(source_name):
        results.append((table, layer, "source_not_present", None))
        continue

    source_count = spark.table(source_name).count()
    spark.sql(f"CREATE TABLE {target_name} USING DELTA AS SELECT * FROM {source_qualified_name}")
    target_count = spark.table(target_raw_name).count()
    if target_count != source_count:
        raise RuntimeError(
            f"Row-count mismatch while copying {source_name} to {target_raw_name}: "
            f"source={source_count}, target={target_count}"
        )
    results.append((table, layer, "copied", target_count))

result_frame = spark.createDataFrame(
    results,
    "table_name string, layer string, migration_status string, row_count long",
)
display(result_frame.orderBy("layer", "table_name"))
print(
    f"Organized {sum(row[2] in ('copied', 'already_present') for row in results)} tables; "
    "the legacy schema was retained unchanged."
)

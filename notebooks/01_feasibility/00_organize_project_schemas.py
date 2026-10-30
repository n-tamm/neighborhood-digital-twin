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
# MAGIC This one-time, idempotent transition creates separate bronze, silver, gold, model,
# MAGIC evaluation, and quality schemas. Existing tables are copied from the earlier shared
# MAGIC development or gold schema only when the destination table does not already exist. Source
# MAGIC schemas are never changed or deleted.
# MAGIC Existing source-file paths remain valid lineage references; new acquisitions use the bronze
# MAGIC schema's managed volume.

# COMMAND ----------

import sys
from pathlib import Path


def _add_repository_source() -> None:
    """Make the deployed repository package importable by this notebook."""

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
dbutils.widgets.text("model_schema", "neighborhood_twin_model", "Model-output schema")
dbutils.widgets.text(
    "evaluation_schema", "neighborhood_twin_evaluation", "Model-evaluation schema"
)
dbutils.widgets.text("quality_schema", "neighborhood_twin_quality", "Quality schema")
dbutils.widgets.text("volume", "source_snapshots", "Bronze source-snapshot volume")
dbutils.widgets.text(
    "evaluation_figure_volume", "model_evaluation_figures", "Evaluation-figure volume"
)

catalog = dbutils.widgets.get("catalog").strip()
legacy_schema = dbutils.widgets.get("legacy_schema").strip()
bronze_schema = dbutils.widgets.get("bronze_schema").strip()
silver_schema = dbutils.widgets.get("silver_schema").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
model_schema = dbutils.widgets.get("model_schema").strip()
evaluation_schema = dbutils.widgets.get("evaluation_schema").strip()
quality_schema = dbutils.widgets.get("quality_schema").strip()
volume = dbutils.widgets.get("volume").strip()
evaluation_figure_volume = dbutils.widgets.get("evaluation_figure_volume").strip()

layer_schemas = {
    "bronze": bronze_schema,
    "silver": silver_schema,
    "gold": gold_schema,
    "model": model_schema,
    "evaluation": evaluation_schema,
    "quality": quality_schema,
}

schema_comments = {
    bronze_schema: "Raw, source-shaped project tables and immutable acquisition files.",
    silver_schema: "Cleaned, conformed, and geography-governed project tables.",
    gold_schema: "Curated analytical inputs and application-ready project data products.",
    model_schema: "Generated model predictions, ranked matches, and model artifact references.",
    evaluation_schema: "Model scorecards, diagnostics, figure manifests, and evaluation artifacts.",
    quality_schema: "Pipeline validation, reconciliation, and observability results.",
}

renamed_sources = {
    "forecast_baseline_prediction": (gold_schema, "gold_forecast_baseline_prediction"),
    "forecast_baseline_scorecard": (gold_schema, "gold_forecast_baseline_scorecard"),
    "similarity_baseline_match": (gold_schema, "gold_similarity_baseline_match"),
    "similarity_baseline_summary": (gold_schema, "gold_similarity_baseline_summary"),
}

# COMMAND ----------

ensure_data_objects(spark, catalog=catalog, schema=bronze_schema, volume=volume)
for schema_name in (
    silver_schema,
    gold_schema,
    model_schema,
    evaluation_schema,
    quality_schema,
):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema_name}`")
    comment = schema_comments[schema_name].replace("'", "''")
    spark.sql(f"COMMENT ON SCHEMA `{catalog}`.`{schema_name}` IS '{comment}'")
spark.sql(
    f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{evaluation_schema}`."
    f"`{evaluation_figure_volume}`"
)

results = []
for table, layer in TABLE_LAYERS.items():
    source_schema, source_table = renamed_sources.get(table, (legacy_schema, table))
    source_name = f"{catalog}.{source_schema}.{source_table}"
    source_qualified_name = qualified_name(catalog, source_schema, source_table)
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

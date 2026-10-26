# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Apply managed-table metadata
# MAGIC
# MAGIC Adds a purpose and declared grain to each implemented table, then comments every existing
# MAGIC column. It is safe to rerun after a table is rebuilt with an overwritten schema and skips
# MAGIC column updates whose managed comment already matches.

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

from neighborhood_twin.metadata import apply_table_metadata

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("bronze_schema", "neighborhood_twin_bronze", "Bronze schema")
dbutils.widgets.text("silver_schema", "neighborhood_twin_silver", "Silver schema")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("quality_schema", "neighborhood_twin_quality", "Quality schema")

updated = apply_table_metadata(
    spark,
    catalog=dbutils.widgets.get("catalog").strip(),
    bronze_schema=dbutils.widgets.get("bronze_schema").strip(),
    silver_schema=dbutils.widgets.get("silver_schema").strip(),
    gold_schema=dbutils.widgets.get("gold_schema").strip(),
    quality_schema=dbutils.widgets.get("quality_schema").strip(),
)
print(f"Applied table and column metadata to {len(updated)} tables.")
for table in updated:
    print(table)

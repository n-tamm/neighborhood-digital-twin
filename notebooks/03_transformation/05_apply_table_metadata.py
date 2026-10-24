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
# MAGIC column. It is safe to rerun after a table is rebuilt with an overwritten schema.

# COMMAND ----------

import sys
from pathlib import Path


def _add_repository_source() -> None:
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
dbutils.widgets.text("schema", "neighborhood_twin_dev", "Project schema")

updated = apply_table_metadata(
    spark,
    catalog=dbutils.widgets.get("catalog").strip(),
    schema=dbutils.widgets.get("schema").strip(),
)
print(f"Applied table and column metadata to {len(updated)} tables.")
for table in updated:
    print(table)

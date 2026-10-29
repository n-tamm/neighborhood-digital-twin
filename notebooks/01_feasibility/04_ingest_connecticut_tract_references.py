# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Ingest Connecticut tract reference vintages
# MAGIC
# MAGIC This isolated acquisition job registers the official 2020 and 2024 Connecticut
# MAGIC TIGER/Line tract archives. It retains both complete tract universes so the next task can
# MAGIC build and audit an explicit bridge without rewriting the national bronze pipeline.

# COMMAND ----------

import sys
from pathlib import Path


def _add_repository_source() -> None:
    """Make the deployed repository package importable by this notebook."""

    candidates = (Path.cwd(), *Path.cwd().parents)
    for candidate in candidates:
        source_root = candidate / "src"
        if (source_root / "neighborhood_twin").is_dir():
            sys.path.insert(0, str(source_root))
            return
    raise RuntimeError("Could not find src/neighborhood_twin in the deployed bundle")


_add_repository_source()

# COMMAND ----------

from neighborhood_twin.data import (
    acquire_http_snapshot,
    register_existing_snapshot,
    request_for_static_source,
)
from neighborhood_twin.data.databricks import (
    append_manifest,
    ensure_data_objects,
    ingest_connecticut_tract_reference_bronze,
    volume_root,
)

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("bronze_schema", "neighborhood_twin_bronze", "Bronze schema")
dbutils.widgets.text("volume", "source_snapshots", "Managed raw-data volume")
dbutils.widgets.text(
    "uploaded_source_directory",
    "",
    "Optional volume directory containing manually uploaded source files",
)

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("bronze_schema").strip()
volume = dbutils.widgets.get("volume").strip()
uploaded_source_directory = dbutils.widgets.get("uploaded_source_directory").strip()

ensure_data_objects(spark, catalog=catalog, schema=schema, volume=volume)
raw_root = volume_root(catalog, schema, volume)


def _acquire_or_register(request):
    """Acquire one tract reference or register its approved uploaded copy."""

    if uploaded_source_directory:
        uploaded_path = Path(uploaded_source_directory) / request.file_name
        if uploaded_path.is_file():
            return register_existing_snapshot(request, uploaded_path, raw_root)
    return acquire_http_snapshot(request, raw_root)


# COMMAND ----------

sources = (
    ("census_connecticut_tracts_2020", 2020),
    ("census_connecticut_tracts_2024", 2024),
)
for source_id, vintage in sources:
    request = request_for_static_source(source_id)
    try:
        manifest = _acquire_or_register(request)
    except Exception as error:
        raise RuntimeError(
            f"Could not acquire {source_id}. If workspace HTTP access is blocked, download the "
            "archive locally, upload it to one volume directory, set "
            "uploaded_source_directory, and rerun."
        ) from error
    manifest = ingest_connecticut_tract_reference_bronze(
        spark,
        manifest,
        geography_vintage=vintage,
        catalog=catalog,
        schema=schema,
    )
    append_manifest(spark, manifest, catalog=catalog, schema=schema)
    print(f"Accepted {manifest.snapshot_id}")

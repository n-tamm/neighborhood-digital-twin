# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Core source ingestion pilot
# MAGIC
# MAGIC This notebook creates the first governed project data in Databricks. It saves immutable
# MAGIC source payloads and JSON manifests in a Unity Catalog managed volume, then publishes
# MAGIC validated FHFA and ACS bronze Delta tables. The default states are a feasibility sample,
# MAGIC not a decision to limit the final modeling pool.

# COMMAND ----------

import sys
from pathlib import Path


def _add_repository_source() -> None:
    """Make the repository package importable from a Databricks Git folder."""

    candidates = (Path.cwd(), *Path.cwd().parents)
    for candidate in candidates:
        source_root = candidate / "src"
        if (source_root / "neighborhood_twin").is_dir():
            sys.path.insert(0, str(source_root))
            return
    raise RuntimeError(
        "Could not find src/neighborhood_twin. Run this notebook from the cloned Git folder."
    )


_add_repository_source()

# COMMAND ----------

from neighborhood_twin.data import (
    acquire_http_snapshot,
    register_existing_snapshot,
    request_for_static_source,
)
from neighborhood_twin.data.acs import build_acs_tract_request
from neighborhood_twin.data.databricks import (
    append_manifest,
    ensure_data_objects,
    ingest_acs_bronze,
    ingest_fhfa_bronze,
    qualified_name,
    volume_root,
)

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("bronze_schema", "neighborhood_twin_bronze", "Bronze schema")
dbutils.widgets.text("volume", "source_snapshots", "Managed raw-data volume")
dbutils.widgets.text("acs_release_year", "2024", "ACS five-year release")
dbutils.widgets.text("pilot_state_fips", "04,26,42", "Pilot state FIPS codes")
dbutils.widgets.text("secret_scope", "neighborhood-twin", "Databricks secret scope")
dbutils.widgets.text("census_secret_key", "census-api-key", "Census key secret name")
dbutils.widgets.text(
    "uploaded_source_directory",
    "",
    "Optional volume directory containing manually uploaded source files",
)

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("bronze_schema").strip()
volume = dbutils.widgets.get("volume").strip()
acs_release_year = int(dbutils.widgets.get("acs_release_year"))
pilot_state_fips = tuple(
    value.strip() for value in dbutils.widgets.get("pilot_state_fips").split(",") if value.strip()
)
secret_scope = dbutils.widgets.get("secret_scope").strip()
census_secret_key = dbutils.widgets.get("census_secret_key").strip()
uploaded_source_directory = dbutils.widgets.get("uploaded_source_directory").strip()

if not pilot_state_fips:
    raise ValueError("At least one pilot state FIPS code is required")

# COMMAND ----------

ensure_data_objects(spark, catalog=catalog, schema=schema, volume=volume)
raw_root = volume_root(catalog, schema, volume)
print(f"Raw snapshots will be stored under {raw_root}")


def _acquire_or_register(request):
    """Acquire one source directly or register its approved uploaded copy."""

    if uploaded_source_directory:
        uploaded_path = Path(uploaded_source_directory) / request.file_name
        if uploaded_path.is_file():
            return register_existing_snapshot(request, uploaded_path, raw_root)
    return acquire_http_snapshot(request, raw_root)


# COMMAND ----------

static_source_ids = (
    "fhfa_tract_hpi",
    "census_tract_boundaries_2020",
    "census_tract_relationship_2010_2020",
)

for source_id in static_source_ids:
    request = request_for_static_source(source_id)
    try:
        manifest = _acquire_or_register(request)
    except Exception as error:
        raise RuntimeError(
            f"Could not acquire {source_id}. Databricks Free Edition can restrict outbound "
            "domains. If the source is blocked, download it locally, upload it to one volume "
            "directory, and set the uploaded_source_directory widget before rerunning."
        ) from error

    if source_id == "fhfa_tract_hpi":
        manifest = ingest_fhfa_bronze(spark, manifest, catalog=catalog, schema=schema)
    append_manifest(spark, manifest, catalog=catalog, schema=schema)
    print(f"Accepted {manifest.snapshot_id}")

# COMMAND ----------

try:
    census_api_key = dbutils.secrets.get(scope=secret_scope, key=census_secret_key)
except Exception as error:
    raise RuntimeError(
        "The ACS API now requires a key. Add it to the configured Databricks secret scope, "
        "then rerun this notebook; do not paste the key into a widget or commit it to Git."
    ) from error

for state_fips in pilot_state_fips:
    request = build_acs_tract_request(
        release_year=acs_release_year,
        state_fips=state_fips,
        api_key=census_api_key,
    )
    try:
        manifest = _acquire_or_register(request)
    except Exception as error:
        raise RuntimeError(
            f"Could not acquire the {acs_release_year} ACS tract response for state "
            f"{state_fips}. Check the Census key and Databricks outbound-network access."
        ) from error
    manifest = ingest_acs_bronze(
        spark,
        manifest,
        release_year=acs_release_year,
        catalog=catalog,
        schema=schema,
    )
    append_manifest(spark, manifest, catalog=catalog, schema=schema)
    print(f"Accepted {manifest.snapshot_id}")

# COMMAND ----------

manifest_table = qualified_name(catalog, schema, "source_snapshot_manifest")
display(spark.table(manifest_table).orderBy("retrieval_timestamp_utc", ascending=False))

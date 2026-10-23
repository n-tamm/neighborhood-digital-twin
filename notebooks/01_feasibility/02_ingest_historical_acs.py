# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Historical ACS ingestion
# MAGIC
# MAGIC This isolated job expands the accepted ACS bronze history without reacquiring FHFA or
# MAGIC static geography files. One run is deliberately bounded to a reviewed set of release
# MAGIC years and states. The default six requests test older ACS releases and 2010-vintage
# MAGIC tracts before the project attempts annual national history.

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

from neighborhood_twin.data import acquire_http_snapshot
from neighborhood_twin.data.acs import (
    build_acs_tract_request,
    parse_acs_ingestion_scope,
)
from neighborhood_twin.data.databricks import (
    append_manifest,
    ensure_data_objects,
    ingest_acs_bronze,
    qualified_name,
    volume_root,
)

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("schema", "neighborhood_twin_dev", "Project schema")
dbutils.widgets.text("volume", "source_snapshots", "Managed raw-data volume")
dbutils.widgets.text("acs_release_years", "2014,2019", "Comma-separated ACS releases")
dbutils.widgets.text("state_fips_codes", "04,26,42", "Comma-separated state FIPS codes")
dbutils.widgets.text("maximum_requests", "25", "Safety limit for API calls in one run")
dbutils.widgets.text("secret_scope", "neighborhood-twin", "Databricks secret scope")
dbutils.widgets.text("census_secret_key", "census-api-key", "Census key secret name")

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
volume = dbutils.widgets.get("volume").strip()
secret_scope = dbutils.widgets.get("secret_scope").strip()
census_secret_key = dbutils.widgets.get("census_secret_key").strip()
scope = parse_acs_ingestion_scope(
    release_years=dbutils.widgets.get("acs_release_years"),
    state_fips_codes=dbutils.widgets.get("state_fips_codes"),
    maximum_requests=int(dbutils.widgets.get("maximum_requests")),
)
print(
    f"Historical ACS scope: releases={scope.release_years}, "
    f"states={scope.state_fips_codes}, requests={scope.request_count}"
)

# COMMAND ----------

ensure_data_objects(spark, catalog=catalog, schema=schema, volume=volume)
raw_root = volume_root(catalog, schema, volume)
try:
    census_api_key = dbutils.secrets.get(scope=secret_scope, key=census_secret_key)
except Exception as error:
    raise RuntimeError(
        "Add the Census API key to the configured Databricks secret scope; do not paste "
        "the key into a widget or commit it to Git."
    ) from error

# COMMAND ----------

accepted_snapshots = []
for release_year in scope.release_years:
    for state_fips in scope.state_fips_codes:
        request = build_acs_tract_request(
            release_year=release_year,
            state_fips=state_fips,
            api_key=census_api_key,
        )
        try:
            manifest = acquire_http_snapshot(request, raw_root)
        except Exception as error:
            raise RuntimeError(
                f"Could not acquire the {release_year} ACS tract response for state "
                f"{state_fips}. No later requests in this batch were attempted."
            ) from error
        manifest = ingest_acs_bronze(
            spark,
            manifest,
            release_year=release_year,
            catalog=catalog,
            schema=schema,
        )
        append_manifest(spark, manifest, catalog=catalog, schema=schema)
        accepted_snapshots.append(manifest.snapshot_id)
        print(f"Accepted {manifest.snapshot_id}")

# COMMAND ----------

bronze_name = qualified_name(catalog, schema, "bronze_acs5_tract")
manifest_name = qualified_name(catalog, schema, "source_snapshot_manifest")
display(
    spark.table(bronze_name)
    .where(functions.col("acs_release_year").isin(scope.release_years))
    .groupBy("acs_release_year", "state")
    .agg(
        functions.count(functions.lit(1)).alias("tract_count"),
        functions.countDistinct("source_snapshot_id").alias("snapshot_count"),
    )
    .orderBy("acs_release_year", "state")
)
display(
    spark.table(manifest_name)
    .where(functions.col("snapshot_id").isin(accepted_snapshots))
    .select(
        "snapshot_id",
        "reference_period",
        "row_count",
        "validation_status",
        "retrieval_timestamp_utc",
    )
    .orderBy("reference_period", "snapshot_id")
)

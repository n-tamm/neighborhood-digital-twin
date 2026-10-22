"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Small Spark helpers for governed raw files and Delta bronze tables in Databricks.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

from neighborhood_twin.data.acs import parse_acs_api_payload
from neighborhood_twin.data.manifest import SourceManifest


def _quoted_identifier(value: str) -> str:
    if not value or "`" in value:
        raise ValueError("Databricks identifiers must be non-empty and cannot contain backticks")
    return f"`{value}`"


def qualified_name(catalog: str, schema: str, object_name: str) -> str:
    """Build a safely quoted three-level Unity Catalog object name."""

    return ".".join(_quoted_identifier(value) for value in (catalog, schema, object_name))


def volume_root(catalog: str, schema: str, volume: str) -> Path:
    """Return the POSIX-style path for a Unity Catalog volume."""

    for value in (catalog, schema, volume):
        if not value or "/" in value or ".." in value:
            raise ValueError("Volume path components cannot be blank or contain path separators")
    return Path("/Volumes") / catalog / schema / volume


def ensure_data_objects(spark: Any, *, catalog: str, schema: str, volume: str) -> None:
    """Create the project schema and managed volume inside an existing catalog."""

    spark.sql(
        f"CREATE SCHEMA IF NOT EXISTS {_quoted_identifier(catalog)}.{_quoted_identifier(schema)}"
    )
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {qualified_name(catalog, schema, volume)}")


def _snapshot_exists(spark: Any, table_name: str, snapshot_id: str) -> bool:
    if not spark.catalog.tableExists(table_name):
        return False
    from pyspark.sql import functions as functions  # type: ignore[import-not-found]

    return (
        spark.table(table_name)
        .where(functions.col("source_snapshot_id") == snapshot_id)
        .limit(1)
        .count()
        > 0
    )


def append_manifest(spark: Any, manifest: SourceManifest, *, catalog: str, schema: str) -> None:
    """Append a source manifest once to the governed manifest Delta table."""

    table_name = qualified_name(catalog, schema, "source_snapshot_manifest")
    raw_table_name = f"{catalog}.{schema}.source_snapshot_manifest"
    if spark.catalog.tableExists(raw_table_name):
        from pyspark.sql import functions as functions  # type: ignore[import-not-found]

        exists = (
            spark.table(raw_table_name)
            .where(functions.col("snapshot_id") == manifest.snapshot_id)
            .limit(1)
            .count()
            > 0
        )
        if exists:
            return
    from pyspark.sql.types import (  # type: ignore[import-not-found]
        LongType,
        StringType,
        StructField,
        StructType,
    )

    manifest_schema = StructType(
        [
            StructField("snapshot_id", StringType(), False),
            StructField("source_id", StringType(), False),
            StructField("source_name", StringType(), False),
            StructField("publisher", StringType(), False),
            StructField("landing_page", StringType(), False),
            StructField("endpoint", StringType(), False),
            StructField("reference_period", StringType(), True),
            StructField("publication_date", StringType(), True),
            StructField("retrieval_timestamp_utc", StringType(), False),
            StructField("geographic_grain", StringType(), False),
            StructField("geography_vintage", StringType(), True),
            StructField("file_format", StringType(), False),
            StructField("file_path", StringType(), False),
            StructField("byte_size", LongType(), False),
            StructField("sha256", StringType(), False),
            StructField("http_status", LongType(), False),
            StructField("content_type", StringType(), True),
            StructField("etag", StringType(), True),
            StructField("last_modified", StringType(), True),
            StructField("terms_url", StringType(), False),
            StructField("code_version", StringType(), False),
            StructField("row_count", LongType(), True),
            StructField("schema_fingerprint", StringType(), True),
            StructField("validation_status", StringType(), False),
            StructField("request_parameters_json", StringType(), False),
            StructField("known_limitations_json", StringType(), False),
            StructField("validation_messages_json", StringType(), False),
        ]
    )
    spark.createDataFrame([manifest.to_spark_record()], schema=manifest_schema).write.format(
        "delta"
    ).mode("append").saveAsTable(table_name)


def ingest_fhfa_bronze(
    spark: Any,
    manifest: SourceManifest,
    *,
    catalog: str,
    schema: str,
) -> SourceManifest:
    """Validate the current FHFA CSV shape and append one immutable bronze partition."""

    from pyspark.sql import functions as functions  # type: ignore[import-not-found]

    table_name = qualified_name(catalog, schema, "bronze_fhfa_tract_hpi")
    raw_table_name = f"{catalog}.{schema}.bronze_fhfa_tract_hpi"
    if _snapshot_exists(spark, raw_table_name, manifest.snapshot_id):
        return manifest

    schema_definition = (
        "tract STRING, state_abbr STRING, year INT, annual_change DOUBLE, "
        "hpi DOUBLE, hpi1990 DOUBLE, hpi2000 DOUBLE"
    )
    frame = (
        spark.read.option("header", True)
        .option("mode", "FAILFAST")
        .schema(schema_definition)
        .csv(manifest.file_path)
    )
    row_count = frame.count()
    invalid_geoids = frame.where(
        functions.col("tract").isNull() | (~functions.col("tract").rlike("^[0-9]{11}$"))
    ).count()
    duplicate_keys = (
        frame.groupBy("tract", "year").count().where(functions.col("count") > 1).count()
    )
    if row_count == 0 or invalid_geoids or duplicate_keys:
        raise ValueError(
            "FHFA bronze validation failed: "
            f"rows={row_count}, invalid_geoids={invalid_geoids}, duplicate_keys={duplicate_keys}"
        )

    schema_fingerprint = hashlib.sha256(frame.schema.json().encode("utf-8")).hexdigest()
    profiled_manifest = manifest.with_profile(
        row_count=row_count,
        schema_fingerprint=schema_fingerprint,
        validation_status="bronze_validated",
    )
    profiled_manifest.write_sidecar()
    (
        frame.withColumn("source_snapshot_id", functions.lit(manifest.snapshot_id))
        .withColumn(
            "source_retrieval_timestamp_utc",
            functions.lit(manifest.retrieval_timestamp_utc),
        )
        .withColumn("source_file_path", functions.lit(manifest.file_path))
        .write.format("delta")
        .mode("append")
        .saveAsTable(table_name)
    )
    return profiled_manifest


def ingest_acs_bronze(
    spark: Any,
    manifest: SourceManifest,
    *,
    release_year: int,
    catalog: str,
    schema: str,
) -> SourceManifest:
    """Parse one state response and append it to the ACS bronze Delta table."""

    from pyspark.sql import functions as functions  # type: ignore[import-not-found]

    table_name = qualified_name(catalog, schema, "bronze_acs5_tract")
    raw_table_name = f"{catalog}.{schema}.bronze_acs5_tract"
    if _snapshot_exists(spark, raw_table_name, manifest.snapshot_id):
        return manifest

    records = parse_acs_api_payload(
        Path(manifest.file_path).read_bytes(), release_year=release_year
    )
    frame = spark.createDataFrame(records)
    invalid_geoids = frame.where(~functions.col("geoid").rlike("^[0-9]{11}$")).count()
    duplicate_keys = (
        frame.groupBy("geoid", "acs_release_year").count().where(functions.col("count") > 1).count()
    )
    if not records or invalid_geoids or duplicate_keys:
        raise ValueError(
            "ACS bronze validation failed: "
            f"rows={len(records)}, invalid_geoids={invalid_geoids}, "
            f"duplicate_keys={duplicate_keys}"
        )

    schema_fingerprint = hashlib.sha256(
        json.dumps(sorted(frame.columns)).encode("utf-8")
    ).hexdigest()
    profiled_manifest = manifest.with_profile(
        row_count=len(records),
        schema_fingerprint=schema_fingerprint,
        validation_status="bronze_validated",
    )
    profiled_manifest.write_sidecar()
    (
        frame.withColumn("source_snapshot_id", functions.lit(manifest.snapshot_id))
        .withColumn(
            "source_retrieval_timestamp_utc",
            functions.lit(manifest.retrieval_timestamp_utc),
        )
        .withColumn("source_file_path", functions.lit(manifest.file_path))
        .write.format("delta")
        .mode("append")
        .saveAsTable(table_name)
    )
    return profiled_manifest

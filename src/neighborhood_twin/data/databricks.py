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
from neighborhood_twin.data.boundary import read_boundary_archive
from neighborhood_twin.data.manifest import SourceManifest
from neighborhood_twin.data.tiger import read_tiger_tract_archive

MANIFEST_STATUS_RANK = {"acquired": 1, "registered": 1, "bronze_validated": 2}

TRACT_RELATIONSHIP_COLUMNS = (
    "OID_TRACT_20",
    "GEOID_TRACT_20",
    "NAMELSAD_TRACT_20",
    "AREALAND_TRACT_20",
    "AREAWATER_TRACT_20",
    "MTFCC_TRACT_20",
    "FUNCSTAT_TRACT_20",
    "OID_TRACT_10",
    "GEOID_TRACT_10",
    "NAMELSAD_TRACT_10",
    "AREALAND_TRACT_10",
    "AREAWATER_TRACT_10",
    "MTFCC_TRACT_10",
    "FUNCSTAT_TRACT_10",
    "AREALAND_PART",
    "AREAWATER_PART",
)


def _quoted_identifier(value: str) -> str:
    """Validate and quote one Databricks SQL identifier."""

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
    """Return whether a Delta table already contains the source snapshot."""

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
    """Insert a manifest once or upgrade its validation fields in place."""

    table_name = qualified_name(catalog, schema, "source_snapshot_manifest")
    raw_table_name = f"{catalog}.{schema}.source_snapshot_manifest"
    existing_status: str | None = None
    if spark.catalog.tableExists(raw_table_name):
        from pyspark.sql import functions as functions  # type: ignore[import-not-found]

        existing = (
            spark.table(raw_table_name)
            .where(functions.col("snapshot_id") == manifest.snapshot_id)
            .select("validation_status")
            .limit(1)
            .first()
        )
        if existing is not None:
            existing_status = str(existing["validation_status"])
        if existing_status is not None and MANIFEST_STATUS_RANK.get(
            existing_status, 0
        ) >= MANIFEST_STATUS_RANK.get(manifest.validation_status, 0):
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
    manifest_frame = spark.createDataFrame([manifest.to_spark_record()], schema=manifest_schema)
    if existing_status is None:
        manifest_frame.write.format("delta").mode("append").saveAsTable(table_name)
        return

    from delta.tables import DeltaTable  # type: ignore[import-not-found]

    (
        DeltaTable.forName(spark, raw_table_name)
        .alias("target")
        .merge(manifest_frame.alias("source"), "target.snapshot_id = source.snapshot_id")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )


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


def ingest_tract_relationship_bronze(
    spark: Any,
    manifest: SourceManifest,
    *,
    catalog: str,
    schema: str,
) -> SourceManifest:
    """Validate and append the national 2010-to-2020 tract relationship snapshot."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    table_name = qualified_name(catalog, schema, "bronze_census_tract_relationship_2010_2020")
    raw_table_name = f"{catalog}.{schema}.bronze_census_tract_relationship_2010_2020"
    if _snapshot_exists(spark, raw_table_name, manifest.snapshot_id):
        return manifest

    raw = (
        spark.read.option("header", True)
        .option("delimiter", "|")
        .option("mode", "FAILFAST")
        .csv(manifest.file_path)
    )
    if tuple(raw.columns) != TRACT_RELATIONSHIP_COLUMNS:
        raise ValueError(
            "Census tract relationship schema changed: "
            f"expected={TRACT_RELATIONSHIP_COLUMNS}, actual={tuple(raw.columns)}"
        )

    numeric_columns = {
        "AREALAND_TRACT_20",
        "AREAWATER_TRACT_20",
        "AREALAND_TRACT_10",
        "AREAWATER_TRACT_10",
        "AREALAND_PART",
        "AREAWATER_PART",
    }
    frame = raw.select(
        *[
            functions.col(column).cast("long").alias(column)
            if column in numeric_columns
            else functions.col(column)
            for column in TRACT_RELATIONSHIP_COLUMNS
        ]
    )
    row_count = frame.count()
    invalid_geoids = frame.where(
        (~functions.col("GEOID_TRACT_10").rlike("^[0-9]{11}$"))
        | (~functions.col("GEOID_TRACT_20").rlike("^[0-9]{11}$"))
    ).count()
    duplicate_pairs = (
        frame.groupBy("GEOID_TRACT_10", "GEOID_TRACT_20")
        .count()
        .where(functions.col("count") > 1)
        .count()
    )
    invalid_areas = frame.where(
        functions.col("AREALAND_PART").isNull()
        | functions.col("AREAWATER_PART").isNull()
        | (functions.col("AREALAND_PART") < 0)
        | (functions.col("AREAWATER_PART") < 0)
        | (functions.col("AREALAND_PART") > functions.col("AREALAND_TRACT_10"))
        | (functions.col("AREALAND_PART") > functions.col("AREALAND_TRACT_20"))
        | (functions.col("AREAWATER_PART") > functions.col("AREAWATER_TRACT_10"))
        | (functions.col("AREAWATER_PART") > functions.col("AREAWATER_TRACT_20"))
    ).count()
    if row_count == 0 or invalid_geoids or duplicate_pairs or invalid_areas:
        raise ValueError(
            "Census tract relationship bronze validation failed: "
            f"rows={row_count}, invalid_geoids={invalid_geoids}, "
            f"duplicate_pairs={duplicate_pairs}, invalid_areas={invalid_areas}"
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


def ingest_tract_display_geometry_bronze(
    spark: Any,
    manifest: SourceManifest,
    *,
    catalog: str,
    schema: str,
) -> SourceManifest:
    """Parse and validate the 2020 cartographic tract archive for display use."""

    from pyspark.sql import functions  # type: ignore[import-not-found]
    from pyspark.sql.types import (  # type: ignore[import-not-found]
        BinaryType,
        BooleanType,
        DoubleType,
        LongType,
        StringType,
        StructField,
        StructType,
    )

    table_name = qualified_name(catalog, schema, "bronze_census_tract_display_geometry_2020")
    raw_table_name = f"{catalog}.{schema}.bronze_census_tract_display_geometry_2020"
    if _snapshot_exists(spark, raw_table_name, manifest.snapshot_id):
        return manifest

    archive = read_boundary_archive(Path(manifest.file_path))
    frame_schema = StructType(
        [
            *[
                StructField(column, StringType(), False)
                for column in (
                    "STATEFP",
                    "COUNTYFP",
                    "TRACTCE",
                    "AFFGEOID",
                    "GEOID",
                    "NAME",
                    "NAMELSAD",
                    "STUSPS",
                    "NAMELSADCO",
                    "STATE_NAME",
                    "LSAD",
                )
            ],
            StructField("ALAND", LongType(), False),
            StructField("AWATER", LongType(), False),
            StructField("GEOMETRY_WKB", BinaryType(), False),
            StructField("GEOMETRY_TYPE", StringType(), False),
            StructField("GEOMETRY_IS_VALID", BooleanType(), False),
            StructField("GEOMETRY_IS_EMPTY", BooleanType(), False),
            StructField("MINIMUM_LONGITUDE", DoubleType(), False),
            StructField("MINIMUM_LATITUDE", DoubleType(), False),
            StructField("MAXIMUM_LONGITUDE", DoubleType(), False),
            StructField("MAXIMUM_LATITUDE", DoubleType(), False),
        ]
    )
    frame = spark.createDataFrame(archive.rows, schema=frame_schema)
    row_count = frame.count()
    invalid_rows = frame.where(
        (~functions.col("GEOID").rlike("^[0-9]{11}$"))
        | (functions.col("GEOID") != functions.concat("STATEFP", "COUNTYFP", "TRACTCE"))
        | (functions.col("ALAND") < 0)
        | (functions.col("AWATER") < 0)
        | (~functions.col("GEOMETRY_TYPE").isin("Polygon", "MultiPolygon"))
        | (~functions.col("GEOMETRY_IS_VALID"))
        | functions.col("GEOMETRY_IS_EMPTY")
        | (functions.col("MINIMUM_LONGITUDE") < -180)
        | (functions.col("MAXIMUM_LONGITUDE") > 180)
        | (functions.col("MINIMUM_LATITUDE") < -90)
        | (functions.col("MAXIMUM_LATITUDE") > 90)
    ).count()
    duplicate_geoids = frame.groupBy("GEOID").count().where(functions.col("count") > 1).count()
    if row_count == 0 or invalid_rows or duplicate_geoids:
        raise ValueError(
            "Census display geometry bronze validation failed: "
            f"rows={row_count}, invalid_rows={invalid_rows}, "
            f"duplicate_geoids={duplicate_geoids}"
        )

    schema_fingerprint = hashlib.sha256(frame.schema.json().encode("utf-8")).hexdigest()
    profiled_manifest = manifest.with_profile(
        row_count=row_count,
        schema_fingerprint=schema_fingerprint,
        validation_status="bronze_validated",
        validation_messages=(
            "Cartographic geometry is for display and identifier lookup only, not adjacency.",
        ),
    )
    profiled_manifest.write_sidecar()
    (
        frame.withColumn("SOURCE_CRS_WKT", functions.lit(archive.crs_wkt))
        .withColumn("source_snapshot_id", functions.lit(manifest.snapshot_id))
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


def ingest_connecticut_tract_reference_bronze(
    spark: Any,
    manifest: SourceManifest,
    *,
    geography_vintage: int,
    catalog: str,
    schema: str,
) -> SourceManifest:
    """Validate and append Connecticut tract identifiers from one TIGER archive."""

    from pyspark.sql import functions  # type: ignore[import-not-found]
    from pyspark.sql.types import (  # type: ignore[import-not-found]
        DoubleType,
        IntegerType,
        LongType,
        StringType,
        StructField,
        StructType,
    )

    if geography_vintage not in {2020, 2024}:
        raise ValueError("Connecticut tract reference vintage must be 2020 or 2024")
    table_name = qualified_name(catalog, schema, "bronze_census_connecticut_tract_reference")
    raw_table_name = f"{catalog}.{schema}.bronze_census_connecticut_tract_reference"
    if _snapshot_exists(spark, raw_table_name, manifest.snapshot_id):
        return manifest

    archive = read_tiger_tract_archive(Path(manifest.file_path))
    records = [
        {
            "geography_vintage": geography_vintage,
            "state_fips": str(row["STATEFP"]),
            "county_fips": str(row["COUNTYFP"]),
            "tract_code": str(row["TRACTCE"]),
            "geoid": str(row["GEOID"]),
            "tract_name": str(row["NAME"]),
            "tract_label": str(row["NAMELSAD"]),
            "feature_class_code": str(row["MTFCC"]),
            "functional_status": str(row["FUNCSTAT"]),
            "land_area_sqm": int(row["ALAND"]),
            "water_area_sqm": int(row["AWATER"]),
            "internal_point_latitude": float(row["INTPTLAT"]),
            "internal_point_longitude": float(row["INTPTLON"]),
        }
        for row in archive.rows
    ]
    frame_schema = StructType(
        [
            StructField("geography_vintage", IntegerType(), False),
            StructField("state_fips", StringType(), False),
            StructField("county_fips", StringType(), False),
            StructField("tract_code", StringType(), False),
            StructField("geoid", StringType(), False),
            StructField("tract_name", StringType(), False),
            StructField("tract_label", StringType(), False),
            StructField("feature_class_code", StringType(), False),
            StructField("functional_status", StringType(), False),
            StructField("land_area_sqm", LongType(), False),
            StructField("water_area_sqm", LongType(), False),
            StructField("internal_point_latitude", DoubleType(), False),
            StructField("internal_point_longitude", DoubleType(), False),
        ]
    )
    frame = spark.createDataFrame(records, schema=frame_schema)
    row_count = frame.count()
    invalid_rows = frame.where(
        (functions.col("state_fips") != "09")
        | (~functions.col("geoid").rlike("^09[0-9]{9}$"))
        | (
            functions.col("geoid")
            != functions.concat("state_fips", "county_fips", "tract_code")
        )
        | (functions.col("land_area_sqm") < 0)
        | (functions.col("water_area_sqm") < 0)
        | (~functions.col("internal_point_latitude").between(-90, 90))
        | (~functions.col("internal_point_longitude").between(-180, 180))
    ).count()
    duplicate_geoids = frame.groupBy("geoid").count().where(functions.col("count") > 1).count()
    if row_count == 0 or invalid_rows or duplicate_geoids:
        raise ValueError(
            "Connecticut tract reference bronze validation failed: "
            f"rows={row_count}, invalid_rows={invalid_rows}, "
            f"duplicate_geoids={duplicate_geoids}"
        )

    schema_fingerprint = hashlib.sha256(frame.schema.json().encode("utf-8")).hexdigest()
    profiled_manifest = manifest.with_profile(
        row_count=row_count,
        schema_fingerprint=schema_fingerprint,
        validation_status="bronze_validated",
        validation_messages=(
            "Reference attributes support Connecticut tract identity reconciliation; "
            "water-only tracts are not used to transfer ACS profiles.",
        ),
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

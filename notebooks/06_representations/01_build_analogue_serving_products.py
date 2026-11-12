# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Publish current historical analogue serving products
# MAGIC
# MAGIC This job applies the exact retrieval policy validated by job 604 to every eligible current
# MAGIC tract. It publishes compact matches, descriptive outcome summaries, and explicit
# MAGIC availability states. All tables are versioned and append-only. The manifest is written last,
# MAGIC so an incomplete release cannot become an approved application input.

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

import numpy as np
import pandas as pd
from pyspark.ml.functions import vector_to_array
from pyspark.sql import functions, types

from neighborhood_twin.analogue_serving import (
    ANALOGUE_SERVING_AVAILABILITY_TABLE,
    ANALOGUE_SERVING_MATCH_TABLE,
    ANALOGUE_SERVING_SUMMARY_TABLE,
    SERVING_RELEASE_MANIFEST_TABLE,
    build_indexed_match_frame,
    build_release_manifest,
    build_serving_availability_frame,
    build_serving_match_frame,
    build_serving_summary_frame,
    new_analogue_serving_release,
    validate_serving_outputs,
)
from neighborhood_twin.analogue_serving_retrieval import (
    DEFAULT_KD_TREE_CONFIGURATION,
    KDTreeConfiguration,
    build_exact_kd_tree,
    query_exact_kd_tree,
    validate_tree_inputs,
)
from neighborhood_twin.current_analogues import LOCKED_TEMPORAL_ROLE
from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.historical_analogues import (
    add_weighted_analogue_vector,
    fit_analogue_preprocessing,
    validate_analogue_columns,
)

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("model_schema", "neighborhood_twin_model", "Model schema")
dbutils.widgets.text("serving_schema", "neighborhood_twin_serving", "Serving schema")
dbutils.widgets.text("modeling_panel_table", "gold_modeling_panel", "Modeling panel")
dbutils.widgets.text(
    "current_profile_table", "gold_tract_profile_current", "Current tract profile"
)
dbutils.widgets.text(
    "tree_reference_table", "analogue_tree_benchmark_match", "Approved tree evidence"
)
dbutils.widgets.text("match_table", ANALOGUE_SERVING_MATCH_TABLE, "Serving matches")
dbutils.widgets.text("summary_table", ANALOGUE_SERVING_SUMMARY_TABLE, "Serving summaries")
dbutils.widgets.text(
    "availability_table", ANALOGUE_SERVING_AVAILABILITY_TABLE, "Serving availability"
)
dbutils.widgets.text(
    "manifest_table", SERVING_RELEASE_MANIFEST_TABLE, "Serving release manifest"
)
dbutils.widgets.text("horizons", "1,3", "Comma-separated outcome horizons")
dbutils.widgets.text("top_k", "10", "Distinct historical communities")
dbutils.widgets.text("as_of_year", "", "Optional current year; blank uses latest")
dbutils.widgets.text(
    "leaf_size", str(DEFAULT_KD_TREE_CONFIGURATION.leaf_size), "KD-tree leaf size"
)
dbutils.widgets.text(
    "initial_neighbors",
    str(DEFAULT_KD_TREE_CONFIGURATION.initial_neighbors),
    "Initial candidate states requested per query",
)
dbutils.widgets.text(
    "expansion_factor",
    str(DEFAULT_KD_TREE_CONFIGURATION.expansion_factor),
    "Candidate-state expansion factor",
)
dbutils.widgets.text(
    "query_batch_size",
    str(DEFAULT_KD_TREE_CONFIGURATION.query_batch_size),
    "Queries per measured tree batch",
)


def _parse_int_tuple(value: str, *, label: str) -> tuple[int, ...]:
    """Parse one required comma-separated tuple of integers."""

    parsed = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not parsed:
        raise ValueError(f"{label} must contain at least one value")
    return parsed


catalog = dbutils.widgets.get("catalog").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
model_schema = dbutils.widgets.get("model_schema").strip()
serving_schema = dbutils.widgets.get("serving_schema").strip()
modeling_panel_table = dbutils.widgets.get("modeling_panel_table").strip()
current_profile_table = dbutils.widgets.get("current_profile_table").strip()
tree_reference_table = dbutils.widgets.get("tree_reference_table").strip()
match_table = dbutils.widgets.get("match_table").strip()
summary_table = dbutils.widgets.get("summary_table").strip()
availability_table = dbutils.widgets.get("availability_table").strip()
manifest_table = dbutils.widgets.get("manifest_table").strip()
horizons = _parse_int_tuple(dbutils.widgets.get("horizons"), label="horizons")
top_k = int(dbutils.widgets.get("top_k"))
as_of_value = dbutils.widgets.get("as_of_year").strip()
requested_as_of_year = int(as_of_value) if as_of_value else None
configuration = KDTreeConfiguration(
    leaf_size=int(dbutils.widgets.get("leaf_size")),
    initial_neighbors=int(dbutils.widgets.get("initial_neighbors")),
    expansion_factor=int(dbutils.widgets.get("expansion_factor")),
    query_batch_size=int(dbutils.widgets.get("query_batch_size")),
)
if (
    match_table,
    summary_table,
    availability_table,
    manifest_table,
) != (
    ANALOGUE_SERVING_MATCH_TABLE,
    ANALOGUE_SERVING_SUMMARY_TABLE,
    ANALOGUE_SERVING_AVAILABILITY_TABLE,
    SERVING_RELEASE_MANIFEST_TABLE,
):
    raise ValueError("Serving table names are fixed by the versioned release contract")

panel_name = qualified_name(catalog, gold_schema, modeling_panel_table)
profile_name = qualified_name(catalog, gold_schema, current_profile_table)
tree_reference_name = qualified_name(catalog, model_schema, tree_reference_table)
panel = spark.table(panel_name)
current_profile = spark.table(profile_name)
tree_reference = spark.table(tree_reference_name)
validate_analogue_columns(panel.columns)

latest_year = panel.agg(functions.max("forecast_origin_year")).first()[0]
if latest_year is None:
    raise ValueError("The modeling panel contains no forecast-origin years")
as_of_year = requested_as_of_year or int(latest_year)
if as_of_year > int(latest_year):
    raise ValueError("The requested as-of year exceeds the latest model-ready origin")

tree_run_ids = {
    row[0] for row in tree_reference.select("analogue_tree_run_id").distinct().collect()
}
tree_as_of_years = {
    int(row[0]) for row in tree_reference.select("analogue_tree_as_of_year").distinct().collect()
}
panel_build_ids = {
    row[0] for row in panel.select("model_readiness_build_id").distinct().collect()
}
reference_build_ids = {
    row[0]
    for row in tree_reference.select("query_model_readiness_build_id").distinct().collect()
}
reference_build_ids.update(
    row[0]
    for row in tree_reference.select("candidate_model_readiness_build_id").distinct().collect()
)
if len(tree_run_ids) != 1 or tree_as_of_years != {as_of_year}:
    raise RuntimeError("Job 604 must contain one approved run for the requested as-of year")
if len(panel_build_ids) != 1 or reference_build_ids != panel_build_ids:
    raise RuntimeError("Job 604 must be refreshed after the current model-readiness build")
model_readiness_build_id = next(iter(panel_build_ids))
source_tree_run_id = next(iter(tree_run_ids))

if current_profile.groupBy("geoid_2020").count().where(
    functions.col("count") != 1
).limit(1).count():
    raise RuntimeError("The current profile is not unique by canonical tract")

# COMMAND ----------


def _vector_matrix(values: pd.Series) -> np.ndarray:
    """Convert a pandas series of Spark arrays into one finite float64 matrix."""

    matrix = np.asarray(values.tolist(), dtype=np.float64)
    if matrix.ndim != 2 or not np.isfinite(matrix).all():
        raise RuntimeError("Collected analogue vectors are not a finite two-dimensional matrix")
    return matrix


def _collect_index_arrays(represented):
    """Collect the current-query and historical-candidate arrays for one horizon."""

    candidates = represented.where(
        functions.col("target_is_observed")
        & (functions.col("geographic_role") == "geographic_development")
        & (functions.col("temporal_role") != LOCKED_TEMPORAL_ROLE)
        & (functions.col("target_end_year") <= as_of_year)
    )
    queries = represented.where(functions.col("forecast_origin_year") == as_of_year)
    candidate_pdf = (
        candidates.select(
            functions.col("geoid_2020").cast("long").alias("geoid_numeric"),
            functions.col("forecast_origin_year").cast("integer").alias("origin_year"),
            vector_to_array("analogue_weighted_vector").alias("weighted_vector"),
        )
        .orderBy("geoid_numeric", "origin_year")
        .toPandas()
    )
    query_pdf = (
        queries.select(
            functions.col("geoid_2020").cast("long").alias("geoid_numeric"),
            vector_to_array("analogue_weighted_vector").alias("weighted_vector"),
        )
        .orderBy("geoid_numeric")
        .toPandas()
    )
    candidate_vectors = _vector_matrix(candidate_pdf["weighted_vector"])
    query_vectors = _vector_matrix(query_pdf["weighted_vector"])
    candidate_geoids = candidate_pdf["geoid_numeric"].to_numpy(dtype=np.int64)
    candidate_origin_years = candidate_pdf["origin_year"].to_numpy(dtype=np.int64)
    query_geoids = query_pdf["geoid_numeric"].to_numpy(dtype=np.int64)
    validate_tree_inputs(
        candidate_vectors,
        candidate_geoids,
        candidate_origin_years,
        query_vectors,
        query_geoids,
        top_k=top_k,
    )
    if len(np.unique(query_geoids)) != len(query_geoids):
        raise RuntimeError("Current analogue queries are not unique by tract")
    return (
        candidate_vectors,
        candidate_geoids,
        candidate_origin_years,
        query_vectors,
        query_geoids,
    )


def _build_key_frame(
    result,
    query_geoids: np.ndarray,
    candidate_geoids: np.ndarray,
    candidate_origin_years: np.ndarray,
    *,
    horizon_years: int,
):
    """Create Spark keys from exact indexed arrays without Python row-by-row records."""

    candidate_positions = result.neighbors.candidate_indices.reshape(-1)
    query_count = len(query_geoids)
    numeric_pdf = pd.DataFrame(
        {
            "query_geoid_numeric": np.repeat(query_geoids, top_k),
            "query_origin_year": np.full(query_count * top_k, as_of_year, dtype=np.int32),
            "horizon_years": np.full(query_count * top_k, horizon_years, dtype=np.int32),
            "candidate_geoid_numeric": candidate_geoids[candidate_positions],
            "candidate_origin_year": candidate_origin_years[candidate_positions].astype(
                np.int32
            ),
            "similarity_distance": result.neighbors.distances.reshape(-1),
            "match_rank": np.tile(np.arange(1, top_k + 1, dtype=np.int32), query_count),
            "retrieved_state_count": np.repeat(
                result.neighbors.retrieved_state_counts.astype(np.int32), top_k
            ),
            "tree_expansion_count": np.repeat(
                result.neighbors.expansion_counts.astype(np.int32), top_k
            ),
        }
    )
    numeric_schema = types.StructType(
        [
            types.StructField("query_geoid_numeric", types.LongType(), False),
            types.StructField("query_origin_year", types.IntegerType(), False),
            types.StructField("horizon_years", types.IntegerType(), False),
            types.StructField("candidate_geoid_numeric", types.LongType(), False),
            types.StructField("candidate_origin_year", types.IntegerType(), False),
            types.StructField("similarity_distance", types.DoubleType(), False),
            types.StructField("match_rank", types.IntegerType(), False),
            types.StructField("retrieved_state_count", types.IntegerType(), False),
            types.StructField("tree_expansion_count", types.IntegerType(), False),
        ]
    )
    return spark.createDataFrame(numeric_pdf, schema=numeric_schema).select(
        functions.lpad(functions.col("query_geoid_numeric").cast("string"), 11, "0").alias(
            "query_geoid_2020"
        ),
        "query_origin_year",
        "horizon_years",
        functions.lpad(
            functions.col("candidate_geoid_numeric").cast("string"), 11, "0"
        ).alias("candidate_geoid_2020"),
        "candidate_origin_year",
        "similarity_distance",
        "match_rank",
        "retrieved_state_count",
        "tree_expansion_count",
    )


# COMMAND ----------

horizon_matches = []
retrieval_metrics = []
for horizon in horizons:
    horizon_panel = panel.where(functions.col("horizon_years") == horizon)
    represented = add_weighted_analogue_vector(
        fit_analogue_preprocessing(horizon_panel)
    ).cache()
    represented.count()
    (
        candidate_vectors,
        candidate_geoids,
        candidate_origin_years,
        query_vectors,
        query_geoids,
    ) = _collect_index_arrays(represented)
    tree, build_seconds = build_exact_kd_tree(
        candidate_vectors, leaf_size=configuration.leaf_size
    )
    result = query_exact_kd_tree(
        tree,
        candidate_geoids,
        candidate_origin_years,
        query_vectors,
        query_geoids,
        top_k=top_k,
        configuration=configuration,
    )
    keys = _build_key_frame(
        result,
        query_geoids,
        candidate_geoids,
        candidate_origin_years,
        horizon_years=horizon,
    )
    horizon_match = build_indexed_match_frame(
        represented,
        keys,
        as_of_year=as_of_year,
        horizon_years=horizon,
    ).cache()
    horizon_match.count()
    horizon_matches.append(horizon_match)
    retrieval_metrics.append(
        (
            int(horizon),
            int(len(query_geoids)),
            int(len(candidate_geoids)),
            float(build_seconds),
            float(result.query_elapsed_seconds),
            int(result.distance_computation_count),
            int(result.neighbors.retrieved_state_counts.max()),
            int(result.neighbors.expansion_counts.max()),
        )
    )
    represented.unpersist()

indexed_matches = horizon_matches[0]
for frame in horizon_matches[1:]:
    indexed_matches = indexed_matches.unionByName(frame)

release = new_analogue_serving_release(
    as_of_year=as_of_year,
    horizons=horizons,
    top_k=top_k,
    model_readiness_build_id=model_readiness_build_id,
    source_tree_run_id=source_tree_run_id,
)
serving_matches = build_serving_match_frame(indexed_matches, current_profile, release).cache()
serving_summary = build_serving_summary_frame(
    indexed_matches, current_profile, release
).cache()
serving_availability = build_serving_availability_frame(
    current_profile, indexed_matches, release
).cache()
row_counts = validate_serving_outputs(
    serving_matches, serving_summary, serving_availability, release
)
manifest = build_release_manifest(spark, release, row_counts)

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{serving_schema}`")
spark.sql(
    f"COMMENT ON SCHEMA `{catalog}`.`{serving_schema}` IS "
    "'Versioned, validated products approved for application and reporting use.'"
)

published_frames = (
    (match_table, serving_matches),
    (summary_table, serving_summary),
    (availability_table, serving_availability),
)
for table, frame in published_frames:
    raw_name = f"{catalog}.{serving_schema}.{table}"
    table_name = qualified_name(catalog, serving_schema, table)
    if spark.catalog.tableExists(raw_name) and spark.table(raw_name).where(
        functions.col("serving_release_id") == release.release_id
    ).limit(1).count():
        raise RuntimeError(f"Serving release already exists in {raw_name}")
    writer = frame.write.format("delta").mode("append")
    if not spark.catalog.tableExists(raw_name):
        writer = writer.partitionBy("serving_release_id")
    writer.saveAsTable(table_name)

# The manifest is the release activation record and must always be published last.
manifest_raw_name = f"{catalog}.{serving_schema}.{manifest_table}"
manifest_name = qualified_name(catalog, serving_schema, manifest_table)
if spark.catalog.tableExists(manifest_raw_name) and spark.table(manifest_raw_name).where(
    functions.col("serving_release_id") == release.release_id
).limit(1).count():
    raise RuntimeError(f"Serving release already exists in {manifest_raw_name}")
manifest_writer = manifest.write.format("delta").mode("append")
if not spark.catalog.tableExists(manifest_raw_name):
    manifest_writer = manifest_writer.partitionBy("serving_release_id")
manifest_writer.saveAsTable(manifest_name)

for table, expected_count in row_counts.items():
    raw_name = f"{catalog}.{serving_schema}.{table}"
    published_count = spark.table(raw_name).where(
        functions.col("serving_release_id") == release.release_id
    ).count()
    if published_count != expected_count:
        raise RuntimeError(
            f"Published serving count differs for {raw_name}: "
            f"expected={expected_count}, actual={published_count}"
        )
published_manifest = spark.table(manifest_raw_name).where(
    functions.col("serving_release_id") == release.release_id
)
if published_manifest.count() != len(row_counts):
    raise RuntimeError("Published manifest does not contain every serving table")

metrics_frame = spark.createDataFrame(
    retrieval_metrics,
    "horizon_years integer, query_count long, candidate_state_count long, "
    "tree_build_seconds double, query_seconds double, distance_computation_count long, "
    "maximum_retrieved_state_count integer, maximum_tree_expansion_count integer",
)
display(metrics_frame.orderBy("horizon_years"))
display(
    serving_availability.groupBy("horizon_years", "availability_reason")
    .count()
    .orderBy("horizon_years", "availability_reason")
)
display(serving_summary.orderBy("horizon_years", "query_geoid_2020").limit(20))
display(published_manifest.orderBy("table_name"))
print(f"Activated analogue serving release {release.release_id} in {serving_schema}.")

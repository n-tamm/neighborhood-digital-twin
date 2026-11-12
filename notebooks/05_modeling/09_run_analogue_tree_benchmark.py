# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Exact indexed historical analogue retrieval
# MAGIC
# MAGIC This workflow tests whether an exact scikit-learn KD-tree can replace the exhaustive Spark
# MAGIC query-candidate cross join for current-neighborhood retrieval. It compares the indexed
# MAGIC results with job 603's frozen exact benchmark, measures actual distance computations, and
# MAGIC times larger current-query batches without accessing locked temporal-test outcomes.

# COMMAND ----------

import sys
from pathlib import Path, PurePosixPath


def _add_repository_source() -> None:
    """Make the deployed repository package importable by this notebook."""

    for candidate in [Path.cwd(), *Path.cwd().parents]:
        source_root = candidate / "src"
        if (source_root / "neighborhood_twin").exists():
            sys.path.insert(0, str(source_root))
            return
    raise RuntimeError("Could not locate the repository src directory")


_add_repository_source()

# COMMAND ----------

from datetime import UTC, datetime

import mlflow
import numpy as np
import sklearn
from databricks.sdk import WorkspaceClient
from pyspark.ml.functions import vector_to_array
from pyspark.sql import functions, types

from neighborhood_twin.analogue_serving_retrieval import (
    ANALOGUE_TREE_MATCH_TABLE,
    ANALOGUE_TREE_QUERY_EVALUATION_TABLE,
    ANALOGUE_TREE_RETRIEVAL_CONFIG,
    ANALOGUE_TREE_SCALE_TABLE,
    ANALOGUE_TREE_SCHEMA_VERSION,
    ANALOGUE_TREE_SUMMARY_TABLE,
    DEFAULT_KD_TREE_CONFIGURATION,
    KDTreeConfiguration,
    build_exact_kd_tree,
    kd_tree_array_bytes,
    kd_tree_match_key_records,
    kd_tree_scale_metrics,
    query_exact_kd_tree,
    validate_tree_inputs,
)
from neighborhood_twin.current_analogues import (
    CURRENT_ANALOGUE_REPRESENTATION,
    LOCKED_TEMPORAL_ROLE,
)
from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.historical_analogues import (
    add_weighted_analogue_vector,
    fit_analogue_preprocessing,
    validate_analogue_columns,
)
from neighborhood_twin.scalable_analogues import (
    EXACT_REFERENCE_CONFIG,
    SCALABLE_ANALOGUE_MATCH_TABLE,
    build_query_evaluation,
)

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("model_schema", "neighborhood_twin_model", "Model-output schema")
dbutils.widgets.text(
    "evaluation_schema", "neighborhood_twin_evaluation", "Model-evaluation schema"
)
dbutils.widgets.text("modeling_panel_table", "gold_modeling_panel", "Modeling panel")
dbutils.widgets.text(
    "exact_reference_table",
    SCALABLE_ANALOGUE_MATCH_TABLE,
    "Job-603 exact-reference matches",
)
dbutils.widgets.text("match_table", ANALOGUE_TREE_MATCH_TABLE, "Tree benchmark matches")
dbutils.widgets.text(
    "query_evaluation_table",
    ANALOGUE_TREE_QUERY_EVALUATION_TABLE,
    "Query-level tree fidelity",
)
dbutils.widgets.text("summary_table", ANALOGUE_TREE_SUMMARY_TABLE, "Tree summary")
dbutils.widgets.text("scale_table", ANALOGUE_TREE_SCALE_TABLE, "Scale benchmark")
dbutils.widgets.text("horizons", "1,3", "Comma-separated outcome horizons")
dbutils.widgets.text("top_k", "10", "Distinct historical communities")
dbutils.widgets.text("as_of_year", "", "Optional query year; blank uses latest")
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
    "scale_sample_size", "1000", "Deterministic intermediate current-query sample"
)
dbutils.widgets.text(
    "mlflow_experiment",
    "/Shared/neighborhood-digital-twin/analogue-tree-retrieval",
    "Shared MLflow experiment path",
)


def _parse_int_tuple(value: str, *, label: str) -> tuple[int, ...]:
    """Parse a required comma-separated integer tuple."""

    parsed = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not parsed:
        raise ValueError(f"{label} must contain at least one value")
    return parsed


catalog = dbutils.widgets.get("catalog").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
model_schema = dbutils.widgets.get("model_schema").strip()
evaluation_schema = dbutils.widgets.get("evaluation_schema").strip()
modeling_panel_table = dbutils.widgets.get("modeling_panel_table").strip()
exact_reference_table = dbutils.widgets.get("exact_reference_table").strip()
match_table = dbutils.widgets.get("match_table").strip()
query_evaluation_table = dbutils.widgets.get("query_evaluation_table").strip()
summary_table = dbutils.widgets.get("summary_table").strip()
scale_table = dbutils.widgets.get("scale_table").strip()
horizons = _parse_int_tuple(dbutils.widgets.get("horizons"), label="horizons")
top_k = int(dbutils.widgets.get("top_k"))
as_of_value = dbutils.widgets.get("as_of_year").strip()
requested_as_of_year = int(as_of_value) if as_of_value else None
scale_sample_size = int(dbutils.widgets.get("scale_sample_size"))
configuration = KDTreeConfiguration(
    leaf_size=int(dbutils.widgets.get("leaf_size")),
    initial_neighbors=int(dbutils.widgets.get("initial_neighbors")),
    expansion_factor=int(dbutils.widgets.get("expansion_factor")),
)
experiment_path = dbutils.widgets.get("mlflow_experiment").strip()

panel_name = qualified_name(catalog, gold_schema, modeling_panel_table)
reference_name = qualified_name(catalog, model_schema, exact_reference_table)
panel = spark.table(panel_name)
exact_reference_source = spark.table(reference_name)
validate_analogue_columns(panel.columns)

latest_year = panel.agg(functions.max("forecast_origin_year")).first()[0]
if latest_year is None:
    raise ValueError("The modeling panel contains no forecast-origin years")
as_of_year = requested_as_of_year or int(latest_year)
if as_of_year > int(latest_year):
    raise ValueError("The requested as-of year exceeds the latest model-ready origin")
if scale_sample_size <= 0:
    raise ValueError("scale_sample_size must be positive")

exact_reference = exact_reference_source.where(
    (functions.col("retrieval_config_name") == EXACT_REFERENCE_CONFIG)
    & functions.col("horizon_years").isin(*horizons)
)
if exact_reference.select("scalable_analogue_run_id").distinct().count() != 1:
    raise RuntimeError("Job 603 must publish exactly one exact-reference run")
if exact_reference.where(functions.col("query_origin_year") != as_of_year).limit(1).count():
    raise RuntimeError("Job 603's exact reference does not match the requested as-of year")
panel_build_ids = {
    row[0] for row in panel.select("model_readiness_build_id").distinct().collect()
}
reference_build_ids = {
    row[0]
    for row in exact_reference.select("query_model_readiness_build_id").distinct().collect()
}
reference_build_ids.update(
    row[0]
    for row in exact_reference.select("candidate_model_readiness_build_id").distinct().collect()
)
if len(panel_build_ids) != 1 or reference_build_ids != panel_build_ids:
    raise RuntimeError("Job 603 must be refreshed after the current model-readiness build")

benchmark_geoids = tuple(
    row[0]
    for row in exact_reference.select("query_geoid_2020").distinct().orderBy(
        "query_geoid_2020"
    ).collect()
)
if not benchmark_geoids:
    raise RuntimeError("Job 603 contains no exact-reference benchmark queries")

# COMMAND ----------


def ensure_experiment_parent(experiment: str) -> None:
    """Create the shared Workspace folder required by a nested MLflow experiment path."""

    if not experiment.startswith("/"):
        raise ValueError("The Databricks MLflow experiment path must be absolute")
    WorkspaceClient().workspace.mkdirs(str(PurePosixPath(experiment).parent))


def _vector_matrix(values) -> np.ndarray:
    """Convert a pandas series of Spark vector arrays into one finite float64 matrix."""

    matrix = np.asarray(values.tolist(), dtype=np.float64)
    if matrix.ndim != 2 or not np.isfinite(matrix).all():
        raise RuntimeError("Collected analogue vectors are not a finite two-dimensional matrix")
    return matrix


def _collect_index_arrays(represented, *, horizon: int):
    """Collect the bounded vector and key arrays needed by one exact driver-side index."""

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
            functions.xxhash64("geoid_2020").alias("sample_hash"),
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
        raise RuntimeError(f"Horizon {horizon} current queries are not unique by tract")
    return (
        candidates,
        queries,
        candidate_vectors,
        candidate_geoids,
        candidate_origin_years,
        query_pdf,
        query_vectors,
        query_geoids,
    )


def _query_positions(query_geoids: np.ndarray, selected_geoids: tuple[str, ...]) -> np.ndarray:
    """Resolve declared tract GEOIDs to positions in the sorted current-query matrix."""

    positions = {int(geoid): position for position, geoid in enumerate(query_geoids.tolist())}
    missing = sorted(geoid for geoid in selected_geoids if int(geoid) not in positions)
    if missing:
        raise RuntimeError("Current indexed queries are missing: " + ", ".join(missing))
    return np.asarray([positions[int(geoid)] for geoid in selected_geoids], dtype=np.int64)


def _build_match_frame(represented, key_records, *, horizon: int):
    """Enrich indexed query-candidate keys with the governed match-level contract."""

    key_schema = types.StructType(
        [
            types.StructField("query_geoid_2020", types.StringType(), False),
            types.StructField("query_origin_year", types.IntegerType(), False),
            types.StructField("horizon_years", types.IntegerType(), False),
            types.StructField("candidate_geoid_2020", types.StringType(), False),
            types.StructField("candidate_origin_year", types.IntegerType(), False),
            types.StructField("similarity_distance", types.DoubleType(), False),
            types.StructField("match_rank", types.IntegerType(), False),
            types.StructField("retrieved_state_count", types.IntegerType(), False),
            types.StructField("tree_expansion_count", types.IntegerType(), False),
        ]
    )
    keys = spark.createDataFrame(key_records, schema=key_schema)
    queries = represented.where(functions.col("forecast_origin_year") == as_of_year).select(
        functions.col("geoid_2020").alias("query_geoid_2020"),
        functions.col("forecast_origin_year").alias("query_origin_year"),
        "horizon_years",
        functions.col("forecast_origin_year").alias("query_as_of_year"),
        functions.col("target_end_year").alias("query_forecast_end_year"),
        functions.col("state_abbreviation").alias("query_state_abbreviation"),
        functions.col("county_name").alias("query_county_name"),
        functions.col("region_name").alias("query_region_name"),
        functions.col("modeling_cohort").alias("query_modeling_cohort"),
        functions.col("temporal_role").alias("query_temporal_role"),
        functions.col("geographic_role").alias("query_geographic_role"),
        functions.col("model_readiness_build_id").alias("query_model_readiness_build_id"),
    )
    candidates = represented.where(
        functions.col("target_is_observed")
        & (functions.col("geographic_role") == "geographic_development")
        & (functions.col("temporal_role") != LOCKED_TEMPORAL_ROLE)
        & (functions.col("target_end_year") <= as_of_year)
    ).select(
        functions.col("geoid_2020").alias("candidate_geoid_2020"),
        functions.col("forecast_origin_year").alias("candidate_origin_year"),
        "horizon_years",
        functions.col("target_end_year").alias("candidate_target_end_year"),
        functions.col("target_cumulative_log_change").alias(
            "candidate_target_cumulative_log_change"
        ),
        functions.col("target_annualized_change_pct").alias(
            "candidate_target_annualized_change_pct"
        ),
        functions.col("state_abbreviation").alias("candidate_state_abbreviation"),
        functions.col("county_name").alias("candidate_county_name"),
        functions.col("region_name").alias("candidate_region_name"),
        functions.col("modeling_cohort").alias("candidate_modeling_cohort"),
        functions.col("temporal_role").alias("candidate_temporal_role"),
        functions.col("model_readiness_build_id").alias(
            "candidate_model_readiness_build_id"
        ),
    )
    return (
        keys.join(
            functions.broadcast(queries),
            ["query_geoid_2020", "query_origin_year", "horizon_years"],
            "inner",
        )
        .join(
            candidates,
            ["candidate_geoid_2020", "candidate_origin_year", "horizon_years"],
            "inner",
        )
        .withColumn("representation_name", functions.lit(CURRENT_ANALOGUE_REPRESENTATION))
        .withColumn(
            "candidate_age_years",
            functions.lit(as_of_year) - functions.col("candidate_origin_year"),
        )
        .withColumn("unique_candidate_tract", functions.lit(True))
        .withColumn("locked_temporal_candidates_excluded", functions.lit(True))
        .withColumn("retrieval_config_name", functions.lit(ANALOGUE_TREE_RETRIEVAL_CONFIG))
        .withColumn("retrieval_method", functions.lit("exact_kd_tree_distinct_tract"))
        .withColumn("tree_leaf_size", functions.lit(configuration.leaf_size))
        .withColumn("tree_initial_neighbors", functions.lit(configuration.initial_neighbors))
        .withColumn("tree_expansion_factor", functions.lit(configuration.expansion_factor))
        .where(functions.col("horizon_years") == horizon)
    )


def _add_lineage(frame, *, run_id: str, built_at_utc: str):
    """Attach exact indexed-retrieval schema, run, and current-year lineage."""

    return (
        frame.withColumn(
            "analogue_tree_schema_version", functions.lit(ANALOGUE_TREE_SCHEMA_VERSION)
        )
        .withColumn("analogue_tree_run_id", functions.lit(run_id))
        .withColumn(
            "analogue_tree_built_at_utc", functions.to_timestamp(functions.lit(built_at_utc))
        )
        .withColumn("analogue_tree_as_of_year", functions.lit(as_of_year))
    )


def _build_summary(query_evaluation, scale_frame, build_rows):
    """Combine exact-reference fidelity with index construction and pruning evidence."""

    fidelity = query_evaluation.groupBy("horizon_years", "retrieval_config_name").agg(
        functions.count(functions.lit(1)).alias("query_count"),
        functions.avg(functions.col("complete_top_k").cast("double")).alias(
            "complete_top_k_share"
        ),
        functions.avg("exact_top_k_recall").alias("mean_exact_top_k_recall"),
        functions.min("exact_top_k_recall").alias("minimum_exact_top_k_recall"),
        functions.avg("exact_candidate_state_recall").alias(
            "mean_exact_candidate_state_recall"
        ),
        functions.min("exact_candidate_state_recall").alias(
            "minimum_exact_candidate_state_recall"
        ),
        functions.avg("top_k_jaccard_similarity").alias(
            "mean_top_k_jaccard_similarity"
        ),
        functions.avg("mean_shared_rank_displacement").alias(
            "mean_shared_rank_displacement"
        ),
        functions.avg(functions.abs("median_outcome_drift_log_change")).alias(
            "mean_absolute_median_outcome_drift_log_change"
        ),
        functions.avg(functions.abs("inverse_distance_outcome_drift_log_change")).alias(
            "mean_absolute_inverse_distance_outcome_drift_log_change"
        ),
    )
    build_frame = spark.createDataFrame(build_rows)
    benchmark_work = scale_frame.where(functions.col("sample_name") == "job_603_benchmark").drop(
        "query_count"
    )
    return fidelity.join(benchmark_work, "horizon_years", "inner").join(
        build_frame, "horizon_years", "inner"
    )


def validate_outputs(matches, query_evaluation, summary, scale) -> None:
    """Stop publication when indexed retrieval violates timing, fidelity, or scale contracts."""

    if matches.where(
        functions.col("candidate_target_end_year") > functions.col("query_as_of_year")
    ).limit(1).count():
        raise RuntimeError("Indexed retrieval contains a future candidate outcome")
    if matches.where(
        functions.col("candidate_temporal_role") == LOCKED_TEMPORAL_ROLE
    ).limit(1).count():
        raise RuntimeError("Indexed retrieval accessed a locked temporal-test candidate")
    if matches.where(
        functions.col("candidate_geoid_2020") == functions.col("query_geoid_2020")
    ).limit(1).count():
        raise RuntimeError("Indexed retrieval contains a same-tract result")
    groups = matches.groupBy(
        "query_geoid_2020", "query_origin_year", "horizon_years"
    ).agg(
        functions.count(functions.lit(1)).alias("match_count"),
        functions.countDistinct("candidate_geoid_2020").alias("tract_count"),
    )
    if groups.where(
        (functions.col("match_count") != top_k) | (functions.col("tract_count") != top_k)
    ).limit(1).count():
        raise RuntimeError("Indexed retrieval lacks a complete distinct top-k")
    if query_evaluation.where(
        ~functions.col("complete_top_k")
        | (functions.col("exact_top_k_recall") != 1.0)
        | (functions.col("exact_candidate_state_recall") != 1.0)
        | (functions.col("top_k_jaccard_similarity") != 1.0)
        | (functions.col("exact_top_three_retention_share") != 1.0)
        | (functions.abs("mean_shared_rank_displacement") > 1e-12)
        | (functions.abs("median_outcome_drift_log_change") > 1e-12)
        | (functions.abs("inverse_distance_outcome_drift_log_change") > 1e-12)
    ).limit(1).count():
        raise RuntimeError("The exact KD-tree failed to reproduce job 603")
    if summary.count() != len(horizons):
        raise RuntimeError("The tree summary lacks a horizon row")
    if scale.groupBy("horizon_years").count().where(
        functions.col("count") != 3
    ).limit(1).count():
        raise RuntimeError("The scale benchmark lacks one of its three query populations")
    if scale.where(
        (functions.col("distance_computation_ratio") < 0)
        | (functions.col("query_count") <= 0)
    ).limit(1).count():
        raise RuntimeError("The scale benchmark contains invalid work metrics")


# COMMAND ----------

ensure_experiment_parent(experiment_path)
mlflow.set_experiment(experiment_path)
with mlflow.start_run(run_name="exact-kd-tree-analogue-retrieval") as active_run:
    built_at_utc = datetime.now(UTC).isoformat()
    mlflow.log_params(
        {
            "representation": CURRENT_ANALOGUE_REPRESENTATION,
            "retrieval_method": "exact_kd_tree_distinct_tract",
            "reference_method": "job_603_exhaustive_exact",
            "locked_test_access": "prohibited",
            "horizons": ",".join(str(value) for value in horizons),
            "top_k": top_k,
            "as_of_year": as_of_year,
            "leaf_size": configuration.leaf_size,
            "initial_neighbors": configuration.initial_neighbors,
            "expansion_factor": configuration.expansion_factor,
            "scale_sample_size": scale_sample_size,
            "scikit_learn_version": sklearn.__version__,
        }
    )
    horizon_matches = []
    scale_rows = []
    build_rows = []
    for horizon in horizons:
        horizon_panel = panel.where(functions.col("horizon_years") == horizon)
        represented = add_weighted_analogue_vector(
            fit_analogue_preprocessing(horizon_panel)
        ).cache()
        represented.count()
        (
            _candidates,
            _queries,
            candidate_vectors,
            candidate_geoids,
            candidate_origin_years,
            query_pdf,
            query_vectors,
            query_geoids,
        ) = _collect_index_arrays(represented, horizon=horizon)
        tree, build_seconds = build_exact_kd_tree(
            candidate_vectors, leaf_size=configuration.leaf_size
        )
        tree_bytes = kd_tree_array_bytes(tree)
        benchmark_positions = _query_positions(query_geoids, benchmark_geoids)
        benchmark_result = query_exact_kd_tree(
            tree,
            candidate_geoids,
            candidate_origin_years,
            query_vectors[benchmark_positions],
            query_geoids[benchmark_positions],
            top_k=top_k,
            configuration=configuration,
        )
        key_records = kd_tree_match_key_records(
            benchmark_result,
            query_geoids[benchmark_positions],
            candidate_geoids,
            candidate_origin_years,
            query_origin_year=as_of_year,
            horizon_years=horizon,
        )
        horizon_matches.append(
            _build_match_frame(represented, key_records, horizon=horizon)
        )
        benchmark_metrics = kd_tree_scale_metrics(
            benchmark_result,
            horizon_years=horizon,
            sample_name="job_603_benchmark",
            candidate_state_count=len(candidate_geoids),
        )
        scale_rows.append(benchmark_metrics)

        sample_positions = (
            query_pdf.sort_values(["sample_hash", "geoid_numeric"], kind="mergesort")
            .head(min(scale_sample_size, len(query_pdf)))
            .index.to_numpy(dtype=np.int64)
        )
        intermediate_result = query_exact_kd_tree(
            tree,
            candidate_geoids,
            candidate_origin_years,
            query_vectors[sample_positions],
            query_geoids[sample_positions],
            top_k=top_k,
            configuration=configuration,
        )
        scale_rows.append(
            kd_tree_scale_metrics(
                intermediate_result,
                horizon_years=horizon,
                sample_name="deterministic_intermediate",
                candidate_state_count=len(candidate_geoids),
            )
        )
        all_result = query_exact_kd_tree(
            tree,
            candidate_geoids,
            candidate_origin_years,
            query_vectors,
            query_geoids,
            top_k=top_k,
            configuration=configuration,
        )
        scale_rows.append(
            kd_tree_scale_metrics(
                all_result,
                horizon_years=horizon,
                sample_name="all_current_eligible",
                candidate_state_count=len(candidate_geoids),
            )
        )
        build_rows.append(
            {
                "horizon_years": int(horizon),
                "tree_build_elapsed_seconds": float(build_seconds),
                "tree_array_bytes": int(tree_bytes),
                "tree_leaf_size": int(configuration.leaf_size),
                "tree_initial_neighbors": int(configuration.initial_neighbors),
                "tree_expansion_factor": int(configuration.expansion_factor),
                "current_eligible_query_count": int(len(query_geoids)),
                "candidate_state_count_from_index": int(len(candidate_geoids)),
            }
        )

    matches = horizon_matches[0]
    for frame in horizon_matches[1:]:
        matches = matches.unionByName(frame)
    scale = spark.createDataFrame(scale_rows)
    combined = exact_reference.unionByName(matches, allowMissingColumns=True)
    query_evaluation = build_query_evaluation(
        combined,
        top_k=top_k,
        configuration_names=(ANALOGUE_TREE_RETRIEVAL_CONFIG,),
    )
    summary = _build_summary(query_evaluation, scale, build_rows)
    matches = _add_lineage(
        matches, run_id=active_run.info.run_id, built_at_utc=built_at_utc
    )
    query_evaluation = _add_lineage(
        query_evaluation, run_id=active_run.info.run_id, built_at_utc=built_at_utc
    )
    summary = _add_lineage(
        summary, run_id=active_run.info.run_id, built_at_utc=built_at_utc
    )
    scale = _add_lineage(
        scale, run_id=active_run.info.run_id, built_at_utc=built_at_utc
    )
    validate_outputs(matches, query_evaluation, summary, scale)

    for row in summary.collect():
        stem = f"h{row['horizon_years']}"
        mlflow.log_metric(
            f"{stem}_mean_exact_candidate_state_recall",
            float(row["mean_exact_candidate_state_recall"]),
        )
        mlflow.log_metric(
            f"{stem}_distance_computation_ratio",
            float(row["distance_computation_ratio"]),
        )
        mlflow.log_metric(
            f"{stem}_query_elapsed_seconds",
            float(row["query_elapsed_seconds"]),
        )
        mlflow.log_metric(
            f"{stem}_tree_build_elapsed_seconds",
            float(row["tree_build_elapsed_seconds"]),
        )

# COMMAND ----------

match_name = qualified_name(catalog, model_schema, match_table)
query_evaluation_name = qualified_name(
    catalog, evaluation_schema, query_evaluation_table
)
summary_name = qualified_name(catalog, evaluation_schema, summary_table)
scale_name = qualified_name(catalog, evaluation_schema, scale_table)

for frame, table_name in (
    (matches, match_name),
    (query_evaluation, query_evaluation_name),
    (summary, summary_name),
    (scale, scale_name),
):
    (
        frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table_name)
    )

for table_name in (match_name, query_evaluation_name, summary_name, scale_name):
    published = spark.table(table_name)
    if published.select("analogue_tree_run_id").distinct().count() != 1:
        raise RuntimeError(f"Published table contains multiple run IDs: {table_name}")

display(spark.table(summary_name).orderBy("horizon_years"))
display(spark.table(scale_name).orderBy("horizon_years", "query_count"))
display(
    spark.table(query_evaluation_name).orderBy(
        "horizon_years", "exact_candidate_state_recall", "query_geoid_2020"
    )
)
print(f"Published indexed matches to {match_name}.")
print(f"Published indexed fidelity to {query_evaluation_name}.")
print(f"Published indexed summary to {summary_name}.")
print(f"Published scale evidence to {scale_name}.")
print(f"MLflow run: {active_run.info.run_id}")

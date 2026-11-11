# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Scalable historical analogue retrieval benchmark
# MAGIC
# MAGIC This workflow compares deterministic random-projection LSH candidate shortlists with the
# MAGIC exact current-neighborhood reference. Every shortlisted pair is reranked using the frozen
# MAGIC weighted-standardized distance. The benchmark measures fidelity, outcome-summary drift,
# MAGIC sample coverage, and runtime without accessing locked temporal-test outcomes.

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

import mlflow
from databricks.sdk import WorkspaceClient
from pyspark.sql import functions

from neighborhood_twin.current_analogues import (
    CURRENT_ANALOGUE_REPRESENTATION,
    LOCKED_TEMPORAL_ROLE,
)
from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.scalable_analogues import (
    DEFAULT_BENCHMARK_QUERIES_PER_GROUP,
    DEFAULT_LSH_CONFIGURATIONS,
    DEFAULT_TOP_K,
    EXACT_REFERENCE_CONFIG,
    SCALABLE_ANALOGUE_COVERAGE_TABLE,
    SCALABLE_ANALOGUE_MATCH_TABLE,
    SCALABLE_ANALOGUE_QUERY_EVALUATION_TABLE,
    SCALABLE_ANALOGUE_SUMMARY_TABLE,
    LSHConfiguration,
    build_scalable_analogue_run,
)

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("model_schema", "neighborhood_twin_model", "Model-output schema")
dbutils.widgets.text(
    "evaluation_schema", "neighborhood_twin_evaluation", "Model-evaluation schema"
)
dbutils.widgets.text("modeling_panel_table", "gold_modeling_panel", "Modeling panel")
dbutils.widgets.text("match_table", SCALABLE_ANALOGUE_MATCH_TABLE, "Benchmark matches")
dbutils.widgets.text(
    "query_evaluation_table",
    SCALABLE_ANALOGUE_QUERY_EVALUATION_TABLE,
    "Query-level fidelity table",
)
dbutils.widgets.text("summary_table", SCALABLE_ANALOGUE_SUMMARY_TABLE, "Benchmark summary")
dbutils.widgets.text("coverage_table", SCALABLE_ANALOGUE_COVERAGE_TABLE, "Query coverage")
dbutils.widgets.text("horizons", "1,3", "Comma-separated outcome horizons")
dbutils.widgets.text(
    "queries_per_group",
    str(DEFAULT_BENCHMARK_QUERIES_PER_GROUP),
    "Queries per Census-region and modeling-cohort group",
)
dbutils.widgets.text("top_k", str(DEFAULT_TOP_K), "Distinct historical communities")
dbutils.widgets.text("as_of_year", "", "Optional query year; blank uses latest")
dbutils.widgets.text(
    "lsh_config_names",
    ",".join(item.name for item in DEFAULT_LSH_CONFIGURATIONS),
    "Comma-separated LSH configuration names",
)
dbutils.widgets.text(
    "lsh_bucket_lengths",
    ",".join(str(item.bucket_length) for item in DEFAULT_LSH_CONFIGURATIONS),
    "Comma-separated random-projection bucket lengths",
)
dbutils.widgets.text(
    "lsh_num_hash_tables",
    ",".join(str(item.num_hash_tables) for item in DEFAULT_LSH_CONFIGURATIONS),
    "Comma-separated random-projection hash-table counts",
)
dbutils.widgets.text(
    "mlflow_experiment",
    "/Shared/neighborhood-digital-twin/scalable-analogue-retrieval",
    "Shared MLflow experiment path",
)


def _parse_text_tuple(value: str, *, label: str) -> tuple[str, ...]:
    """Parse a required comma-separated text tuple."""

    parsed = tuple(item.strip() for item in value.split(",") if item.strip())
    if not parsed:
        raise ValueError(f"{label} must contain at least one value")
    return parsed


def _parse_int_tuple(value: str, *, label: str) -> tuple[int, ...]:
    """Parse a required comma-separated integer tuple."""

    return tuple(int(item) for item in _parse_text_tuple(value, label=label))


def _parse_float_tuple(value: str, *, label: str) -> tuple[float, ...]:
    """Parse a required comma-separated floating-point tuple."""

    return tuple(float(item) for item in _parse_text_tuple(value, label=label))


def _parse_lsh_configurations() -> tuple[LSHConfiguration, ...]:
    """Build aligned LSH configurations from notebook parameters."""

    names = _parse_text_tuple(dbutils.widgets.get("lsh_config_names"), label="config names")
    bucket_lengths = _parse_float_tuple(
        dbutils.widgets.get("lsh_bucket_lengths"), label="bucket lengths"
    )
    hash_tables = _parse_int_tuple(
        dbutils.widgets.get("lsh_num_hash_tables"), label="hash-table counts"
    )
    if not (len(names) == len(bucket_lengths) == len(hash_tables)):
        raise ValueError("LSH configuration names, bucket lengths, and hash counts must align")
    return tuple(
        LSHConfiguration(name, bucket_length, num_hash_tables)
        for name, bucket_length, num_hash_tables in zip(
            names, bucket_lengths, hash_tables, strict=True
        )
    )


catalog = dbutils.widgets.get("catalog").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
model_schema = dbutils.widgets.get("model_schema").strip()
evaluation_schema = dbutils.widgets.get("evaluation_schema").strip()
modeling_panel_table = dbutils.widgets.get("modeling_panel_table").strip()
match_table = dbutils.widgets.get("match_table").strip()
query_evaluation_table = dbutils.widgets.get("query_evaluation_table").strip()
summary_table = dbutils.widgets.get("summary_table").strip()
coverage_table = dbutils.widgets.get("coverage_table").strip()
horizons = _parse_int_tuple(dbutils.widgets.get("horizons"), label="horizons")
queries_per_group = int(dbutils.widgets.get("queries_per_group"))
top_k = int(dbutils.widgets.get("top_k"))
as_of_value = dbutils.widgets.get("as_of_year").strip()
as_of_year = int(as_of_value) if as_of_value else None
configurations = _parse_lsh_configurations()
experiment_path = dbutils.widgets.get("mlflow_experiment").strip()

panel = spark.table(qualified_name(catalog, gold_schema, modeling_panel_table))

# COMMAND ----------


def ensure_experiment_parent(experiment: str) -> None:
    """Create the shared Workspace folder required by a nested MLflow experiment path."""

    if not experiment.startswith("/"):
        raise ValueError("The Databricks MLflow experiment path must be absolute")
    WorkspaceClient().workspace.mkdirs(str(PurePosixPath(experiment).parent))


def validate_outputs(result) -> None:
    """Stop publication when the retrieval benchmark violates hard contracts."""

    matches = result.matches
    query_evaluation = result.query_evaluation
    summary = result.summary
    coverage = result.coverage
    if matches.where(
        functions.col("candidate_target_end_year") > functions.col("query_as_of_year")
    ).limit(1).count():
        raise RuntimeError("The benchmark contains a future candidate outcome")
    if matches.where(
        functions.col("candidate_temporal_role") == LOCKED_TEMPORAL_ROLE
    ).limit(1).count():
        raise RuntimeError("The benchmark accessed a locked temporal-test candidate")
    if matches.where(
        functions.col("candidate_geoid_2020") == functions.col("query_geoid_2020")
    ).limit(1).count():
        raise RuntimeError("The benchmark contains a same-tract result")
    if matches.where(
        functions.col("representation_name") != CURRENT_ANALOGUE_REPRESENTATION
    ).limit(1).count():
        raise RuntimeError("The benchmark changed the selected analogue representation")
    if matches.where(
        ~functions.col("unique_candidate_tract")
        | ~functions.col("locked_temporal_candidates_excluded")
    ).limit(1).count():
        raise RuntimeError("The benchmark did not record its candidate safeguards")

    exact_groups = matches.where(
        functions.col("retrieval_config_name") == EXACT_REFERENCE_CONFIG
    ).groupBy("query_geoid_2020", "query_origin_year", "horizon_years").agg(
        functions.count(functions.lit(1)).alias("match_count"),
        functions.countDistinct("candidate_geoid_2020").alias("candidate_tract_count"),
    )
    if exact_groups.where(
        (functions.col("match_count") != top_k)
        | (functions.col("candidate_tract_count") != top_k)
    ).limit(1).count():
        raise RuntimeError("An exact reference query lacks a complete distinct top-k")

    expected_query_config_rows = (
        matches.where(functions.col("retrieval_config_name") == EXACT_REFERENCE_CONFIG)
        .select("query_geoid_2020", "query_origin_year", "horizon_years")
        .distinct()
        .count()
        * len(configurations)
    )
    if query_evaluation.count() != expected_query_config_rows:
        raise RuntimeError("Query evaluation does not cover every query and LSH configuration")
    if query_evaluation.where(
        (functions.col("exact_top_k_recall") < 0)
        | (functions.col("exact_top_k_recall") > 1)
        | (functions.col("exact_candidate_state_recall") < 0)
        | (functions.col("exact_candidate_state_recall") > 1)
        | (functions.col("top_k_jaccard_similarity") < 0)
        | (functions.col("top_k_jaccard_similarity") > 1)
    ).limit(1).count():
        raise RuntimeError("A fidelity metric falls outside its valid zero-to-one range")
    if summary.count() != len(horizons) * (len(configurations) + 1):
        raise RuntimeError("Benchmark summary lacks a horizon and configuration row")
    if coverage.where(
        functions.col("eligible_query_share").isNull()
        | functions.col("selected_query_share").isNull()
    ).limit(1).count():
        raise RuntimeError("Benchmark query coverage contains an undefined share")
    if coverage.where(
        functions.col("dimension_name").isin(
            "housing_composition_band",
            "community_size_band",
            "acs_uncertainty_band",
        )
        & (functions.col("coverage_status") != "covered")
    ).limit(1).count():
        raise RuntimeError("A required current-query coverage group was not selected")

    for frame, label in (
        (matches, "matches"),
        (query_evaluation, "query evaluation"),
        (summary, "summary"),
        (coverage, "coverage"),
    ):
        if frame.select("scalable_analogue_run_id").distinct().count() != 1:
            raise RuntimeError(f"Scalable analogue {label} contains multiple run IDs")


ensure_experiment_parent(experiment_path)
mlflow.set_experiment(experiment_path)
with mlflow.start_run(run_name="scalable-historical-analogue-retrieval") as active_run:
    mlflow.log_params(
        {
            "representation": CURRENT_ANALOGUE_REPRESENTATION,
            "reference_method": "exhaustive_exact",
            "approximate_method": "random_projection_lsh_shortlist_exact_rerank",
            "evaluation_role": "current_query_benchmark",
            "locked_test_access": "prohibited",
            "horizons": ",".join(str(value) for value in horizons),
            "queries_per_group": queries_per_group,
            "sampling_groups": "census_region,modeling_cohort",
            "coverage_supplements": (
                "housing_composition_band,community_size_band,acs_uncertainty_band"
            ),
            "top_k": top_k,
            "as_of_year_requested": as_of_year or "latest",
            "lsh_configurations": ";".join(
                f"{item.name}:{item.bucket_length}:{item.num_hash_tables}"
                for item in configurations
            ),
            "same_tract_exclusion": "true",
            "distinct_physical_candidate_tracts": "true",
            "locked_temporal_candidates_excluded": "true",
        }
    )
    result = build_scalable_analogue_run(
        panel,
        horizons=horizons,
        queries_per_group=queries_per_group,
        top_k=top_k,
        configurations=configurations,
        as_of_year=as_of_year,
        run_id=active_run.info.run_id,
    )
    result.matches.cache().count()
    result.query_evaluation.cache().count()
    result.summary.cache().count()
    result.coverage.cache().count()
    validate_outputs(result)

    mlflow.log_metric("as_of_year", float(result.as_of_year))
    mlflow.log_metric(
        "benchmark_query_tract_count",
        float(result.matches.select("query_geoid_2020").distinct().count()),
    )
    for row in result.summary.collect():
        stem = f"{row['retrieval_config_name']}_h{row['horizon_years']}"
        mlflow.log_metric(
            f"{stem}_retrieval_elapsed_seconds",
            float(row["retrieval_elapsed_seconds"]),
        )
        mlflow.log_metric(
            f"{stem}_mean_exact_top_k_recall",
            float(row["mean_exact_top_k_recall"]),
        )
        mlflow.log_metric(
            f"{stem}_mean_exact_candidate_state_recall",
            float(row["mean_exact_candidate_state_recall"]),
        )
        mlflow.log_metric(
            f"{stem}_complete_top_k_share",
            float(row["complete_top_k_share"]),
        )
        mlflow.log_metric(
            f"{stem}_mean_absolute_outcome_drift",
            float(row["mean_absolute_inverse_distance_outcome_drift_log_change"]),
        )

# COMMAND ----------

match_name = qualified_name(catalog, model_schema, match_table)
query_evaluation_name = qualified_name(
    catalog, evaluation_schema, query_evaluation_table
)
summary_name = qualified_name(catalog, evaluation_schema, summary_table)
coverage_name = qualified_name(catalog, evaluation_schema, coverage_table)

for frame, table_name in (
    (result.matches, match_name),
    (result.query_evaluation, query_evaluation_name),
    (result.summary, summary_name),
    (result.coverage, coverage_name),
):
    (
        frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table_name)
    )

published_matches = spark.table(match_name)
published_query_evaluation = spark.table(query_evaluation_name)
published_summary = spark.table(summary_name)
published_coverage = spark.table(coverage_name)
for table_name, frame in (
    (match_name, published_matches),
    (query_evaluation_name, published_query_evaluation),
    (summary_name, published_summary),
    (coverage_name, published_coverage),
):
    if frame.select("scalable_analogue_run_id").distinct().count() != 1:
        raise RuntimeError(f"Published table contains multiple run IDs: {table_name}")

display(published_summary.orderBy("horizon_years", "retrieval_config_name"))
display(
    published_query_evaluation.orderBy(
        "horizon_years", "retrieval_config_name", "exact_top_k_recall"
    )
)
display(published_coverage.orderBy("dimension_name", "dimension_value"))
print(f"Published benchmark matches to {match_name}.")
print(f"Published query fidelity to {query_evaluation_name}.")
print(f"Published retrieval summary to {summary_name}.")
print(f"Published query coverage to {coverage_name}.")
print(f"MLflow run: {result.run_id}")

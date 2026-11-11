# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Current-neighborhood historical analogue retrieval
# MAGIC
# MAGIC This workflow applies the frozen weighted-standardized representation to selected
# MAGIC neighborhoods at the latest model-ready year. It returns ten distinct historical
# MAGIC communities per horizon and summarizes their later outcomes as context, not as the
# MAGIC primary forecast or a calibrated interval.

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
    CURRENT_ANALOGUE_MATCH_TABLE,
    CURRENT_ANALOGUE_REPRESENTATION,
    CURRENT_ANALOGUE_SUMMARY_TABLE,
    LOCKED_TEMPORAL_ROLE,
    build_current_analogue_run,
)
from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.products import parse_state_fips_codes
from neighborhood_twin.similarity import parse_geoid_list

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("model_schema", "neighborhood_twin_model", "Model-output schema")
dbutils.widgets.text("modeling_panel_table", "gold_modeling_panel", "Modeling panel")
dbutils.widgets.text("match_table", CURRENT_ANALOGUE_MATCH_TABLE, "Current match table")
dbutils.widgets.text("summary_table", CURRENT_ANALOGUE_SUMMARY_TABLE, "Current summary table")
dbutils.widgets.text("query_geoids", "", "Optional comma-separated current tract GEOIDs")
dbutils.widgets.text("query_state_fips", "04,26,42", "Fallback query state FIPS codes")
dbutils.widgets.text("queries_per_state", "1", "Fallback queries selected per state")
dbutils.widgets.text("horizons", "1,3", "Comma-separated outcome horizons")
dbutils.widgets.text("top_k", "10", "Distinct historical communities per query and horizon")
dbutils.widgets.text("as_of_year", "", "Optional model-ready query year; blank uses latest")
dbutils.widgets.text(
    "mlflow_experiment",
    "/Shared/neighborhood-digital-twin/current-analogue-retrieval",
    "Shared MLflow experiment path",
)


def _parse_int_tuple(value: str, *, label: str) -> tuple[int, ...]:
    """Parse a required comma-separated integer tuple."""

    parsed = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not parsed:
        raise ValueError(f"{label} must contain at least one integer")
    return parsed


catalog = dbutils.widgets.get("catalog").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
model_schema = dbutils.widgets.get("model_schema").strip()
modeling_panel_table = dbutils.widgets.get("modeling_panel_table").strip()
match_table = dbutils.widgets.get("match_table").strip()
summary_table = dbutils.widgets.get("summary_table").strip()
query_geoids = parse_geoid_list(dbutils.widgets.get("query_geoids"))
query_state_fips = parse_state_fips_codes(dbutils.widgets.get("query_state_fips"))
queries_per_state = int(dbutils.widgets.get("queries_per_state"))
horizons = _parse_int_tuple(dbutils.widgets.get("horizons"), label="horizons")
top_k = int(dbutils.widgets.get("top_k"))
as_of_value = dbutils.widgets.get("as_of_year").strip()
as_of_year = int(as_of_value) if as_of_value else None
experiment_path = dbutils.widgets.get("mlflow_experiment").strip()

panel = spark.table(qualified_name(catalog, gold_schema, modeling_panel_table))

# COMMAND ----------


def ensure_experiment_parent(experiment: str) -> None:
    """Create the shared Workspace folder required by a nested MLflow experiment path."""

    if not experiment.startswith("/"):
        raise ValueError("The Databricks MLflow experiment path must be absolute")
    WorkspaceClient().workspace.mkdirs(str(PurePosixPath(experiment).parent))


def validate_outputs(result) -> None:
    """Stop publication when current retrieval violates its frozen contracts."""

    matches = result.matches
    summary = result.summary
    if matches.where(
        functions.col("query_origin_year") != functions.col("current_analogue_as_of_year")
    ).limit(1).count():
        raise RuntimeError("A current query does not use the declared as-of year")
    if matches.where(
        functions.col("candidate_target_end_year") > functions.col("query_as_of_year")
    ).limit(1).count():
        raise RuntimeError("A candidate outcome was unavailable at the query as-of year")
    if matches.where(
        functions.col("candidate_temporal_role") == LOCKED_TEMPORAL_ROLE
    ).limit(1).count():
        raise RuntimeError("Current retrieval accessed a locked temporal-test candidate")
    if matches.where(
        functions.col("candidate_geoid_2020") == functions.col("query_geoid_2020")
    ).limit(1).count():
        raise RuntimeError("Current retrieval contains a same-tract result")
    if matches.where(
        functions.col("representation_name") != CURRENT_ANALOGUE_REPRESENTATION
    ).limit(1).count():
        raise RuntimeError("Current retrieval published an unapproved representation")
    if matches.where(
        ~functions.col("unique_candidate_tract")
        | ~functions.col("locked_temporal_candidates_excluded")
    ).limit(1).count():
        raise RuntimeError("Current retrieval did not record its candidate safeguards")

    match_groups = matches.groupBy(
        "query_geoid_2020", "query_origin_year", "horizon_years"
    ).agg(
        functions.count(functions.lit(1)).alias("match_count"),
        functions.countDistinct("candidate_geoid_2020").alias("candidate_tract_count"),
        functions.min("match_rank").alias("minimum_rank"),
        functions.max("match_rank").alias("maximum_rank"),
    )
    if match_groups.where(
        (functions.col("match_count") != top_k)
        | (functions.col("candidate_tract_count") != top_k)
        | (functions.col("minimum_rank") != 1)
        | (functions.col("maximum_rank") != top_k)
    ).limit(1).count():
        raise RuntimeError("A current query lacks a complete distinct top-k match list")
    if summary.where(
        (functions.col("analogue_match_count") != top_k)
        | (functions.col("distinct_candidate_tract_count") != top_k)
        | functions.col("outcome_range_is_calibrated_interval")
    ).limit(1).count():
        raise RuntimeError("A current analogue summary violates its interpretation contract")
    if summary.select(
        "query_geoid_2020", "query_origin_year", "horizon_years"
    ).distinct().count() != summary.count():
        raise RuntimeError("Current analogue summary contains duplicate query-horizon rows")
    if matches.select("current_analogue_run_id").distinct().count() != 1:
        raise RuntimeError("Current matches contain more than one retrieval run")
    if summary.select("current_analogue_run_id").distinct().count() != 1:
        raise RuntimeError("Current summaries contain more than one retrieval run")


ensure_experiment_parent(experiment_path)
mlflow.set_experiment(experiment_path)
with mlflow.start_run(run_name="current-historical-analogue-retrieval") as active_run:
    mlflow.log_params(
        {
            "representation": CURRENT_ANALOGUE_REPRESENTATION,
            "representation_selection_source": "validated_job_602",
            "query_geoids": ",".join(query_geoids),
            "query_state_fips": ",".join(query_state_fips),
            "queries_per_state": queries_per_state,
            "horizons": ",".join(str(value) for value in horizons),
            "top_k": top_k,
            "as_of_year_requested": as_of_year or "latest",
            "same_tract_exclusion": "true",
            "distinct_physical_candidate_tracts": "true",
            "locked_temporal_candidates_excluded": "true",
            "candidate_time_rule": "candidate_target_end_year<=query_as_of_year",
            "analogue_role": "historical_context_not_primary_forecast",
        }
    )
    result = build_current_analogue_run(
        panel,
        query_geoids=query_geoids,
        query_state_fips=query_state_fips,
        queries_per_state=queries_per_state,
        horizons=horizons,
        top_k=top_k,
        as_of_year=as_of_year,
        run_id=active_run.info.run_id,
    )
    result.matches.cache().count()
    result.summary.cache().count()
    validate_outputs(result)

    mlflow.log_metric("as_of_year", float(result.as_of_year))
    mlflow.log_metric(
        "query_tract_count",
        float(result.summary.select("query_geoid_2020").distinct().count()),
    )
    mlflow.log_metric("match_row_count", float(result.matches.count()))
    for row in result.summary.groupBy("horizon_years").agg(
        functions.count(functions.lit(1)).alias("query_count"),
        functions.avg("cross_state_match_share").alias("cross_state_match_share"),
        functions.avg("mean_candidate_age_years").alias("mean_candidate_age_years"),
    ).collect():
        horizon = int(row["horizon_years"])
        mlflow.log_metric(f"h{horizon}_query_count", float(row["query_count"]))
        mlflow.log_metric(
            f"h{horizon}_cross_state_match_share",
            float(row["cross_state_match_share"]),
        )
        mlflow.log_metric(
            f"h{horizon}_mean_candidate_age_years",
            float(row["mean_candidate_age_years"]),
        )

# COMMAND ----------

match_name = qualified_name(catalog, model_schema, match_table)
summary_name = qualified_name(catalog, model_schema, summary_table)

for frame, table_name in (
    (result.matches, match_name),
    (result.summary, summary_name),
):
    (
        frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table_name)
    )

published_matches = spark.table(match_name)
published_summary = spark.table(summary_name)
if published_matches.select("current_analogue_run_id").distinct().count() != 1:
    raise RuntimeError("Published current matches contain more than one retrieval run")
if published_summary.select("current_analogue_run_id").distinct().count() != 1:
    raise RuntimeError("Published current summaries contain more than one retrieval run")

display(published_summary.orderBy("query_geoid_2020", "horizon_years"))
display(
    published_matches.orderBy("query_geoid_2020", "horizon_years", "match_rank")
)
print(f"Published current analogue matches to {match_name}.")
print(f"Published current analogue summaries to {summary_name}.")
print(f"Current as-of year: {result.as_of_year}")
print(f"MLflow run: {result.run_id}")

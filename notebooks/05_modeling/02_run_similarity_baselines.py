# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Current-state similarity baseline workflow
# MAGIC
# MAGIC This workflow compares two transparent neighborhood representations: standardized current
# MAGIC features and a lower-dimensional PCA representation. It retrieves exact neighbors for a
# MAGIC small review set so the team can inspect whether matches are credible before scaling the
# MAGIC method or adding historical outcome evaluation.

# COMMAND ----------

import sys
from pathlib import Path


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

from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.products import SIMILARITY_FEATURE_COLUMNS
from neighborhood_twin.similarity import (
    SIMILARITY_MATCH_TABLE,
    SIMILARITY_SUMMARY_TABLE,
    build_similarity_baseline_run,
    parse_geoid_list,
)

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text(
    "candidate_table", "gold_similarity_candidate_current", "Current similarity candidates"
)
dbutils.widgets.text("match_table", SIMILARITY_MATCH_TABLE, "Match output")
dbutils.widgets.text("summary_table", SIMILARITY_SUMMARY_TABLE, "Summary output")
dbutils.widgets.text("query_geoids", "", "Optional explicit tract GEOIDs")
dbutils.widgets.text("query_state_fips", "04,26,42", "Fallback query states")
dbutils.widgets.text("queries_per_state", "2", "Fallback queries per state")
dbutils.widgets.text("top_k", "10", "Neighbors per representation")
dbutils.widgets.text("pca_components", "6", "PCA component count")
dbutils.widgets.text(
    "mlflow_experiment",
    "/Shared/neighborhood-digital-twin/similarity-baselines",
    "MLflow experiment",
)

catalog = dbutils.widgets.get("catalog").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
candidate_table = dbutils.widgets.get("candidate_table").strip()
match_table = dbutils.widgets.get("match_table").strip()
summary_table = dbutils.widgets.get("summary_table").strip()
query_geoids = parse_geoid_list(dbutils.widgets.get("query_geoids"))
query_state_fips = tuple(
    item.strip() for item in dbutils.widgets.get("query_state_fips").split(",") if item.strip()
)
queries_per_state = int(dbutils.widgets.get("queries_per_state"))
top_k = int(dbutils.widgets.get("top_k"))
pca_components = int(dbutils.widgets.get("pca_components"))
experiment_path = dbutils.widgets.get("mlflow_experiment").strip()

candidates = spark.table(qualified_name(catalog, gold_schema, candidate_table))

# COMMAND ----------

mlflow.set_experiment(experiment_path)
with mlflow.start_run(run_name="current-similarity-baselines") as active_run:
    mlflow.log_params(
        {
            "feature_count": len(SIMILARITY_FEATURE_COLUMNS),
            "features": ",".join(SIMILARITY_FEATURE_COLUMNS),
            "query_mode": "explicit" if query_geoids else "deterministic_state_sample",
            "query_state_fips": ",".join(query_state_fips),
            "queries_per_state": queries_per_state,
            "top_k": top_k,
            "pca_components": pca_components,
        }
    )
    result = build_similarity_baseline_run(
        candidates,
        query_geoids=query_geoids,
        query_state_fips=query_state_fips,
        queries_per_state=queries_per_state,
        top_k=top_k,
        pca_components=pca_components,
        run_id=active_run.info.run_id,
    )
    for row in result.summary.collect():
        representation = str(row["representation_name"])
        mlflow.log_metric(
            f"{representation}_cross_state_match_share",
            float(row["cross_state_match_share"]),
        )
        mlflow.log_metric(
            f"{representation}_median_distance",
            float(row["median_similarity_distance"]),
        )
    summary_row = result.summary.first()
    mlflow.log_metric("pca_explained_variance", float(summary_row["pca_explained_variance"]))
    mlflow.log_metric(
        "mean_raw_pca_top_k_overlap",
        float(summary_row["mean_raw_pca_top_k_overlap"]),
    )

# COMMAND ----------

match_name = qualified_name(catalog, gold_schema, match_table)
summary_name = qualified_name(catalog, gold_schema, summary_table)
(
    result.matches.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(match_name)
)
(
    result.summary.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(summary_name)
)

expected_matches = result.matches.select("query_geoid_2020").distinct().count() * top_k * 2
if spark.table(match_name).count() != expected_matches:
    raise RuntimeError("Published match count does not reconcile to queries, top-k, and methods")
if spark.table(match_name).where("query_geoid_2020 = match_geoid_2020").limit(1).count():
    raise RuntimeError("Published similarity output contains a self-match")

display(spark.table(summary_name).orderBy("representation_name"))
display(spark.table(match_name).orderBy("query_geoid_2020", "representation_name", "match_rank"))
print(f"Published current-state matches to {match_name}.")
print(f"Published representation summary to {summary_name}.")
print(f"MLflow run: {result.run_id}")

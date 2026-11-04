# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Historical analogue baseline
# MAGIC
# MAGIC This development workflow retrieves earlier tract-year states whose later outcomes were
# MAGIC already observable at each validation query date. It compares median and inverse-distance
# MAGIC analogue estimates with zero-change, state-trend, and regularized-linear forecasts on the
# MAGIC same sampled queries. It does not access locked temporal test queries or publish an
# MAGIC application-serving product.

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


def _parse_int_tuple(value: str, *, label: str) -> tuple[int, ...]:
    """Parse a nonempty comma-separated integer widget value."""

    parsed = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not parsed:
        raise ValueError(f"{label} must contain at least one integer")
    return parsed


def _parse_text_tuple(value: str, *, label: str) -> tuple[str, ...]:
    """Parse a nonempty comma-separated text widget value."""

    parsed = tuple(item.strip() for item in value.split(",") if item.strip())
    if not parsed:
        raise ValueError(f"{label} must contain at least one value")
    return parsed


_add_repository_source()

# COMMAND ----------

import mlflow
from databricks.sdk import WorkspaceClient
from pyspark.sql import functions

from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.historical_analogues import (
    ANALOGUE_FEATURE_COLUMNS,
    ANALOGUE_FEATURE_FAMILIES,
    DEFAULT_COMPARATOR_MODELS,
    DEFAULT_HORIZONS,
    DEFAULT_PCA_COMPONENTS,
    HISTORICAL_ANALOGUE_MATCH_TABLE,
    HISTORICAL_ANALOGUE_PREDICTION_TABLE,
    HISTORICAL_ANALOGUE_SCORECARD_TABLE,
    HISTORICAL_ANALOGUE_SUMMARY_TABLE,
    build_historical_analogue_run,
)

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("model_schema", "neighborhood_twin_model", "Model-output schema")
dbutils.widgets.text(
    "evaluation_schema", "neighborhood_twin_evaluation", "Model-evaluation schema"
)
dbutils.widgets.text("modeling_panel_table", "gold_modeling_panel", "Modeling panel")
dbutils.widgets.text(
    "forecast_prediction_table", "forecast_baseline_prediction", "Forecast comparators"
)
dbutils.widgets.text("match_table", HISTORICAL_ANALOGUE_MATCH_TABLE, "Match output")
dbutils.widgets.text(
    "analogue_prediction_table", HISTORICAL_ANALOGUE_PREDICTION_TABLE, "Prediction output"
)
dbutils.widgets.text("summary_table", HISTORICAL_ANALOGUE_SUMMARY_TABLE, "Summary output")
dbutils.widgets.text("scorecard_table", HISTORICAL_ANALOGUE_SCORECARD_TABLE, "Scorecard output")
dbutils.widgets.text(
    "horizons", ",".join(str(value) for value in DEFAULT_HORIZONS), "Evaluated horizons"
)
dbutils.widgets.text("queries_per_group", "1", "Queries per origin, region, and geographic role")
dbutils.widgets.text("top_k", "10", "Historical matches per representation")
dbutils.widgets.text("pca_components", str(DEFAULT_PCA_COMPONENTS), "PCA component count")
dbutils.widgets.text(
    "comparator_models",
    ",".join(DEFAULT_COMPARATOR_MODELS),
    "Forecast methods compared on the same queries",
)
dbutils.widgets.text(
    "mlflow_experiment",
    "/Shared/neighborhood-digital-twin/historical-analogues",
    "MLflow experiment",
)

catalog = dbutils.widgets.get("catalog").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
model_schema = dbutils.widgets.get("model_schema").strip()
evaluation_schema = dbutils.widgets.get("evaluation_schema").strip()
modeling_panel_table = dbutils.widgets.get("modeling_panel_table").strip()
forecast_prediction_table = dbutils.widgets.get("forecast_prediction_table").strip()
match_table = dbutils.widgets.get("match_table").strip()
analogue_prediction_table = dbutils.widgets.get("analogue_prediction_table").strip()
summary_table = dbutils.widgets.get("summary_table").strip()
scorecard_table = dbutils.widgets.get("scorecard_table").strip()
horizons = _parse_int_tuple(dbutils.widgets.get("horizons"), label="horizons")
queries_per_group = int(dbutils.widgets.get("queries_per_group"))
top_k = int(dbutils.widgets.get("top_k"))
pca_components = int(dbutils.widgets.get("pca_components"))
comparator_models = _parse_text_tuple(
    dbutils.widgets.get("comparator_models"), label="comparator_models"
)
experiment_path = dbutils.widgets.get("mlflow_experiment").strip()

panel = spark.table(qualified_name(catalog, gold_schema, modeling_panel_table))
forecast_predictions = spark.table(
    qualified_name(catalog, model_schema, forecast_prediction_table)
)

# COMMAND ----------


def ensure_experiment_parent(experiment: str) -> None:
    """Create the shared Workspace folder required by a nested MLflow experiment path."""

    if not experiment.startswith("/"):
        raise ValueError("The Databricks MLflow experiment path must be absolute")
    WorkspaceClient().workspace.mkdirs(str(PurePosixPath(experiment).parent))


ensure_experiment_parent(experiment_path)
mlflow.set_experiment(experiment_path)
with mlflow.start_run(run_name="time-safe-historical-analogue-baseline") as active_run:
    mlflow.log_params(
        {
            "evaluation_role": "validation",
            "locked_test_access": "prohibited",
            "horizons": ",".join(str(value) for value in horizons),
            "queries_per_group": queries_per_group,
            "top_k": top_k,
            "pca_components": pca_components,
            "comparator_models": ",".join(comparator_models),
            "feature_count": len(ANALOGUE_FEATURE_COLUMNS),
            "features": ",".join(ANALOGUE_FEATURE_COLUMNS),
            "feature_families": ",".join(ANALOGUE_FEATURE_FAMILIES),
            "candidate_time_rule": "candidate_target_end_year<=query_origin_year",
            "candidate_geography_rule": "geographic_development_only",
            "same_tract_exclusion": "true",
        }
    )
    result = build_historical_analogue_run(
        panel,
        forecast_predictions,
        horizons=horizons,
        queries_per_group=queries_per_group,
        top_k=top_k,
        pca_components=pca_components,
        comparator_models=comparator_models,
        run_id=active_run.info.run_id,
    )
    for row in result.summary.collect():
        stem = f"{row['representation_name']}_h{row['horizon_years']}"
        mlflow.log_metric(
            f"{stem}_median_distance", float(row["median_similarity_distance"])
        )
        mlflow.log_metric(
            f"{stem}_cross_state_share", float(row["cross_state_match_share"])
        )
        mlflow.log_metric(
            f"{stem}_same_county_share", float(row["same_county_match_share"])
        )
        mlflow.log_metric(
            f"{stem}_mean_candidate_age_years", float(row["mean_candidate_age_years"])
        )
        mlflow.log_metric(
            f"{stem}_pca_explained_variance", float(row["pca_explained_variance"])
        )
        mlflow.log_metric(
            f"{stem}_raw_pca_overlap_share",
            float(row["mean_raw_pca_top_k_overlap_share"]),
        )
    overall_rows = result.scorecard.where("slice_name = 'overall'").collect()
    for row in overall_rows:
        stem = f"{row['prediction_method']}_h{row['horizon_years']}"
        mlflow.log_metric(f"{stem}_mae", float(row["mae_log_change"]))
        mlflow.log_metric(f"{stem}_rmse", float(row["rmse_log_change"]))
        mlflow.log_metric(f"{stem}_mean_error", float(row["mean_error_log_change"]))
        if row["mae_skill_vs_zero_change"] is not None:
            mlflow.log_metric(
                f"{stem}_mae_skill_vs_zero",
                float(row["mae_skill_vs_zero_change"]),
            )

# COMMAND ----------

match_name = qualified_name(catalog, model_schema, match_table)
prediction_name = qualified_name(catalog, model_schema, analogue_prediction_table)
summary_name = qualified_name(catalog, evaluation_schema, summary_table)
scorecard_name = qualified_name(catalog, evaluation_schema, scorecard_table)

outputs = (
    (result.matches, match_name),
    (result.predictions, prediction_name),
    (result.summary, summary_name),
    (result.scorecard, scorecard_name),
)
for frame, table_name in outputs:
    (
        frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table_name)
    )

# COMMAND ----------

published_matches = spark.table(match_name)
published_predictions = spark.table(prediction_name)
published_summary = spark.table(summary_name)
published_scorecard = spark.table(scorecard_name)

if published_matches.where("query_temporal_role <> 'validation'").limit(1).count():
    raise RuntimeError("Historical analogue matches contain a non-validation query")
if published_predictions.where("query_temporal_role <> 'validation'").limit(1).count():
    raise RuntimeError("Historical analogue predictions contain a non-validation query")
if published_matches.where(
    "candidate_target_end_year > query_origin_year"
).limit(1).count():
    raise RuntimeError("Historical analogue matches violate the outcome-known-by-query rule")
if published_matches.where(
    "candidate_geoid_2020 = query_geoid_2020"
).limit(1).count():
    raise RuntimeError("Historical analogue matches contain a same-tract result")

match_reconciliation = (
    published_matches.groupBy(
        "query_geoid_2020",
        "query_origin_year",
        "horizon_years",
        "representation_name",
    )
    .count()
    .where(functions.col("count") != top_k)
)
if match_reconciliation.limit(1).count():
    raise RuntimeError("At least one query and representation did not publish top-k matches")

expected_prediction_methods = 4 + len(comparator_models)
method_reconciliation = (
    published_predictions.groupBy(
        "query_geoid_2020", "query_origin_year", "horizon_years"
    )
    .agg(functions.countDistinct("prediction_method").alias("method_count"))
    .where(functions.col("method_count") != expected_prediction_methods)
)
if method_reconciliation.limit(1).count():
    raise RuntimeError("Prediction methods do not reconcile on the sampled query set")
if published_summary.where("query_count <= 0 OR match_count <= 0").limit(1).count():
    raise RuntimeError("Historical analogue summary contains an empty evaluation group")
if published_scorecard.where("query_count <= 0").limit(1).count():
    raise RuntimeError("Historical analogue scorecard contains an empty evaluation slice")

display(
    published_scorecard.where("slice_name = 'overall'").orderBy(
        "horizon_years", "mae_log_change"
    )
)
display(published_summary.orderBy("horizon_years", "representation_name"))
display(
    published_matches.orderBy(
        "horizon_years",
        "query_origin_year",
        "query_geoid_2020",
        "representation_name",
        "match_rank",
    )
)
print(f"Published historical analogue matches to {match_name}.")
print(f"Published analogue and comparator predictions to {prediction_name}.")
print(f"Published retrieval diagnostics to {summary_name}.")
print(f"Published development scorecards to {scorecard_name}.")
print(f"MLflow run: {result.run_id}")

# Cached feature representations and match frames are intentionally retained until every
# lazy output has been materialized. Spark Connect invalidates downstream plans when a parent
# DataFrame is uncached too early, so cleanup belongs at the end of the workflow.
spark.catalog.clearCache()

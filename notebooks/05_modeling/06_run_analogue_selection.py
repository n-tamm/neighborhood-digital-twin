# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Expanded historical analogue selection
# MAGIC
# MAGIC This workflow expands the validation query sample without opening the locked temporal
# MAGIC tests. It compares weighted-standardized and PCA retrieval on identical queries, requires
# MAGIC ten distinct physical candidate tracts, and measures how the deterministic sample covers
# MAGIC the full eligible validation population.

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

from neighborhood_twin.analogue_selection import (
    ANALOGUE_SELECTION_COVERAGE_TABLE,
    ANALOGUE_SELECTION_MATCH_TABLE,
    ANALOGUE_SELECTION_PREDICTION_TABLE,
    ANALOGUE_SELECTION_SCORECARD_TABLE,
    ANALOGUE_SELECTION_SUMMARY_TABLE,
    DEFAULT_SELECTION_QUERIES_PER_GROUP,
    REQUIRED_SELECTION_COVERAGE_COLUMNS,
    build_analogue_selection_run,
    eligible_selection_queries,
    incomplete_sampling_strata,
)
from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.historical_analogues import (
    DEFAULT_COMPARATOR_MODELS,
    DEFAULT_HORIZONS,
    DEFAULT_PCA_COMPONENTS,
)

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("model_schema", "neighborhood_twin_model", "Model-output schema")
dbutils.widgets.text(
    "evaluation_schema", "neighborhood_twin_evaluation", "Model-evaluation schema"
)
dbutils.widgets.text("modeling_panel_table", "gold_modeling_panel", "Modeling panel")
dbutils.widgets.text(
    "forecast_prediction_table", "forecast_baseline_prediction", "Forecast predictions"
)
dbutils.widgets.text("match_table", ANALOGUE_SELECTION_MATCH_TABLE, "Expanded matches")
dbutils.widgets.text(
    "analogue_prediction_table",
    ANALOGUE_SELECTION_PREDICTION_TABLE,
    "Expanded predictions",
)
dbutils.widgets.text("summary_table", ANALOGUE_SELECTION_SUMMARY_TABLE, "Retrieval summary")
dbutils.widgets.text("scorecard_table", ANALOGUE_SELECTION_SCORECARD_TABLE, "Scorecard")
dbutils.widgets.text("coverage_table", ANALOGUE_SELECTION_COVERAGE_TABLE, "Query coverage")
dbutils.widgets.text(
    "horizons", ",".join(str(value) for value in DEFAULT_HORIZONS), "Evaluated horizons"
)
dbutils.widgets.text(
    "queries_per_group",
    str(DEFAULT_SELECTION_QUERIES_PER_GROUP),
    "Queries per origin, region, and geographic role",
)
dbutils.widgets.text("top_k", "10", "Distinct historical communities per representation")
dbutils.widgets.text("pca_components", str(DEFAULT_PCA_COMPONENTS), "PCA component count")
dbutils.widgets.text(
    "comparator_models",
    ",".join(DEFAULT_COMPARATOR_MODELS),
    "Forecast comparators",
)
dbutils.widgets.text(
    "mlflow_experiment",
    "/Shared/neighborhood-digital-twin/analogue-selection",
    "MLflow experiment",
)


def _parse_int_tuple(value: str, *, label: str) -> tuple[int, ...]:
    """Parse a required comma-separated integer widget."""

    parsed = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not parsed:
        raise ValueError(f"{label} must contain at least one integer")
    return parsed


def _parse_text_tuple(value: str, *, label: str) -> tuple[str, ...]:
    """Parse a required comma-separated text widget."""

    parsed = tuple(item.strip() for item in value.split(",") if item.strip())
    if not parsed:
        raise ValueError(f"{label} must contain at least one value")
    return parsed


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
coverage_table = dbutils.widgets.get("coverage_table").strip()
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


def selected_query_dimensions(result_predictions, eligible_queries):
    """Return governed dimensions for the exact queries selected by the run."""

    selected_keys = result_predictions.selectExpr(
        "query_geoid_2020 AS geoid_2020",
        "query_origin_year AS forecast_origin_year",
        "horizon_years",
    ).distinct()
    return eligible_queries.join(
        selected_keys,
        ["geoid_2020", "forecast_origin_year", "horizon_years"],
        "inner",
    )


def validate_outputs(result, eligible_queries, selected_queries) -> None:
    """Stop publication when expanded evaluation violates timing or coverage contracts."""

    matches = result.matches
    predictions = result.predictions
    coverage = result.coverage

    if matches.where("query_temporal_role <> 'validation'").limit(1).count():
        raise RuntimeError("Expanded analogue matches contain a non-validation query")
    if predictions.where("query_temporal_role <> 'validation'").limit(1).count():
        raise RuntimeError("Expanded predictions contain a non-validation query")
    if matches.where("candidate_target_end_year > query_origin_year").limit(1).count():
        raise RuntimeError("Expanded matches use a candidate outcome unavailable at query time")
    if matches.where("candidate_geoid_2020 = query_geoid_2020").limit(1).count():
        raise RuntimeError("Expanded matches contain a same-tract result")
    if matches.where("NOT unique_candidate_tract").limit(1).count():
        raise RuntimeError("Expanded matches do not record the required distinct-tract policy")

    match_groups = matches.groupBy(
        "query_geoid_2020",
        "query_origin_year",
        "horizon_years",
        "representation_name",
    ).agg(
        functions.count(functions.lit(1)).alias("match_count"),
        functions.countDistinct("candidate_geoid_2020").alias("candidate_tract_count"),
    )
    if match_groups.where(
        (functions.col("match_count") != top_k)
        | (functions.col("candidate_tract_count") != top_k)
    ).limit(1).count():
        raise RuntimeError("A query and representation lacks ten distinct physical candidates")
    if matches.select("representation_name").distinct().count() != 2:
        raise RuntimeError("Expanded evaluation must publish weighted and PCA representations")

    expected_prediction_methods = 4 + len(comparator_models)
    prediction_groups = predictions.groupBy(
        "query_geoid_2020", "query_origin_year", "horizon_years"
    ).agg(functions.countDistinct("prediction_method").alias("method_count"))
    if prediction_groups.where(
        functions.col("method_count") != expected_prediction_methods
    ).limit(1).count():
        raise RuntimeError("Expanded queries do not share the complete prediction-method set")

    if incomplete_sampling_strata(
        eligible_queries,
        selected_queries,
        queries_per_group=queries_per_group,
    ).limit(1).count():
        raise RuntimeError("Expanded query selection did not fill every available sampling stratum")
    if selected_queries.select("geoid_2020").distinct().count() <= 16:
        raise RuntimeError("Expanded selection did not materially exceed the baseline query sample")
    if coverage.where(
        functions.col("eligible_query_share").isNull()
        | functions.col("selected_query_share").isNull()
    ).limit(1).count():
        raise RuntimeError("Expanded query coverage contains an undefined distribution share")
    required_dimensions = [
        column.removeprefix("query_") for column in REQUIRED_SELECTION_COVERAGE_COLUMNS
    ]
    if coverage.where(
        functions.col("dimension_name").isin(*required_dimensions)
        & (functions.col("coverage_status") != "covered")
    ).limit(1).count():
        raise RuntimeError("A required housing, size, or uncertainty group lacks a query")
    if coverage.select("analogue_selection_run_id").distinct().count() != 1:
        raise RuntimeError("Expanded coverage contains more than one selection run")


eligible_queries = eligible_selection_queries(
    panel,
    forecast_predictions,
    horizons=horizons,
    comparator_models=comparator_models,
).cache()
eligible_queries.count()

ensure_experiment_parent(experiment_path)
mlflow.set_experiment(experiment_path)
with mlflow.start_run(run_name="expanded-historical-analogue-selection") as active_run:
    mlflow.log_params(
        {
            "evaluation_role": "validation",
            "locked_test_access": "prohibited",
            "horizons": ",".join(str(value) for value in horizons),
            "queries_per_group": queries_per_group,
            "sampling_strata": "origin_year,census_region,geographic_role",
            "required_coverage_supplements": ",".join(
                REQUIRED_SELECTION_COVERAGE_COLUMNS
            ),
            "top_k": top_k,
            "pca_components": pca_components,
            "comparator_models": ",".join(comparator_models),
            "candidate_time_rule": "candidate_target_end_year<=query_origin_year",
            "candidate_geography_rule": "geographic_development_only",
            "same_tract_exclusion": "true",
            "distinct_physical_candidate_tracts": "true",
        }
    )
    result = build_analogue_selection_run(
        panel,
        forecast_predictions,
        horizons=horizons,
        queries_per_group=queries_per_group,
        top_k=top_k,
        pca_components=pca_components,
        comparator_models=comparator_models,
        run_id=active_run.info.run_id,
    )
    result.matches.cache().count()
    result.predictions.cache().count()
    result.summary.cache().count()
    result.scorecard.cache().count()
    result.coverage.cache().count()
    selected_queries = selected_query_dimensions(result.predictions, eligible_queries).cache()
    selected_queries.count()
    validate_outputs(result, eligible_queries, selected_queries)

    for row in (
        selected_queries.groupBy("horizon_years")
        .agg(functions.count(functions.lit(1)).alias("query_count"))
        .collect()
    ):
        mlflow.log_metric(
            f"h{row['horizon_years']}_selected_query_count",
            float(row["query_count"]),
        )
    max_share_gap = result.coverage.agg(
        functions.max(functions.abs("selected_minus_eligible_share"))
    ).first()[0]
    mlflow.log_metric("maximum_absolute_coverage_share_gap", float(max_share_gap))
    for row in result.scorecard.where("slice_name = 'overall'").collect():
        stem = f"{row['prediction_method']}_h{row['horizon_years']}"
        mlflow.log_metric(f"{stem}_mae", float(row["mae_log_change"]))
        mlflow.log_metric(f"{stem}_rmse", float(row["rmse_log_change"]))

# COMMAND ----------

match_name = qualified_name(catalog, model_schema, match_table)
prediction_name = qualified_name(catalog, model_schema, analogue_prediction_table)
summary_name = qualified_name(catalog, evaluation_schema, summary_table)
scorecard_name = qualified_name(catalog, evaluation_schema, scorecard_table)
coverage_name = qualified_name(catalog, evaluation_schema, coverage_table)

outputs = (
    (result.matches, match_name),
    (result.predictions, prediction_name),
    (result.summary, summary_name),
    (result.scorecard, scorecard_name),
    (result.coverage, coverage_name),
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
published_coverage = spark.table(coverage_name)

for table_name, frame in (
    (match_name, published_matches),
    (prediction_name, published_predictions),
    (summary_name, published_summary),
    (scorecard_name, published_scorecard),
    (coverage_name, published_coverage),
):
    if frame.select("analogue_selection_run_id").distinct().count() != 1:
        raise RuntimeError(f"Published table contains more than one selection run: {table_name}")

display(
    published_scorecard.where("slice_name = 'overall'").orderBy(
        "horizon_years", "mae_log_change"
    )
)
display(
    published_coverage.where("dimension_name <> 'sampling_stratum'").orderBy(
        "horizon_years", "dimension_name", "dimension_value"
    )
)
display(published_summary.orderBy("horizon_years", "representation_name"))
print(f"Published expanded historical matches to {match_name}.")
print(f"Published expanded predictions to {prediction_name}.")
print(f"Published retrieval diagnostics to {summary_name}.")
print(f"Published expanded scorecards to {scorecard_name}.")
print(f"Published query coverage to {coverage_name}.")
print(f"MLflow run: {result.run_id}")

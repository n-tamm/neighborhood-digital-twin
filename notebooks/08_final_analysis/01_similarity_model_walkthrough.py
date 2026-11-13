# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Historical analogue similarity: sequential walkthrough
# MAGIC
# MAGIC **Purpose:** explain the implemented similarity system from question to application output.
# MAGIC This notebook reads governed model, evaluation, and serving tables. It does not fit a model,
# MAGIC choose new weights, retrieve new neighbors, or open the locked temporal tests.
# MAGIC
# MAGIC **Speaking callout:** Start with the distinction between *a forecast* and *an analogue*.
# MAGIC The forecast produces the primary numerical estimate. The analogue system finds earlier
# MAGIC communities that looked similar and shows what happened afterward as historical context.

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

from IPython.display import Image
from IPython.display import display as display_ipython
from pyspark.sql import functions

from neighborhood_twin.analogue_serving_enrichment import (
    ANALOGUE_FAMILY_DISPLAY_NAMES,
    ANALOGUE_FEATURE_DISPLAY_NAMES,
)
from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.historical_analogues import ANALOGUE_FEATURE_FAMILIES
from neighborhood_twin.similarity_visuals import (
    DEFAULT_CASE_HORIZON_YEARS,
    DEFAULT_CASE_QUERY_GEOID,
    SIMILARITY_FIGURE_COUNT,
)

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("evaluation_schema", "neighborhood_twin_evaluation", "Evaluation schema")
dbutils.widgets.text("serving_schema", "neighborhood_twin_serving", "Serving schema")
dbutils.widgets.text(
    "figure_manifest_table",
    "similarity_evaluation_figure_manifest",
    "Similarity figure manifest",
)
dbutils.widgets.text("release_manifest_table", "serving_release_manifest", "Serving manifest")
dbutils.widgets.text("availability_table", "serving_analogue_availability_current", "Availability")
dbutils.widgets.text("match_table", "serving_analogue_match_current", "Current matches")
dbutils.widgets.text(
    "explanation_table", "serving_analogue_explanation_current", "Match explanations"
)
dbutils.widgets.text(
    "trajectory_table", "serving_analogue_trajectory_current", "Observed trajectories"
)
dbutils.widgets.text(
    "stability_table", "historical_analogue_stability_summary", "Stability evidence"
)
dbutils.widgets.text(
    "scorecard_table", "historical_analogue_selection_scorecard", "Selection scorecard"
)
dbutils.widgets.text("tree_scale_table", "analogue_tree_scale_benchmark", "Tree scale evidence")
dbutils.widgets.text("case_query_geoid", DEFAULT_CASE_QUERY_GEOID, "Case-study query GEOID")
dbutils.widgets.text(
    "case_horizon_years", str(DEFAULT_CASE_HORIZON_YEARS), "Case-study horizon"
)

catalog = dbutils.widgets.get("catalog").strip()
evaluation_schema = dbutils.widgets.get("evaluation_schema").strip()
serving_schema = dbutils.widgets.get("serving_schema").strip()
figure_manifest_table = dbutils.widgets.get("figure_manifest_table").strip()
release_manifest_table = dbutils.widgets.get("release_manifest_table").strip()
availability_table = dbutils.widgets.get("availability_table").strip()
match_table = dbutils.widgets.get("match_table").strip()
explanation_table = dbutils.widgets.get("explanation_table").strip()
trajectory_table = dbutils.widgets.get("trajectory_table").strip()
stability_table = dbutils.widgets.get("stability_table").strip()
scorecard_table = dbutils.widgets.get("scorecard_table").strip()
tree_scale_table = dbutils.widgets.get("tree_scale_table").strip()
case_query_geoid = dbutils.widgets.get("case_query_geoid").strip()
case_horizon_years = int(dbutils.widgets.get("case_horizon_years"))

figure_manifest = spark.table(
    qualified_name(catalog, evaluation_schema, figure_manifest_table)
)
release_manifest = spark.table(
    qualified_name(catalog, serving_schema, release_manifest_table)
)
latest_figure_build = (
    figure_manifest.orderBy(functions.col("similarity_figure_built_at_utc").desc())
    .select("similarity_figure_build_id")
    .first()
)
if latest_figure_build is None:
    raise RuntimeError("Run job 800 before using the walkthrough")
figure_build_id = str(latest_figure_build["similarity_figure_build_id"])
figures = figure_manifest.where(
    functions.col("similarity_figure_build_id") == figure_build_id
)
if figures.count() != SIMILARITY_FIGURE_COUNT:
    raise RuntimeError("The current similarity figure build is incomplete")
serving_release_ids = [
    str(row["source_serving_release_id"])
    for row in figures.select("source_serving_release_id").distinct().collect()
]
if len(serving_release_ids) != 1:
    raise RuntimeError("The figure build does not reference exactly one serving release")
serving_release_id = serving_release_ids[0]


def show_figure(sequence: int) -> None:
    """Display one reviewed PNG from the current governed similarity build."""

    row = figures.where(functions.col("figure_sequence") == sequence).select(
        "figure_path", "figure_title"
    ).first()
    if row is None:
        raise RuntimeError(f"Similarity figure {sequence} is unavailable")
    print(str(row["figure_title"]))
    display_ipython(Image(filename=str(row["figure_path"])))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. What was published?
# MAGIC
# MAGIC The serving manifest is the activation record. A valid schema-1.1 release contains five
# MAGIC rows: matches, summaries, availability, deterministic explanations, and annual historical
# MAGIC paths. The application should read all of them from the same release ID.
# MAGIC
# MAGIC **Speaking callout:** The tables below are not five separate analyses. They are five views
# MAGIC of one validated national release.

# COMMAND ----------

display(
    release_manifest.where(functions.col("serving_release_id") == serving_release_id)
    .select(
        "table_name",
        "row_count",
        "serving_as_of_year",
        "horizons_csv",
        "retrieval_method",
        "release_status",
    )
    .orderBy("table_name")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. What does “similar” mean?
# MAGIC
# MAGIC Twelve features are organized into five families. Imputation and standardization are fit
# MAGIC only on point-model training rows. Each family receives equal total influence before exact
# MAGIC Euclidean distance is calculated, preventing a family with more columns from dominating
# MAGIC simply because it has more columns.
# MAGIC
# MAGIC **Speaking callout:** Similarity is conditional on this declared representation. It is not
# MAGIC a universal statement that two neighborhoods are alike in every lived-experience dimension.

# COMMAND ----------

family_rows = []
for family, features in ANALOGUE_FEATURE_FAMILIES.items():
    for feature in features:
        family_rows.append(
            (
                ANALOGUE_FAMILY_DISPLAY_NAMES[family],
                ANALOGUE_FEATURE_DISPLAY_NAMES[feature],
            )
        )
display(spark.createDataFrame(family_rows, "feature_family string, feature string"))

# COMMAND ----------

show_figure(1)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. How are future information and duplicate communities avoided?
# MAGIC
# MAGIC For a historical query year, candidates must come from an earlier tract-year state and
# MAGIC their later FHFA outcome must already be knowable at that query date. Locked temporal-test
# MAGIC candidates and the query tract itself are excluded. Retrieval then keeps ten distinct
# MAGIC physical tracts, so the result cannot fill the list with several years from one community.
# MAGIC
# MAGIC These rules were evaluated retrospectively before the method was applied to 2025 queries.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Is the match list stable, and why is weighted matching the default?
# MAGIC
# MAGIC Small 20% family-weight adjustments retain most of the original top ten. Full family
# MAGIC removals are much more disruptive, especially when recent market trajectory is removed.
# MAGIC Weighted matching also has lower expanded-validation error than PCA at one and three years.
# MAGIC PCA remains an audit lens rather than a second application mode.
# MAGIC
# MAGIC **Speaking callout:** Stability means the list is not arbitrary under a minor change. It
# MAGIC does not mean there is one objectively correct set of historical matches.

# COMMAND ----------

stability = spark.table(qualified_name(catalog, evaluation_schema, stability_table))
display(
    stability.where(
        functions.col("perturbation_kind").isin(
            "small_weight_change",
            "candidate_uniqueness",
            "pca_component_count",
            "family_ablation",
        )
    )
    .groupBy("perturbation_kind")
    .agg(
        functions.avg("top_k_overlap_share").alias("mean_top_ten_retention"),
        functions.expr("percentile_approx(top_k_overlap_share, 0.5)").alias(
            "median_top_ten_retention"
        ),
        functions.min("top_k_overlap_share").alias("minimum_top_ten_retention"),
        functions.count(functions.lit(1)).alias("query_variant_count"),
    )
    .orderBy(functions.col("mean_top_ten_retention").desc())
)

# COMMAND ----------

show_figure(2)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Do historical outcomes improve the primary forecast?
# MAGIC
# MAGIC In the expanded validation sample, the analogue estimates beat a zero-change reference but
# MAGIC do not beat the state-trend or regularized-linear forecast. That result sets the product
# MAGIC boundary: analogues provide understandable historical evidence and a secondary comparison;
# MAGIC they do not replace the primary forecast.

# COMMAND ----------

scorecard = spark.table(qualified_name(catalog, evaluation_schema, scorecard_table))
display(
    scorecard.where(
        (functions.col("slice_name") == "overall")
        & functions.col("prediction_method").isin(
            "zero_change",
            "state_current_trend",
            "regularized_linear",
            "analogue_median_weighted_standardized",
            "analogue_inverse_distance_weighted_standardized",
        )
    )
    .select(
        "horizon_years",
        "prediction_method",
        "query_count",
        "mae_log_change",
        "rmse_log_change",
        "mean_error_log_change",
    )
    .orderBy("horizon_years", "mae_log_change")
)

# COMMAND ----------

show_figure(3)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Where can the current system return a result?
# MAGIC
# MAGIC Availability is narrower than current ACS profile coverage because the chosen
# MAGIC representation needs usable market history and a complete model-ready current state.
# MAGIC Unsupported tracts remain in the availability table with a reason; they are not silently
# MAGIC removed or matched with a different method.

# COMMAND ----------

availability = spark.table(qualified_name(catalog, serving_schema, availability_table)).where(
    functions.col("serving_release_id") == serving_release_id
)
display(
    availability.groupBy("horizon_years", "availability_reason")
    .agg(functions.count(functions.lit(1)).alias("tract_count"))
    .orderBy("horizon_years", functions.col("tract_count").desc())
)

# COMMAND ----------

show_figure(4)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Can exact retrieval serve the national population?
# MAGIC
# MAGIC The exhaustive cross join was useful as an evaluation reference but too expensive for
# MAGIC application publication. The approved exact KD-tree reproduces every tested reference rank
# MAGIC and directly queries all 46,719 eligible current tracts. Job 700 uses it in a batch release;
# MAGIC the application never rebuilds the index during a user request.

# COMMAND ----------

tree_scale = spark.table(qualified_name(catalog, evaluation_schema, tree_scale_table))
display(
    tree_scale.where(functions.col("sample_name") == "all_current_eligible")
    .select(
        "horizon_years",
        "query_count",
        "candidate_state_count",
        "query_elapsed_seconds",
        "queries_per_second",
        "distance_computation_ratio",
        "expanded_query_share",
    )
    .orderBy("horizon_years")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. What does one application result look like?
# MAGIC
# MAGIC The default example is Oakland County, Michigan, tract `26125144200`. It was selected by a
# MAGIC declared communication rule: ten three-year matches, ten represented states, complete
# MAGIC annual paths, and no imputed query feature. It is a clear demonstration case, not evidence
# MAGIC that every tract will have the same quality or geographic diversity.
# MAGIC
# MAGIC **Speaking callout:** On the map, the numbers are match ranks. The feature gaps explain why
# MAGIC the closest result is close under the model. The lower panel shows observed historical FHFA
# MAGIC paths after each candidate year—not forecasts for Oakland County.

# COMMAND ----------

matches = spark.table(qualified_name(catalog, serving_schema, match_table)).where(
    (functions.col("serving_release_id") == serving_release_id)
    & (functions.col("query_geoid_2020") == case_query_geoid)
    & (functions.col("horizon_years") == case_horizon_years)
)
explanations = spark.table(
    qualified_name(catalog, serving_schema, explanation_table)
).where(
    (functions.col("serving_release_id") == serving_release_id)
    & (functions.col("query_geoid_2020") == case_query_geoid)
    & (functions.col("horizon_years") == case_horizon_years)
)
display(
    matches.join(
        explanations.select(
            "query_geoid_2020",
            "query_origin_year",
            "horizon_years",
            "candidate_geoid_2020",
            "candidate_origin_year",
            "match_rank",
            "strongest_shared_family_display_name",
            "largest_difference_family_display_name",
        ),
        [
            "query_geoid_2020",
            "query_origin_year",
            "horizon_years",
            "candidate_geoid_2020",
            "candidate_origin_year",
            "match_rank",
        ],
    )
    .select(
        "match_rank",
        "candidate_state_abbreviation",
        "candidate_county_name",
        "candidate_tract_name",
        "candidate_origin_year",
        "similarity_distance",
        "strongest_shared_family_display_name",
        "largest_difference_family_display_name",
        "candidate_target_cumulative_log_change",
    )
    .orderBy("match_rank")
)

# COMMAND ----------

show_figure(5)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Interpretation limits to leave on screen
# MAGIC
# MAGIC - FHFA describes a filtered single-family housing market, not every property or household.
# MAGIC - ACS releases are overlapping five-year estimates rather than independent annual surveys.
# MAGIC - A small distance means close under twelve declared features, not identical lived
# MAGIC   experience.
# MAGIC - Historical outcomes are descriptive evidence, not causal effects or calibrated intervals.
# MAGIC - Current analogues are available for 46,719 model-ready tracts, not every U.S. tract.
# MAGIC - The selected example has complete paths; the application must show gaps for other matches.
# MAGIC
# MAGIC **Closing callout:** The similarity system is useful because it turns an abstract current
# MAGIC state into concrete earlier comparisons. Its value is interpretation and context. The
# MAGIC forecast remains the primary numerical prediction.

# Databricks notebook source
# AI Assistance:
# OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
# and code methodological brainstorming. All final modeling, implementation,
# validation, commentary, and interpretation were performed and verified by the authors.
# Model used: GPT-5
# ruff: noqa: E402, F821

# COMMAND ----------

# MAGIC %md
# MAGIC # Historical analogue case review and stability
# MAGIC
# MAGIC This evaluation workflow checks the published job-502 matches before it changes any
# MAGIC modeling choice. It builds deterministic review cases, reruns the two baseline
# MAGIC representations, and measures how the top ten changes under bounded feature-family,
# MAGIC PCA, and candidate-uniqueness variants. Results remain development-only and do not access
# MAGIC the locked temporal tests or choose the production representation automatically.

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

from neighborhood_twin.analogue_audit import (
    ANALOGUE_AUDIT_MATCH_TABLE,
    ANALOGUE_CASE_REVIEW_TABLE,
    ANALOGUE_STABILITY_SUMMARY_TABLE,
    AUDIT_QUERY_KEYS,
    default_audit_variants,
)
from neighborhood_twin.analogue_stability import build_analogue_stability_run
from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.historical_analogues import HISTORICAL_ANALOGUE_MATCH_TABLE

dbutils.widgets.text("catalog", "workspace", "Existing Unity Catalog catalog")
dbutils.widgets.text("gold_schema", "neighborhood_twin_gold", "Gold schema")
dbutils.widgets.text("model_schema", "neighborhood_twin_model", "Model-output schema")
dbutils.widgets.text(
    "evaluation_schema", "neighborhood_twin_evaluation", "Model-evaluation schema"
)
dbutils.widgets.text("modeling_panel_table", "gold_modeling_panel", "Modeling panel")
dbutils.widgets.text(
    "baseline_match_table", HISTORICAL_ANALOGUE_MATCH_TABLE, "Job-502 baseline matches"
)
dbutils.widgets.text("audit_match_table", ANALOGUE_AUDIT_MATCH_TABLE, "Variant matches")
dbutils.widgets.text(
    "stability_summary_table", ANALOGUE_STABILITY_SUMMARY_TABLE, "Stability summary"
)
dbutils.widgets.text("case_review_table", ANALOGUE_CASE_REVIEW_TABLE, "Case review evidence")
dbutils.widgets.text("top_k", "10", "Matches retained per query and variant")
dbutils.widgets.text("shortlist_k", "1000", "Exact baseline candidates retained per query")
dbutils.widgets.text(
    "mlflow_experiment",
    "/Shared/neighborhood-digital-twin/analogue-audit-stability",
    "MLflow experiment",
)

catalog = dbutils.widgets.get("catalog").strip()
gold_schema = dbutils.widgets.get("gold_schema").strip()
model_schema = dbutils.widgets.get("model_schema").strip()
evaluation_schema = dbutils.widgets.get("evaluation_schema").strip()
modeling_panel_table = dbutils.widgets.get("modeling_panel_table").strip()
baseline_match_table = dbutils.widgets.get("baseline_match_table").strip()
audit_match_table = dbutils.widgets.get("audit_match_table").strip()
stability_summary_table = dbutils.widgets.get("stability_summary_table").strip()
case_review_table = dbutils.widgets.get("case_review_table").strip()
top_k = int(dbutils.widgets.get("top_k"))
shortlist_k = int(dbutils.widgets.get("shortlist_k"))
experiment_path = dbutils.widgets.get("mlflow_experiment").strip()

panel = spark.table(qualified_name(catalog, gold_schema, modeling_panel_table))
baseline_matches = spark.table(
    qualified_name(catalog, model_schema, baseline_match_table)
)

# COMMAND ----------


def ensure_experiment_parent(experiment: str) -> None:
    """Create the shared Workspace folder required by a nested MLflow experiment path."""

    if not experiment.startswith("/"):
        raise ValueError("The Databricks MLflow experiment path must be absolute")
    WorkspaceClient().workspace.mkdirs(str(PurePosixPath(experiment).parent))


def baseline_reconciliation(generated_matches):
    """Return source-versus-rerun baseline rows whose match identity or distance differs."""

    source = baseline_matches.select(
        *AUDIT_QUERY_KEYS,
        "representation_name",
        "match_rank",
        functions.col("candidate_geoid_2020").alias("source_candidate_geoid_2020"),
        functions.col("candidate_origin_year").alias("source_candidate_origin_year"),
        functions.col("similarity_distance").alias("source_similarity_distance"),
    )
    generated = generated_matches.where(
        functions.col("perturbation_kind") == "baseline"
    ).select(
        *AUDIT_QUERY_KEYS,
        "representation_name",
        "match_rank",
        functions.col("candidate_geoid_2020").alias("generated_candidate_geoid_2020"),
        functions.col("candidate_origin_year").alias("generated_candidate_origin_year"),
        functions.col("similarity_distance").alias("generated_similarity_distance"),
    )
    keys = [*AUDIT_QUERY_KEYS, "representation_name", "match_rank"]
    return source.join(generated, keys, "full").where(
        functions.col("source_candidate_geoid_2020").isNull()
        | functions.col("generated_candidate_geoid_2020").isNull()
        | (
            functions.col("source_candidate_geoid_2020")
            != functions.col("generated_candidate_geoid_2020")
        )
        | (
            functions.col("source_candidate_origin_year")
            != functions.col("generated_candidate_origin_year")
        )
        | (
            functions.abs(
                functions.col("source_similarity_distance")
                - functions.col("generated_similarity_distance")
            )
            > functions.lit(1e-8)
        )
    )


def validate_outputs(result, *, expected_variant_count: int) -> None:
    """Stop publication when lineage, timing, completeness, or baseline checks fail."""

    audit_matches = result.audit_matches
    stability = result.stability_summary
    case_review = result.case_review

    if baseline_reconciliation(audit_matches).limit(1).count():
        raise RuntimeError("Audit baselines do not reproduce the published job-502 matches")
    if audit_matches.where("query_temporal_role <> 'validation'").limit(1).count():
        raise RuntimeError("Analogue audit opened a non-validation query")
    if audit_matches.where(
        "candidate_target_end_year > query_origin_year"
    ).limit(1).count():
        raise RuntimeError("Analogue audit contains a candidate outcome unavailable at query time")
    if audit_matches.where(
        "candidate_geoid_2020 = query_geoid_2020"
    ).limit(1).count():
        raise RuntimeError("Analogue audit contains a same-tract match")

    incomplete = (
        audit_matches.groupBy(*AUDIT_QUERY_KEYS, "variant_name")
        .count()
        .where(functions.col("count") != top_k)
    )
    if incomplete.limit(1).count():
        raise RuntimeError("At least one query and audit variant did not return top-k matches")

    query_variant_counts = (
        audit_matches.groupBy(*AUDIT_QUERY_KEYS)
        .agg(functions.countDistinct("variant_name").alias("variant_count"))
        .where(functions.col("variant_count") != expected_variant_count)
    )
    if query_variant_counts.limit(1).count():
        raise RuntimeError("Audit variants do not cover an identical set of query cases")
    if audit_matches.select("variant_name").distinct().count() != expected_variant_count:
        raise RuntimeError("Published audit variant count differs from the declared registry")
    if audit_matches.where("exactness_status IS NULL").limit(1).count():
        raise RuntimeError("Analogue audit contains a variant without exactness evidence")
    if audit_matches.where(
        "perturbation_kind = 'baseline' AND NOT exactness_certified"
    ).limit(1).count():
        raise RuntimeError("A rerun baseline was not marked as exact")

    repeated_unique = (
        audit_matches.where("unique_candidate_tract")
        .groupBy(*AUDIT_QUERY_KEYS, "variant_name")
        .agg(functions.countDistinct("candidate_geoid_2020").alias("tract_count"))
        .where(functions.col("tract_count") != top_k)
    )
    if repeated_unique.limit(1).count():
        raise RuntimeError("A unique-candidate variant contains a repeated physical tract")

    stability_variant_counts = (
        stability.groupBy(*AUDIT_QUERY_KEYS)
        .agg(functions.countDistinct("variant_name").alias("variant_count"))
        .where(functions.col("variant_count") != expected_variant_count)
    )
    if stability_variant_counts.limit(1).count():
        raise RuntimeError("Stability summary dropped one or more query and variant combinations")
    expected_stability_rows = (
        audit_matches.select(*AUDIT_QUERY_KEYS).distinct().count()
        * expected_variant_count
    )
    if stability.count() != expected_stability_rows:
        raise RuntimeError("Stability summary row count does not reconcile to queries and variants")
    if stability.where(
        (functions.col("match_count") != top_k)
        | functions.col("top_k_overlap_share").isNull()
        | (functions.col("top_k_overlap_share") < 0)
        | (functions.col("top_k_overlap_share") > 1)
    ).limit(1).count():
        raise RuntimeError("Stability summary failed completeness or metric-range checks")
    if case_review.limit(1).count() == 0:
        raise RuntimeError("Deterministic case selection returned no review evidence")
    if case_review.where("query_temporal_role <> 'validation'").limit(1).count():
        raise RuntimeError("Case-review evidence contains a non-validation query")


ensure_experiment_parent(experiment_path)
mlflow.set_experiment(experiment_path)
variants = default_audit_variants()
with mlflow.start_run(run_name="historical-analogue-audit-and-stability") as active_run:
    mlflow.log_params(
        {
            "evaluation_role": "validation",
            "locked_test_access": "prohibited",
            "top_k": top_k,
            "shortlist_k": shortlist_k,
            "variant_count": len(variants),
            "variant_names": ",".join(variant.variant_name for variant in variants),
            "source_baseline_table": baseline_match_table,
            "baseline_reproduction_required": "true",
        }
    )
    result = build_analogue_stability_run(
        panel,
        baseline_matches,
        top_k=top_k,
        shortlist_k=shortlist_k,
        variants=variants,
        run_id=active_run.info.run_id,
    )
    result.audit_matches.cache().count()
    result.stability_summary.cache().count()
    result.case_review.cache().count()
    validate_outputs(result, expected_variant_count=len(variants))

    metric_rows = (
        result.stability_summary.groupBy("perturbation_kind")
        .agg(
            functions.avg("top_k_overlap_share").alias("mean_overlap_share"),
            functions.avg("top_k_jaccard_similarity").alias("mean_jaccard"),
            functions.avg("top_three_retention_share").alias("mean_top_three_retention"),
            functions.avg(functions.col("exactness_certified").cast("double")).alias(
                "exactness_certification_share"
            ),
        )
        .collect()
    )
    for row in metric_rows:
        stem = str(row["perturbation_kind"])
        mlflow.log_metric(f"{stem}_mean_overlap_share", float(row["mean_overlap_share"]))
        mlflow.log_metric(f"{stem}_mean_jaccard", float(row["mean_jaccard"]))
        mlflow.log_metric(
            f"{stem}_mean_top_three_retention",
            float(row["mean_top_three_retention"]),
        )
        mlflow.log_metric(
            f"{stem}_exactness_certification_share",
            float(row["exactness_certification_share"]),
        )

# COMMAND ----------

audit_match_name = qualified_name(catalog, model_schema, audit_match_table)
stability_summary_name = qualified_name(
    catalog, evaluation_schema, stability_summary_table
)
case_review_name = qualified_name(catalog, evaluation_schema, case_review_table)

outputs = (
    (result.audit_matches, audit_match_name),
    (result.stability_summary, stability_summary_name),
    (result.case_review, case_review_name),
)
for frame, table_name in outputs:
    (
        frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table_name)
    )

# COMMAND ----------

published_audit = spark.table(audit_match_name)
published_stability = spark.table(stability_summary_name)
published_cases = spark.table(case_review_name)

if published_audit.select("analogue_audit_run_id").distinct().count() != 1:
    raise RuntimeError("Published audit matches contain more than one audit run")
if published_stability.select("analogue_audit_run_id").distinct().count() != 1:
    raise RuntimeError("Published stability summary contains more than one audit run")
if published_cases.select("analogue_audit_run_id").distinct().count() != 1:
    raise RuntimeError("Published case review contains more than one audit run")

display(
    published_stability.groupBy(
        "representation_name", "perturbation_kind", "stability_band"
    ).agg(
        functions.count(functions.lit(1)).alias("query_variant_count"),
        functions.avg("top_k_overlap_share").alias("mean_top_k_overlap_share"),
        functions.avg(functions.col("exactness_certified").cast("double")).alias(
            "exactness_certification_share"
        ),
    ).orderBy("representation_name", "perturbation_kind", "stability_band")
)
display(
    published_cases.orderBy(
        "horizon_years",
        "query_origin_year",
        "query_geoid_2020",
        "representation_name",
        "match_rank",
    )
)
print(f"Published analogue variant matches to {audit_match_name}.")
print(f"Published query-level stability metrics to {stability_summary_name}.")
print(f"Published deterministic case-review evidence to {case_review_name}.")
print(f"Source historical analogue run: {result.source_historical_analogue_run_id}")
print(f"Audit MLflow run: {result.run_id}")

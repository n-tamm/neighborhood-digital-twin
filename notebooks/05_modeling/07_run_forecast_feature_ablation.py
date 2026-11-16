# Databricks notebook source
# ruff: noqa: E402, F821
# AI Assistance:
# OpenAI Copilot SDK in VS Code assisted with code generation and experiment setup.
# Results are exploratory; model and feature-selection decisions remain author-owned.

# COMMAND ----------

import json
import sys
from pathlib import Path

import mlflow

for candidate in (Path.cwd(), *Path.cwd().parents):
    repository_src = candidate / "src"
    if (repository_src / "neighborhood_twin").is_dir():
        sys.path.insert(0, str(repository_src))
        break
else:
    raise RuntimeError("Could not locate the deployed project src directory")

from neighborhood_twin.forecasting import (  # noqa: E402
    GBT_SEED,
    GBT_STEP_SIZE,
    GBT_SUBSAMPLING_RATE,
    LINEAR_FEATURE_COLUMNS,
    gbt_temporal_cv_origin_years,
)

from pyspark.ml import Pipeline
from pyspark.ml.feature import Imputer, VectorAssembler
from pyspark.ml.regression import GBTRegressor
from pyspark.sql import functions

# COMMAND ----------

HORIZON = 1
MAX_DEPTH = 2
MAX_ITER = 50
STEP_SIZE = 0.05
SUBSAMPLING_RATE = 0.8
EXPERIMENT_PATH = "/Shared/neighborhood-digital-twin/forecast-baselines"

FEATURE_FAMILIES = {
    "hpi_history": (
        "origin_annual_change_pct",
        "hpi_change_1_year_pct",
        "hpi_change_3_year_pct",
        "hpi_change_5_year_pct",
        "hpi_recent_3_year_mean_change_pct",
        "hpi_recent_5_year_change_stddev_pct",
        "hpi_history_observation_count",
        "hpi_history_gap_count",
    ),
    "regional_context": (
        "county_origin_mean_annual_change_pct",
        "state_origin_mean_annual_change_pct",
    ),
    "community_scale": (
        "population_total_estimate",
        "housing_units_total_estimate",
    ),
    "occupancy_tenure": (
        "occupancy_rate_estimate",
        "vacancy_rate_estimate",
        "owner_occupancy_rate_estimate",
        "renter_occupancy_rate_estimate",
    ),
    "housing_structure": (
        "single_family_share_estimate",
        "multifamily_share_estimate",
        "mobile_home_share_estimate",
    ),
    "affordability": (
        "median_household_income_estimate",
        "median_owner_occupied_value_estimate",
        "median_gross_rent_estimate",
    ),
    "data_timing_quality": (
        "acs_measurement_age_years",
        "median_household_income_relative_moe",
        "median_owner_occupied_value_relative_moe",
        "median_gross_rent_relative_moe",
    ),
}
ALL_FEATURES = LINEAR_FEATURE_COLUMNS
if set(feature for family in FEATURE_FAMILIES.values() for feature in family) != set(
    ALL_FEATURES
):
    raise ValueError("Feature families must partition the registered model inputs")

panel = spark.table("workspace.neighborhood_twin_gold.gold_modeling_panel")
training = panel.where(
    (functions.col("horizon_years") == HORIZON)
    & functions.col("eligible_for_point_model_fit")
    & functions.col("target_is_observed")
)
training_origins = [
    int(row[0])
    for row in training.select("forecast_origin_year").distinct().collect()
]
fold_years = gbt_temporal_cv_origin_years(
    training_origins,
    horizon_years=HORIZON,
)
if len(fold_years) < 2:
    raise ValueError(f"Expected at least two purge-safe folds; got {fold_years}")

ABLATIONS = {"full_features": ALL_FEATURES}
for family_name, family_features in FEATURE_FAMILIES.items():
    ABLATIONS[f"drop_{family_name}"] = tuple(
        name for name in ALL_FEATURES if name not in family_features
    )

# COMMAND ----------

fold_results = []
mlflow.set_experiment(EXPERIMENT_PATH)
with mlflow.start_run(run_name="one-year-training-only-feature-ablation") as run:
    mlflow.log_params(
        {
            "analysis": "one_year_drop_one_feature_family",
            "horizon_years": HORIZON,
            "target": "target_cumulative_log_change",
            "evaluation_data": "eligible_training_rows_only",
            "fold_years": ",".join(map(str, fold_years)),
            "training_target_purge": "target_end_year < held_out_origin_year",
            "max_depth": MAX_DEPTH,
            "max_iter": MAX_ITER,
            "step_size": GBT_STEP_SIZE,
            "subsampling_rate": GBT_SUBSAMPLING_RATE,
            "seed": GBT_SEED,
            "features_per_family": json.dumps(
                {name: len(features) for name, features in FEATURE_FAMILIES.items()},
                sort_keys=True,
            ),
        }
    )
    for fold_year in fold_years:
        fold_training = training.where(
            (functions.col("forecast_origin_year") < fold_year)
            & (functions.col("target_end_year") < fold_year)
        )
        fold_validation = training.where(
            functions.col("forecast_origin_year") == fold_year
        )
        if not fold_training.limit(1).count() or not fold_validation.limit(1).count():
            raise ValueError(f"Temporal fold {fold_year} is empty after purging")

        for variant_name, feature_columns in ABLATIONS.items():
            imputed_columns = tuple(
                f"_{variant_name}_{index}_imputed"
                for index in range(len(feature_columns))
            )
            pipeline = Pipeline(
                stages=[
                    Imputer(
                        strategy="median",
                        inputCols=list(feature_columns),
                        outputCols=list(imputed_columns),
                    ),
                    VectorAssembler(
                        inputCols=list(imputed_columns),
                        outputCol=f"_{variant_name}_features",
                        handleInvalid="error",
                    ),
                    GBTRegressor(
                        featuresCol=f"_{variant_name}_features",
                        labelCol="target_cumulative_log_change",
                        predictionCol=f"_{variant_name}_prediction",
                        maxDepth=MAX_DEPTH,
                        maxIter=MAX_ITER,
                        stepSize=GBT_STEP_SIZE,
                        subsamplingRate=GBT_SUBSAMPLING_RATE,
                        seed=GBT_SEED,
                    ),
                ]
            )
            fitted = pipeline.fit(fold_training)
            scored = fitted.transform(fold_validation)
            summary = scored.agg(
                functions.count("*").alias("row_count"),
                functions.avg(
                    functions.abs(
                        functions.col("target_cumulative_log_change")
                        - functions.col(f"_{variant_name}_prediction")
                    )
                ).alias("mae"),
            ).first()
            fold_results.append(
                {
                    "variant": variant_name,
                    "fold_origin_year": fold_year,
                    "observation_count": int(summary["row_count"]),
                    "mae": float(summary["mae"]),
                    "feature_count": len(feature_columns),
                }
            )
            mlflow.log_metric(
                f"{variant_name}_fold_{fold_year}_mae",
                float(summary["mae"]),
            )

    mean_scores = {}
    for variant_name in ABLATIONS:
        scores = [
            row["mae"] for row in fold_results if row["variant"] == variant_name
        ]
        mean_scores[variant_name] = sum(scores) / len(scores)
        mlflow.log_metric(f"{variant_name}_mean_fold_mae", mean_scores[variant_name])

    baseline_mae = mean_scores["full_features"]
    for variant_name, mae in mean_scores.items():
        if variant_name != "full_features":
            mlflow.log_metric(
                f"{variant_name}_delta_mae_vs_full",
                mae - baseline_mae,
            )

result = {
    "mlflow_run_id": run.info.run_id,
    "horizon_years": HORIZON,
    "fold_origin_years": list(fold_years),
    "candidate_parameters": {
        "max_depth": MAX_DEPTH,
        "max_iter": MAX_ITER,
        "step_size": GBT_STEP_SIZE,
        "subsampling_rate": GBT_SUBSAMPLING_RATE,
        "seed": GBT_SEED,
    },
    "mean_fold_mae": mean_scores,
    "delta_mae_vs_full_features": {
        name: score - baseline_mae
        for name, score in mean_scores.items()
        if name != "full_features"
    },
    "fold_results": fold_results,
    "publishes_forecasts_or_scorecards": False,
}
print(json.dumps(result, indent=2))
dbutils.notebook.exit(json.dumps(result))

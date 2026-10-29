"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Reusable summary contracts for the visual EDA checkpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import reduce
from typing import Any

from neighborhood_twin.data.databricks import qualified_name
from neighborhood_twin.products import SIMILARITY_FEATURE_COLUMNS, parse_state_fips_codes
from neighborhood_twin.validate import QualityMetric, hard_failures, new_quality_run_id

HOUSING_COVERAGE_TABLE = "gold_eda_housing_coverage"
COHORT_COMPARISON_TABLE = "gold_eda_cohort_comparison"
HPI_TEMPORAL_TABLE = "gold_eda_hpi_temporal"
FIGURE_MANIFEST_TABLE = "gold_eda_figure_manifest"
VISUAL_EDA_SCHEMA_VERSION = "1.0.0"

HOUSING_COMPOSITION_BANDS = (
    (1, "Less than 25% single-family", 0.00, 0.25),
    (2, "25% to less than 50%", 0.25, 0.50),
    (3, "50% to less than 75%", 0.50, 0.75),
    (4, "75% to less than 90%", 0.75, 0.90),
    (5, "90% to 100%", 0.90, 1.01),
)


@dataclass(frozen=True)
class VisualEdaBuild:
    """Validated visual-EDA summary frames that have not yet been published."""

    build_id: str
    built_at_utc: str
    frames: dict[str, Any]
    metrics: list[QualityMetric]


def housing_composition_band(value: float | None) -> str:
    """Assign one single-family housing-share band for labels and tests."""

    if value is None:
        return "Missing housing composition"
    for _, label, lower, upper in HOUSING_COMPOSITION_BANDS:
        if lower <= value < upper:
            return label
    raise ValueError("Single-family housing share must be between zero and one")


def _lineage(frame: Any, *, build_id: str, built_at_utc: str) -> Any:
    """Attach visual-EDA schema and build lineage to a Spark summary frame."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    return (
        frame.withColumn("visual_eda_schema_version", functions.lit(VISUAL_EDA_SCHEMA_VERSION))
        .withColumn("visual_eda_build_id", functions.lit(build_id))
        .withColumn(
            "visual_eda_built_at_utc", functions.to_timestamp(functions.lit(built_at_utc))
        )
    )


def _housing_band_columns(functions: Any) -> tuple[Any, Any]:
    """Build ordered Spark expressions for the housing-composition bands."""

    value = functions.col("single_family_share_estimate")
    order = functions.when(value.isNull(), functions.lit(6))
    label = functions.when(value.isNull(), functions.lit("Missing housing composition"))
    for band_order, band_label, _lower, upper in HOUSING_COMPOSITION_BANDS:
        order = order.when(value < upper, functions.lit(band_order))
        label = label.when(value < upper, functions.lit(band_label))
    return order.otherwise(functions.lit(6)), label.otherwise(
        functions.lit("Missing housing composition")
    )


def _housing_coverage(profile: Any, *, build_id: str, built_at_utc: str) -> Any:
    """Summarize FHFA and product eligibility by housing-composition band."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    band_order, band_label = _housing_band_columns(functions)
    current = (
        profile.where(functions.col("has_current_acs_profile"))
        .withColumn("housing_composition_band_order", band_order)
        .withColumn("housing_composition_band", band_label)
    )
    summary = current.groupBy(
        "housing_composition_band_order", "housing_composition_band"
    ).agg(
        functions.count("geoid_2020").alias("tract_count"),
        functions.sum(functions.col("has_fhfa_history").cast("int")).alias(
            "fhfa_history_tract_count"
        ),
        functions.sum(functions.col("forecast_candidate").cast("int")).alias(
            "forecast_candidate_count"
        ),
        functions.sum(functions.col("similarity_candidate").cast("int")).alias(
            "similarity_candidate_count"
        ),
        functions.expr("percentile_approx(single_family_share_estimate, 0.5, 10000)").alias(
            "median_single_family_share"
        ),
        functions.expr("percentile_approx(multifamily_share_estimate, 0.5, 10000)").alias(
            "median_multifamily_share"
        ),
        functions.expr(
            "percentile_approx(median_household_income_estimate, 0.5, 10000)"
        ).alias("median_household_income"),
    )
    return _lineage(
        summary.withColumn(
            "fhfa_history_share",
            functions.col("fhfa_history_tract_count") / functions.col("tract_count"),
        )
        .withColumn(
            "forecast_candidate_share",
            functions.col("forecast_candidate_count") / functions.col("tract_count"),
        )
        .withColumn(
            "similarity_candidate_share",
            functions.col("similarity_candidate_count") / functions.col("tract_count"),
        ),
        build_id=build_id,
        built_at_utc=built_at_utc,
    )


def _feature_summary(profile: Any, feature: str, candidate: bool, order: int) -> Any:
    """Summarize one feature for either included or excluded current tracts."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    cohort = profile.where(
        functions.col("has_current_acs_profile")
        & (functions.col("forecast_candidate") == functions.lit(candidate))
    )
    return cohort.agg(
        functions.lit(order).alias("feature_order"),
        functions.lit(feature).alias("feature_name"),
        functions.lit("forecast_candidate" if candidate else "excluded_current_acs").alias(
            "cohort"
        ),
        functions.count(functions.lit(1)).alias("cohort_tract_count"),
        functions.count(feature).alias("available_value_count"),
        functions.avg(feature).alias("feature_mean"),
        functions.stddev_samp(feature).alias("feature_standard_deviation"),
        functions.expr(f"percentile_approx(`{feature}`, 0.5, 10000)").alias("feature_median"),
    ).withColumn(
        "missing_value_share",
        (functions.col("cohort_tract_count") - functions.col("available_value_count"))
        / functions.col("cohort_tract_count"),
    )


def _cohort_comparison(profile: Any, *, build_id: str, built_at_utc: str) -> Any:
    """Compare forecast candidates with excluded current-ACS tracts by feature."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    summaries = [
        _feature_summary(profile, feature, candidate, order)
        for order, feature in enumerate(SIMILARITY_FEATURE_COLUMNS, start=1)
        for candidate in (True, False)
    ]
    long_summary = reduce(lambda left, right: left.unionByName(right), summaries)
    included = long_summary.where(functions.col("cohort") == "forecast_candidate").alias(
        "included"
    )
    excluded = long_summary.where(functions.col("cohort") == "excluded_current_acs").alias(
        "excluded"
    )
    pooled_sd = functions.sqrt(
        (
            functions.pow(functions.col("included.feature_standard_deviation"), 2)
            + functions.pow(functions.col("excluded.feature_standard_deviation"), 2)
        )
        / 2
    )
    comparison = included.join(excluded, "feature_name", "inner").select(
        functions.col("included.feature_order").alias("feature_order"),
        "feature_name",
        functions.col("included.cohort_tract_count").alias("included_tract_count"),
        functions.col("excluded.cohort_tract_count").alias("excluded_tract_count"),
        functions.col("included.available_value_count").alias("included_available_count"),
        functions.col("excluded.available_value_count").alias("excluded_available_count"),
        functions.col("included.feature_mean").alias("included_mean"),
        functions.col("excluded.feature_mean").alias("excluded_mean"),
        functions.col("included.feature_median").alias("included_median"),
        functions.col("excluded.feature_median").alias("excluded_median"),
        functions.col("included.missing_value_share").alias("included_missing_share"),
        functions.col("excluded.missing_value_share").alias("excluded_missing_share"),
        functions.when(
            pooled_sd > 0,
            (functions.col("included.feature_mean") - functions.col("excluded.feature_mean"))
            / pooled_sd,
        ).alias("standardized_mean_difference"),
    )
    return _lineage(comparison, build_id=build_id, built_at_utc=built_at_utc)


def _one_temporal_scope(fhfa: Any, *, state_fips: str | None, label: str) -> Any:
    """Summarize annual FHFA change quantiles for one national or state scope."""

    from pyspark.sql import functions  # type: ignore[import-not-found]

    scoped = fhfa if state_fips is None else fhfa.where(functions.col("state_fips") == state_fips)
    return scoped.groupBy("observation_year").agg(
        functions.lit("US" if state_fips is None else state_fips).alias("scope_code"),
        functions.lit(label).alias("scope_label"),
        functions.count(functions.lit(1)).alias("source_row_count"),
        functions.count("annual_change_pct").alias("available_change_count"),
        functions.expr("percentile_approx(annual_change_pct, 0.1, 10000)").alias(
            "p10_annual_change_pct"
        ),
        functions.expr("percentile_approx(annual_change_pct, 0.5, 10000)").alias(
            "median_annual_change_pct"
        ),
        functions.expr("percentile_approx(annual_change_pct, 0.9, 10000)").alias(
            "p90_annual_change_pct"
        ),
    )


def _hpi_temporal(
    fhfa: Any,
    *,
    pilot_states: tuple[str, ...],
    build_id: str,
    built_at_utc: str,
) -> Any:
    """Combine national and selected-state FHFA temporal summaries."""

    labels = {"04": "Arizona", "26": "Michigan", "42": "Pennsylvania"}
    scopes = [_one_temporal_scope(fhfa, state_fips=None, label="United States")]
    scopes.extend(
        _one_temporal_scope(
            fhfa,
            state_fips=state_fips,
            label=labels.get(state_fips, f"State {state_fips}"),
        )
        for state_fips in pilot_states
    )
    return _lineage(
        reduce(lambda left, right: left.unionByName(right), scopes),
        build_id=build_id,
        built_at_utc=built_at_utc,
    )


def _quality_metrics(
    frames: dict[str, Any], *, build_id: str, built_at_utc: str, catalog: str, schema: str
) -> list[QualityMetric]:
    """Validate visual-EDA summary volume, keys, and effect-size availability."""

    keys = {
        HOUSING_COVERAGE_TABLE: ("housing_composition_band_order",),
        COHORT_COMPARISON_TABLE: ("feature_name",),
        HPI_TEMPORAL_TABLE: ("scope_code", "observation_year"),
    }
    metrics: list[QualityMetric] = []
    for table, frame in frames.items():
        row_count = frame.count()
        duplicate_count = row_count - frame.select(*keys[table]).distinct().count()
        for metric_name, value, status, expectation in (
            ("row_count", row_count, "pass" if row_count > 0 else "fail", "> 0"),
            (
                "duplicate_key_count",
                duplicate_count,
                "pass" if duplicate_count == 0 else "fail",
                "= 0",
            ),
        ):
            metrics.append(
                QualityMetric(
                    quality_run_id=build_id,
                    profiled_at_utc=built_at_utc,
                    table_name=f"{catalog}.{schema}.{table}",
                    metric_group="visual_eda",
                    metric_name=metric_name,
                    dimension="all",
                    metric_value=float(value),
                    status=status,
                    expectation=expectation,
                    notes="Visual EDA summary publication check.",
                )
            )
    comparison = frames[COHORT_COMPARISON_TABLE]
    missing_effect_count = comparison.where(
        comparison.standardized_mean_difference.isNull()
    ).count()
    metrics.append(
        QualityMetric(
            quality_run_id=build_id,
            profiled_at_utc=built_at_utc,
            table_name=f"{catalog}.{schema}.{COHORT_COMPARISON_TABLE}",
            metric_group="visual_eda",
            metric_name="missing_standardized_difference_count",
            dimension="all",
            metric_value=float(missing_effect_count),
            status="pass" if missing_effect_count == 0 else "fail",
            expectation="= 0",
            notes="Every compared feature must have a defined pooled standard deviation.",
        )
    )
    return metrics


def prepare_visual_eda_build(
    spark: Any,
    *,
    catalog: str,
    silver_schema: str,
    gold_schema: str,
    pilot_state_fips: str = "04,26,42",
    built_at: datetime | None = None,
) -> VisualEdaBuild:
    """Create visual-EDA summary contracts from current gold and FHFA silver data."""

    pilot_states = parse_state_fips_codes(pilot_state_fips)
    profile = spark.table(f"{catalog}.{gold_schema}.gold_tract_profile_current")
    fhfa = spark.table(f"{catalog}.{silver_schema}.silver_fhfa_tract_year")
    build_id, built_at_utc = new_quality_run_id(built_at)
    frames = {
        HOUSING_COVERAGE_TABLE: _housing_coverage(
            profile, build_id=build_id, built_at_utc=built_at_utc
        ),
        COHORT_COMPARISON_TABLE: _cohort_comparison(
            profile, build_id=build_id, built_at_utc=built_at_utc
        ),
        HPI_TEMPORAL_TABLE: _hpi_temporal(
            fhfa,
            pilot_states=pilot_states,
            build_id=build_id,
            built_at_utc=built_at_utc,
        ),
    }
    metrics = _quality_metrics(
        frames,
        build_id=build_id,
        built_at_utc=built_at_utc,
        catalog=catalog,
        schema=gold_schema,
    )
    return VisualEdaBuild(build_id, built_at_utc, frames, metrics)


def publish_visual_eda_build(
    build: VisualEdaBuild, *, catalog: str, schema: str
) -> tuple[str, ...]:
    """Publish every visual-EDA summary after all hard checks pass."""

    failures = hard_failures(build.metrics)
    if failures:
        raise ValueError(
            "Visual EDA build has hard failures: "
            + ", ".join(f"{item.table_name}:{item.metric_name}" for item in failures)
        )
    published = []
    for table, frame in build.frames.items():
        name = qualified_name(catalog, schema, table)
        (
            frame.write.format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(name)
        )
        published.append(name)
    return tuple(published)

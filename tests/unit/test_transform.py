"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

from neighborhood_twin.data.acs import ACS_CORE_MEASURES
from neighborhood_twin.transform import (
    ACS_DERIVED_RATIO_COLUMNS,
    SILVER_SCHEMA_VERSION,
    acs_silver_measure_columns,
    parse_acs_numeric_value,
)


def test_parse_acs_numeric_value_preserves_valid_number() -> None:
    assert parse_acs_numeric_value(" 123.5 ") == (123.5, None)


def test_parse_acs_numeric_value_classifies_missing_values() -> None:
    assert parse_acs_numeric_value(None) == (None, "blank")
    assert parse_acs_numeric_value("  ") == (None, "blank")
    assert parse_acs_numeric_value("-666666666") == (
        None,
        "census_special_value:-666666666",
    )
    assert parse_acs_numeric_value("not-a-number") == (None, "parse_failure")


def test_acs_silver_measure_columns_are_complete_and_unique() -> None:
    columns = acs_silver_measure_columns()

    assert len(columns) == len(ACS_CORE_MEASURES) * 5
    assert len(columns) == len(set(columns))
    assert "median_household_income_estimate" in columns
    assert "median_household_income_moe" in columns
    assert "median_household_income_relative_moe" in columns


def test_silver_contract_version_and_ratio_names_are_stable() -> None:
    assert SILVER_SCHEMA_VERSION == "1.0.0"
    assert "single_family_share_estimate" in ACS_DERIVED_RATIO_COLUMNS
    assert "multifamily_share_estimate" in ACS_DERIVED_RATIO_COLUMNS

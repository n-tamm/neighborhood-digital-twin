"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

from neighborhood_twin.geography_hierarchy import (
    COUNTRY_ROWS,
    DIVISION_ROWS,
    GEOGRAPHY_TABLES,
    REGION_ROWS,
    STATE_ROWS,
    SUPPORTED_STATE_FIPS,
)


def test_hierarchy_reference_counts_and_keys_are_complete() -> None:
    assert len(COUNTRY_ROWS) == 1
    assert len(REGION_ROWS) == 4
    assert len(DIVISION_ROWS) == 9
    assert len(STATE_ROWS) == 51
    assert len(SUPPORTED_STATE_FIPS) == len(set(SUPPORTED_STATE_FIPS))
    assert "11" in SUPPORTED_STATE_FIPS
    assert "72" not in SUPPORTED_STATE_FIPS


def test_every_state_has_valid_division_and_region_parents() -> None:
    divisions = {row["division_code"]: row["region_code"] for row in DIVISION_ROWS}
    regions = {row["region_code"] for row in REGION_ROWS}

    assert all(row["division_code"] in divisions for row in STATE_ROWS)
    assert all(divisions[row["division_code"]] in regions for row in STATE_ROWS)


def test_expected_silver_dimension_names_are_unique() -> None:
    assert set(GEOGRAPHY_TABLES) == {
        "country",
        "region",
        "division",
        "state",
        "county",
        "tract",
    }
    assert len(GEOGRAPHY_TABLES.values()) == len(set(GEOGRAPHY_TABLES.values()))

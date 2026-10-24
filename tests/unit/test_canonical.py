"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

from neighborhood_twin.canonical import (
    CANONICAL_SCHEMA_VERSION,
    CANONICAL_TRACT_COLUMNS,
    CANONICAL_TRACT_TABLE,
)


def test_canonical_contract_has_one_explicit_geography_key() -> None:
    assert CANONICAL_SCHEMA_VERSION == "1.0.0"
    assert CANONICAL_TRACT_TABLE == "silver_canonical_tract_2020"
    assert CANONICAL_TRACT_COLUMNS[0] == "geoid_2020"
    assert len(CANONICAL_TRACT_COLUMNS) == len(set(CANONICAL_TRACT_COLUMNS))
    assert "has_display_geometry" in CANONICAL_TRACT_COLUMNS
    assert "display_geometry_role" in CANONICAL_TRACT_COLUMNS

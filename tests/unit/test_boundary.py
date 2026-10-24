"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

from neighborhood_twin.data.boundary import (
    BOUNDARY_ATTRIBUTE_FIELDS,
    BOUNDARY_REQUIRED_EXTENSIONS,
    valid_boundary_identity,
)


def test_boundary_identity_requires_hierarchical_geoid() -> None:
    assert valid_boundary_identity(
        state_fips="26",
        county_fips="163",
        tract_code="500100",
        geoid="26163500100",
    )
    assert not valid_boundary_identity(
        state_fips="26",
        county_fips="163",
        tract_code="500100",
        geoid="26163500101",
    )


def test_boundary_source_contract_is_explicit() -> None:
    assert BOUNDARY_ATTRIBUTE_FIELDS[0:3] == ("STATEFP", "COUNTYFP", "TRACTCE")
    assert "GEOID" in BOUNDARY_ATTRIBUTE_FIELDS
    assert BOUNDARY_REQUIRED_EXTENSIONS == (".shp", ".shx", ".dbf", ".prj")

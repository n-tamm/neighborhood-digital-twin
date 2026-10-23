"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import json
from urllib.parse import parse_qs, urlsplit

import pytest

from neighborhood_twin.data.acquisition import redact_url
from neighborhood_twin.data.acs import (
    acs_variable_codes,
    build_acs_tract_request,
    parse_acs_api_payload,
)


def test_acs_request_stays_within_limit_and_redacts_key() -> None:
    request = build_acs_tract_request(release_year=2024, state_fips="26", api_key="private-key")
    query = parse_qs(urlsplit(request.url).query)

    assert len(query["get"][0].split(",")) <= 50
    assert query["in"] == ["state:26", "county:*"]
    assert query["key"] == ["private-key"]
    assert "private-key" not in redact_url(request.url, request.secret_query_parameters)
    assert request.reference_period == "2020-2024"


def test_acs_parser_builds_geoid_and_time_fields() -> None:
    header = ["NAME", *acs_variable_codes(), "state", "county", "tract"]
    row = ["Census Tract 1, Sample County, Michigan", *["1"] * 42, "26", "163", "000100"]
    payload = json.dumps([header, row])

    records = parse_acs_api_payload(payload, release_year=2024)

    assert len(records) == 1
    assert records[0]["geoid"] == "26163000100"
    assert records[0]["acs_release_year"] == 2024
    assert records[0]["acs_survey_start_year"] == 2020


def test_acs_parser_rejects_missing_required_fields() -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        parse_acs_api_payload(json.dumps([["NAME", "state"], ["Name", "26"]]), release_year=2024)

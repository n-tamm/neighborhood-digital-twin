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
    ACS_CORE_MEASURES,
    NATIONAL_ACS_RELEASE_YEARS,
    NATIONAL_SUPPORTED_STATE_FIPS,
    acs_measure_dictionary_records,
    acs_variable_codes,
    build_acs_tract_request,
    national_acs_expected_pairs,
    national_acs_expected_source_ids,
    parse_acs_api_payload,
    parse_acs_ingestion_scope,
)


def test_national_acs_contract_covers_2010_through_2024_for_states_and_dc() -> None:
    pairs = national_acs_expected_pairs()
    source_ids = national_acs_expected_source_ids()

    assert NATIONAL_ACS_RELEASE_YEARS == tuple(range(2010, 2025))
    assert len(NATIONAL_SUPPORTED_STATE_FIPS) == 51
    assert "11" in NATIONAL_SUPPORTED_STATE_FIPS
    assert "72" not in NATIONAL_SUPPORTED_STATE_FIPS
    assert len(pairs) == 765
    assert len(set(pairs)) == len(pairs)
    assert len(source_ids) == len(pairs)
    assert source_ids[0] == "acs5_tract_2010_state_01"
    assert source_ids[-1] == "acs5_tract_2024_state_56"


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


def test_acs_measure_dictionary_has_one_complete_row_per_measure() -> None:
    records = acs_measure_dictionary_records(release_year=2024)

    assert len(records) == len(ACS_CORE_MEASURES)
    assert len({record["measure_name"] for record in records}) == len(records)
    median_rent = next(
        record for record in records if record["measure_name"] == "median_gross_rent"
    )
    assert median_rent["universe"] == "Renter-occupied housing units paying cash rent"
    assert median_rent["unit"] == "dollars"
    metadata_url = median_rent["metadata_url"]
    assert isinstance(metadata_url, str)
    assert metadata_url.endswith("/B25064.html")


def test_historical_scope_parses_a_bounded_state_year_grid() -> None:
    scope = parse_acs_ingestion_scope(
        release_years="2014, 2019",
        state_fips_codes="04,26,42",
        maximum_requests=6,
    )

    assert scope.release_years == (2014, 2019)
    assert scope.state_fips_codes == ("04", "26", "42")
    assert scope.request_count == 6


@pytest.mark.parametrize(
    ("release_years", "state_fips_codes", "maximum_requests", "message"),
    [
        ("2019,2019", "26", 2, "duplicates"),
        ("2019", "2", 1, "two digits"),
        ("2014,2019", "04,26", 3, "split the history"),
    ],
)
def test_historical_scope_rejects_ambiguous_or_excessive_requests(
    release_years: str,
    state_fips_codes: str,
    maximum_requests: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        parse_acs_ingestion_scope(
            release_years=release_years,
            state_fips_codes=state_fips_codes,
            maximum_requests=maximum_requests,
        )

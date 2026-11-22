"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Known-answer tests for bounded Census address-to-tract lookup.
"""

from __future__ import annotations

import io
import json
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from neighborhood_app.geocoding import lookup_census_tract


class JsonResponse(io.BytesIO):
    """Context-managed byte response used by the geocoder opener double."""

    def __enter__(self) -> JsonResponse:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


def _payload(*, matches: list[dict[str, Any]]) -> bytes:
    return json.dumps({"result": {"addressMatches": matches}}).encode("utf-8")


def test_address_lookup_returns_2020_tract_and_readable_place() -> None:
    """A valid Census response should retain the tract, place, county, and state context."""

    captured: dict[str, Any] = {}

    def opener(request: Any, *, timeout: float) -> JsonResponse:
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return JsonResponse(
            _payload(
                matches=[
                    {
                        "matchedAddress": "4600 SILVER HILL RD, WASHINGTON, DC, 20233",
                        "addressComponents": {"city": "WASHINGTON", "state": "DC"},
                        "geographies": {
                            "Census Tracts": [{"GEOID": "24033802405"}],
                            "Counties": [{"NAME": "Prince George's County"}],
                            "States": [{"STUSAB": "MD"}],
                            "Census Designated Places": [{"NAME": "Suitland CDP"}],
                        },
                    }
                ]
            )
        )

    result = lookup_census_tract(
        "4600 Silver Hill Rd, Washington, DC 20233",
        opener=opener,
    )

    assert result.geoid_2020 == "24033802405"
    assert result.area_name == "Suitland CDP"
    assert result.county_name == "Prince George's County"
    assert result.state_abbreviation == "MD"
    assert result.display_label.startswith("Suitland CDP, Prince George's County, MD")
    query = parse_qs(urlparse(str(captured["url"])).query)
    assert query["benchmark"] == ["Public_AR_Current"]
    assert query["vintage"] == ["Census2020_Current"]
    assert captured["timeout"] == 10.0


def test_address_lookup_reports_no_match_without_guessing_a_tract() -> None:
    """An unmatched address should remain unavailable rather than returning a partial guess."""

    def opener(_: Any, *, timeout: float) -> JsonResponse:
        del timeout
        return JsonResponse(_payload(matches=[]))

    with pytest.raises(LookupError, match="could not match"):
        lookup_census_tract("9999 Unknown Road, Ann Arbor, MI 48104", opener=opener)


def test_address_lookup_rejects_incomplete_input_before_network_access() -> None:
    """A short location fragment is not enough to justify an external geocoder request."""

    with pytest.raises(ValueError, match="complete street address"):
        lookup_census_tract("Ann Arbor")

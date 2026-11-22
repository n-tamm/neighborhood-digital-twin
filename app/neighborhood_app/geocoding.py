"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Bounded address-to-tract lookup through the public U.S. Census Geocoder.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CENSUS_GEOCODER_ENDPOINT = (
    "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
)
GEOCODER_BENCHMARK = "Public_AR_Current"
GEOCODER_VINTAGE = "Census2020_Current"


@dataclass(frozen=True)
class GeocodedTract:
    """One Census-confirmed address match and its canonical 2020 tract context."""

    geoid_2020: str
    matched_address: str
    area_name: str
    county_name: str
    state_abbreviation: str

    @property
    def display_label(self) -> str:
        """Return a readable place label without making the tract identifier primary."""

        geography = ", ".join(
            item
            for item in (self.area_name, self.county_name, self.state_abbreviation)
            if item
        )
        return f"{geography} · Census tract {self.geoid_2020}"


def _first_geography(
    geographies: Mapping[str, Any],
    names: tuple[str, ...],
) -> Mapping[str, Any]:
    """Return the first available record across equivalent Census geography layers."""

    for name in names:
        records = geographies.get(name)
        if isinstance(records, list) and records and isinstance(records[0], Mapping):
            return records[0]
    return {}


def _area_name(geographies: Mapping[str, Any], address_components: Mapping[str, Any]) -> str:
    """Choose the most recognizable available incorporated, CDP, or subdivision label."""

    place = _first_geography(
        geographies,
        ("Incorporated Places", "Census Designated Places", "County Subdivisions"),
    )
    name = str(place.get("NAME") or place.get("BASENAME") or "").strip()
    if name:
        return name
    return str(address_components.get("city") or "").strip().title()


def lookup_census_tract(
    address: str,
    *,
    timeout_seconds: float = 10.0,
    opener: Callable[..., Any] = urlopen,
) -> GeocodedTract:
    """Resolve one U.S. street address to a canonical 2020 Census tract.

    The address is sent directly to the public Census Geocoder and is not written to project
    tables. The caller is responsible for explaining that external request to the user.
    """

    cleaned = " ".join(address.strip().split())
    if len(cleaned) < 8 or not re.search(r"\d", cleaned):
        raise ValueError("Enter a complete street address, city, and state or ZIP code.")
    if len(cleaned) > 200:
        raise ValueError("Address lookup is limited to 200 characters.")

    query = urlencode(
        {
            "address": cleaned,
            "benchmark": GEOCODER_BENCHMARK,
            "vintage": GEOCODER_VINTAGE,
            "format": "json",
        }
    )
    request = Request(
        f"{CENSUS_GEOCODER_ENDPOINT}?{query}",
        headers={"User-Agent": "Neighborhood-Housing-Intelligence/0.1"},
    )
    try:
        with opener(request, timeout=timeout_seconds) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError("The Census address lookup is temporarily unavailable.") from error

    matches = payload.get("result", {}).get("addressMatches", [])
    if not matches or not isinstance(matches[0], Mapping):
        raise LookupError(
            "The Census Geocoder could not match that address. Check the street, city, state, "
            "and ZIP code."
        )
    match = matches[0]
    geographies = match.get("geographies", {})
    if not isinstance(geographies, Mapping):
        raise LookupError("The matched address did not include Census geography information.")

    tract = _first_geography(geographies, ("Census Tracts",))
    county = _first_geography(geographies, ("Counties",))
    state = _first_geography(geographies, ("States",))
    geoid = str(tract.get("GEOID") or "")
    if len(geoid) != 11 or not geoid.isdigit():
        raise LookupError("The matched address did not resolve to a canonical 2020 Census tract.")

    address_components = match.get("addressComponents", {})
    if not isinstance(address_components, Mapping):
        address_components = {}
    return GeocodedTract(
        geoid_2020=geoid,
        matched_address=str(match.get("matchedAddress") or cleaned),
        area_name=_area_name(geographies, address_components),
        county_name=str(county.get("NAME") or county.get("BASENAME") or "").strip(),
        state_abbreviation=str(
            state.get("STUSAB") or address_components.get("state") or ""
        ).strip(),
    )

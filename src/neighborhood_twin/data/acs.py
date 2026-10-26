"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Focused ACS five-year tract requests and raw-response parsing.
"""

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from neighborhood_twin.data.acquisition import SourceRequest
from neighborhood_twin.data.catalog import SourceDefinition

NATIONAL_ACS_RELEASE_YEARS: tuple[int, ...] = tuple(range(2010, 2025))
NATIONAL_SUPPORTED_STATE_FIPS: tuple[str, ...] = (
    "01",
    "02",
    "04",
    "05",
    "06",
    "08",
    "09",
    "10",
    "11",
    "12",
    "13",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "27",
    "28",
    "29",
    "30",
    "31",
    "32",
    "33",
    "34",
    "35",
    "36",
    "37",
    "38",
    "39",
    "40",
    "41",
    "42",
    "44",
    "45",
    "46",
    "47",
    "48",
    "49",
    "50",
    "51",
    "53",
    "54",
    "55",
    "56",
)


@dataclass(frozen=True)
class AcsMeasure:
    """One named ACS estimate whose estimate and margin of error travel together."""

    name: str
    variable_root: str
    concept: str

    @property
    def group_code(self) -> str:
        """Return the Census table group encoded in the variable root."""

        return self.variable_root.split("_", maxsplit=1)[0]

    @property
    def estimate_code(self) -> str:
        """Return the Census API code for the measure estimate."""

        return f"{self.variable_root}E"

    @property
    def margin_of_error_code(self) -> str:
        """Return the Census API code for the published margin of error."""

        return f"{self.variable_root}M"


@dataclass(frozen=True)
class AcsIngestionScope:
    """Bounded state-by-release scope for one historical acquisition run."""

    release_years: tuple[int, ...]
    state_fips_codes: tuple[str, ...]

    @property
    def request_count(self) -> int:
        """Return the state-by-release request count represented by this scope."""

        return len(self.release_years) * len(self.state_fips_codes)


ACS_CORE_MEASURES: tuple[AcsMeasure, ...] = (
    AcsMeasure("population_total", "B01003_001", "Total population"),
    AcsMeasure("housing_units_total", "B25001_001", "Total housing units"),
    AcsMeasure("occupied_units", "B25002_002", "Occupied housing units"),
    AcsMeasure("vacant_units", "B25002_003", "Vacant housing units"),
    AcsMeasure("occupied_tenure_total", "B25003_001", "Occupied tenure universe"),
    AcsMeasure("owner_occupied_units", "B25003_002", "Owner-occupied units"),
    AcsMeasure("renter_occupied_units", "B25003_003", "Renter-occupied units"),
    AcsMeasure("units_in_structure_total", "B25024_001", "Units in structure universe"),
    AcsMeasure("single_family_detached", "B25024_002", "One detached unit"),
    AcsMeasure("single_family_attached", "B25024_003", "One attached unit"),
    AcsMeasure("units_in_2_unit_buildings", "B25024_004", "Two-unit buildings"),
    AcsMeasure("units_in_3_to_4_unit_buildings", "B25024_005", "Three- or four-unit buildings"),
    AcsMeasure("units_in_5_to_9_unit_buildings", "B25024_006", "Five- to nine-unit buildings"),
    AcsMeasure("units_in_10_to_19_unit_buildings", "B25024_007", "Ten- to 19-unit buildings"),
    AcsMeasure("units_in_20_to_49_unit_buildings", "B25024_008", "20- to 49-unit buildings"),
    AcsMeasure("units_in_50_plus_unit_buildings", "B25024_009", "50-or-more-unit buildings"),
    AcsMeasure("mobile_homes", "B25024_010", "Mobile homes"),
    AcsMeasure("boats_rvs_vans_other", "B25024_011", "Boat, RV, van, or other"),
    AcsMeasure("median_household_income", "B19013_001", "Median household income"),
    AcsMeasure("median_owner_occupied_value", "B25077_001", "Median home value"),
    AcsMeasure("median_gross_rent", "B25064_001", "Median gross rent"),
)


@dataclass(frozen=True)
class AcsGroupMetadata:
    """Shared Census metadata for one ACS detailed-table group."""

    concept: str
    universe: str
    unit: str
    group_code: str

    def metadata_url(self, release_year: int) -> str:
        """Return the Census metadata page for this group and release."""

        return (
            f"https://api.census.gov/data/{release_year}/acs/acs5/groups/"
            f"{self.group_code}.html"
        )


ACS_GROUP_METADATA: dict[str, AcsGroupMetadata] = {
    "B01003": AcsGroupMetadata("Total Population", "Total population", "count", "B01003"),
    "B25001": AcsGroupMetadata("Housing Units", "Housing units", "count", "B25001"),
    "B25002": AcsGroupMetadata("Occupancy Status", "Housing units", "count", "B25002"),
    "B25003": AcsGroupMetadata("Tenure", "Occupied housing units", "count", "B25003"),
    "B25024": AcsGroupMetadata("Units in Structure", "Housing units", "count", "B25024"),
    "B19013": AcsGroupMetadata(
        "Median Household Income in the Past 12 Months",
        "Households",
        "inflation-adjusted dollars",
        "B19013",
    ),
    "B25077": AcsGroupMetadata(
        "Median Value (Dollars)",
        "Owner-occupied housing units",
        "dollars",
        "B25077",
    ),
    "B25064": AcsGroupMetadata(
        "Median Gross Rent (Dollars)",
        "Renter-occupied housing units paying cash rent",
        "dollars",
        "B25064",
    ),
}


def national_acs_expected_pairs() -> tuple[tuple[int, str], ...]:
    """Return the required 2010-2024 release-by-state/DC coverage grid."""

    return tuple(
        (release_year, state_fips)
        for release_year in NATIONAL_ACS_RELEASE_YEARS
        for state_fips in NATIONAL_SUPPORTED_STATE_FIPS
    )


def national_acs_expected_source_ids() -> tuple[str, ...]:
    """Return the stable source IDs required for complete national ACS history."""

    return tuple(
        f"acs5_tract_{release_year}_state_{state_fips}"
        for release_year, state_fips in national_acs_expected_pairs()
    )


def acs_measure_dictionary_records(*, release_year: int) -> tuple[dict[str, str | int], ...]:
    """Return one stable, human-readable dictionary row per requested measure."""

    records: list[dict[str, str | int]] = []
    for measure_order, measure in enumerate(ACS_CORE_MEASURES, start=1):
        group = ACS_GROUP_METADATA[measure.group_code]
        records.append(
            {
                "measure_order": measure_order,
                "measure_name": measure.name,
                "group_code": measure.group_code,
                "measure_label": measure.concept,
                "table_concept": group.concept,
                "universe": group.universe,
                "unit": group.unit,
                "estimate_code": measure.estimate_code,
                "margin_of_error_code": measure.margin_of_error_code,
                "metadata_url": group.metadata_url(release_year),
            }
        )
    return tuple(records)


def acs_variable_codes() -> tuple[str, ...]:
    """Return the requested estimate and margin-of-error codes."""

    codes = tuple(
        code
        for measure in ACS_CORE_MEASURES
        for code in (measure.estimate_code, measure.margin_of_error_code)
    )
    if len(codes) + 1 > 50:
        raise ValueError("The ACS request exceeds the 50-variable API limit")
    return codes


def parse_acs_ingestion_scope(
    *,
    release_years: str,
    state_fips_codes: str,
    maximum_requests: int,
) -> AcsIngestionScope:
    """Parse and guard a comma-separated historical ACS job scope."""

    if maximum_requests < 1:
        raise ValueError("maximum_requests must be positive")
    release_tokens = tuple(token.strip() for token in release_years.split(",") if token.strip())
    state_tokens = tuple(token.strip() for token in state_fips_codes.split(",") if token.strip())
    if not release_tokens or not state_tokens:
        raise ValueError("At least one ACS release year and one state FIPS code are required")
    if len(release_tokens) != len(set(release_tokens)):
        raise ValueError("ACS release years must not contain duplicates")
    if len(state_tokens) != len(set(state_tokens)):
        raise ValueError("State FIPS codes must not contain duplicates")

    try:
        parsed_years = tuple(int(token) for token in release_tokens)
    except ValueError as error:
        raise ValueError("ACS release years must be comma-separated integers") from error
    if any(year < 2009 for year in parsed_years):
        raise ValueError("ACS five-year releases begin in 2009")
    if any(len(code) != 2 or not code.isdigit() for code in state_tokens):
        raise ValueError("Every state FIPS code must contain exactly two digits")

    scope = AcsIngestionScope(parsed_years, state_tokens)
    if scope.request_count > maximum_requests:
        raise ValueError(
            f"Requested {scope.request_count} ACS API calls, exceeding this run's "
            f"maximum of {maximum_requests}; split the history into reviewed batches"
        )
    return scope


def build_acs_tract_request(*, release_year: int, state_fips: str, api_key: str) -> SourceRequest:
    """Build one state-level tract request without exposing the key in metadata."""

    if not api_key.strip():
        raise ValueError("A Census API key is required")
    if len(state_fips) != 2 or not state_fips.isdigit():
        raise ValueError("state_fips must contain exactly two digits")
    if release_year < 2009:
        raise ValueError("ACS five-year releases begin in 2009")

    variables = ("NAME", *acs_variable_codes())
    query_items = [
        ("get", ",".join(variables)),
        ("for", "tract:*"),
        ("in", f"state:{state_fips}"),
        ("in", "county:*"),
        ("key", api_key),
    ]
    url = f"https://api.census.gov/data/{release_year}/acs/acs5?{urlencode(query_items)}"
    source = SourceDefinition(
        source_id=f"acs5_tract_{release_year}_state_{state_fips}",
        name=f"{release_year} ACS Five-Year Tract Core Extract, State {state_fips}",
        publisher="U.S. Census Bureau",
        landing_page=("https://www.census.gov/data/developers/data-sets/acs-5year.html"),
        download_url=f"https://api.census.gov/data/{release_year}/acs/acs5",
        file_name=f"acs5_tract_{release_year}_state_{state_fips}.json",
        file_format="json",
        geographic_grain="ACS five-year release by census tract",
        geography_vintage=None,
        intended_use=(
            "Housing mix, tenure, vacancy, affordability, and community context with margins "
            "of error."
        ),
        terms_url="https://www.census.gov/about/policies/open-gov/open-data.html",
        expected_content_types=("application/json", "text/json", "text/plain"),
        minimum_bytes=100,
        limitations=(
            "The release pools 60 months of responses and is not a single-year measurement.",
            "Adjacent releases overlap by four years.",
            "Estimates must remain paired with margins of error and missing-value rules.",
        ),
    )
    return SourceRequest(
        source=source,
        url=url,
        file_name=source.file_name,
        request_parameters={
            "release_year": str(release_year),
            "state_fips": state_fips,
            "geography": "tract:* within county:*",
            "variables": ",".join(variables),
            "key": "[REDACTED]",
        },
        secret_query_parameters=frozenset({"key"}),
        reference_period=f"{release_year - 4}-{release_year}",
    )


def parse_acs_api_payload(payload: str | bytes, *, release_year: int) -> list[dict[str, Any]]:
    """Convert the Census array-of-arrays response into bronze records."""

    decoded = json.loads(payload)
    if not isinstance(decoded, list) or len(decoded) < 2:
        raise ValueError("ACS response must contain a header and at least one data row")
    header = decoded[0]
    if not isinstance(header, list) or not all(isinstance(value, str) for value in header):
        raise ValueError("ACS response header is invalid")
    if len(header) != len(set(header)):
        raise ValueError("ACS response contains duplicate column names")

    required = {"NAME", "state", "county", "tract", *acs_variable_codes()}
    missing = sorted(required.difference(header))
    if missing:
        raise ValueError(f"ACS response is missing required columns: {', '.join(missing)}")

    records: list[dict[str, Any]] = []
    for row_number, row in enumerate(decoded[1:], start=2):
        if not isinstance(row, list) or len(row) != len(header):
            raise ValueError(f"ACS row {row_number} does not match the header width")
        record = dict(zip(header, row, strict=True))
        record["geoid"] = f"{record['state']}{record['county']}{record['tract']}"
        record["acs_release_year"] = release_year
        record["acs_survey_start_year"] = release_year - 4
        record["acs_survey_end_year"] = release_year
        records.append(record)
    return records

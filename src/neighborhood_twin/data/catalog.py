"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Reviewed definitions for the first public data sources used by the project.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceDefinition:
    """Stable metadata and validation rules for one external source."""

    source_id: str
    name: str
    publisher: str
    landing_page: str
    download_url: str
    file_name: str
    file_format: str
    geographic_grain: str
    geography_vintage: str | None
    intended_use: str
    terms_url: str
    expected_content_types: tuple[str, ...]
    minimum_bytes: int
    limitations: tuple[str, ...]


CORE_FILE_SOURCES: dict[str, SourceDefinition] = {
    "fhfa_tract_hpi": SourceDefinition(
        source_id="fhfa_tract_hpi",
        name="Annual Census Tract House Price Index",
        publisher="Federal Housing Finance Agency",
        landing_page="https://www.fhfa.gov/house-price-index",
        download_url="https://www.fhfa.gov/hpi/download/annual/hpi_at_tract.csv",
        file_name="hpi_at_tract.csv",
        file_format="csv",
        geographic_grain="census tract-year",
        geography_vintage=None,
        intended_use="Initial single-family HPI forecast target and market history.",
        terms_url="https://www.fhfa.gov/about/policies",
        expected_content_types=("text/csv", "application/octet-stream"),
        minimum_bytes=1_000_000,
        limitations=(
            "Developmental and not seasonally adjusted.",
            "Represents a filtered single-family market rather than all housing.",
            "Missing values reflect insufficient usable repeat transactions.",
        ),
    ),
    "census_tract_boundaries_2020": SourceDefinition(
        source_id="census_tract_boundaries_2020",
        name="2020 Census Tract Cartographic Boundary File",
        publisher="U.S. Census Bureau",
        landing_page=(
            "https://www.census.gov/geographies/mapping-files/time-series/geo/"
            "cartographic-boundary.2020.html"
        ),
        download_url=("https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_tract_500k.zip"),
        file_name="cb_2020_us_tract_500k.zip",
        file_format="zip/shapefile",
        geographic_grain="2020 census tract",
        geography_vintage="2020",
        intended_use="Map geometry, tract identifiers, and spatial relationships.",
        terms_url="https://www.census.gov/about/policies/open-gov/open-data.html",
        expected_content_types=("application/zip", "application/octet-stream"),
        minimum_bytes=1_000_000,
        limitations=(
            "Cartographic boundaries are simplified for display.",
            "Display geometry should not be used for scientific adjacency without review.",
        ),
    ),
    "census_tract_relationship_2010_2020": SourceDefinition(
        source_id="census_tract_relationship_2010_2020",
        name="National 2020 Census Tract to 2010 Census Tract Relationship File",
        publisher="U.S. Census Bureau",
        landing_page=(
            "https://www.census.gov/geographies/reference-files/time-series/geo/"
            "relationship-files.2020.html"
        ),
        download_url=(
            "https://www2.census.gov/geo/docs/maps-data/data/rel2020/tract/"
            "tab20_tract20_tract10_natl.txt"
        ),
        file_name="tab20_tract20_tract10_natl.txt",
        file_format="pipe-delimited text",
        geographic_grain="2010-to-2020 census tract relationship",
        geography_vintage="2010 and 2020",
        intended_use="Cross-vintage tract diagnostics and geography harmonization.",
        terms_url="https://www.census.gov/about/policies/open-gov/open-data.html",
        expected_content_types=("text/plain", "application/octet-stream"),
        minimum_bytes=1_000_000,
        limitations=(
            "The relationship file does not provide population or housing weights.",
            "Rates, medians, and indexes cannot be allocated as if they were counts.",
        ),
    ),
}


def get_source(source_id: str) -> SourceDefinition:
    """Return a reviewed source definition or raise a useful error."""

    try:
        return CORE_FILE_SOURCES[source_id]
    except KeyError as error:
        known = ", ".join(sorted(CORE_FILE_SOURCES))
        raise KeyError(f"Unknown source_id {source_id!r}. Known sources: {known}") from error

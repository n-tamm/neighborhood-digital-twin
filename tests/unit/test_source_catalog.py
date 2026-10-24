"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

from neighborhood_twin.data.catalog import CORE_FILE_SOURCES, get_source


def test_core_sources_have_https_access_and_terms() -> None:
    assert CORE_FILE_SOURCES
    for source in CORE_FILE_SOURCES.values():
        assert source.landing_page.startswith("https://")
        assert source.download_url.startswith("https://")
        assert source.terms_url.startswith("https://")
        assert source.minimum_bytes > 0


def test_fhfa_uses_current_download_path() -> None:
    source = get_source("fhfa_tract_hpi")
    assert source.download_url.endswith("/hpi/download/annual/hpi_at_tract.csv")


def test_connecticut_bridge_sources_use_reviewed_tiger_vintages() -> None:
    source_2020 = get_source("census_connecticut_tracts_2020")
    source_2024 = get_source("census_connecticut_tracts_2024")
    assert source_2020.geography_vintage == "2020"
    assert source_2024.geography_vintage == "2024"
    assert source_2020.download_url.endswith("/TIGER2020/TRACT/tl_2020_09_tract.zip")
    assert source_2024.download_url.endswith("/TIGER2024/TRACT/tl_2024_09_tract.zip")

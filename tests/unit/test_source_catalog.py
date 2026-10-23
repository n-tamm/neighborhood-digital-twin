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

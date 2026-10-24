"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

from neighborhood_twin.metadata import TABLE_METADATA, column_comment


def test_every_table_metadata_entry_declares_description_and_grain() -> None:
    assert "silver_canonical_tract_2020" in TABLE_METADATA
    for metadata in TABLE_METADATA.values():
        assert metadata.description.endswith(".")
        assert metadata.grain.startswith("One row per")


def test_generated_acs_columns_receive_specific_comments() -> None:
    assert "ACS estimate" in column_comment("population_total_estimate")
    assert "margin of error" in column_comment("population_total_margin_of_error")
    assert "Reason" in column_comment("median_gross_rent_estimate_missing_reason")

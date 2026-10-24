"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

from types import SimpleNamespace

from neighborhood_twin.metadata import TABLE_METADATA, apply_table_metadata, column_comment


def test_every_table_metadata_entry_declares_description_and_grain() -> None:
    assert "silver_canonical_tract_2020" in TABLE_METADATA
    for metadata in TABLE_METADATA.values():
        assert metadata.description.endswith(".")
        assert metadata.grain.startswith("One row per")


def test_generated_acs_columns_receive_specific_comments() -> None:
    assert "ACS estimate" in column_comment("population_total_estimate")
    assert "margin of error" in column_comment("population_total_margin_of_error")
    assert "Reason" in column_comment("median_gross_rent_estimate_missing_reason")


def test_metadata_application_skips_matching_column_comments() -> None:
    fields = [
        SimpleNamespace(name="geoid", metadata={"comment": column_comment("geoid")}),
        SimpleNamespace(name="status", metadata={"comment": "outdated"}),
    ]

    class Catalog:
        @staticmethod
        def tableExists(name: str) -> bool:  # noqa: N802
            return name.endswith(".source_snapshot_manifest")

    class Spark:
        catalog = Catalog()

        def __init__(self) -> None:
            self.statements: list[str] = []

        def table(self, name: str) -> SimpleNamespace:
            return SimpleNamespace(schema=SimpleNamespace(fields=fields))

        def sql(self, statement: str) -> None:
            self.statements.append(statement)

    spark = Spark()
    updated = apply_table_metadata(spark, catalog="workspace", schema="project")

    assert updated == ["workspace.project.source_snapshot_manifest"]
    assert len(spark.statements) == 2
    assert spark.statements[0].startswith("COMMENT ON TABLE")
    assert "ALTER COLUMN `status`" in spark.statements[1]

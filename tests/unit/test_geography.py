"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import pytest

from neighborhood_twin.geography import (
    GEOGRAPHY_SCHEMA_VERSION,
    STABLE_LAND_SHARE_THRESHOLD,
    TRACT_RELATIONSHIP_SILVER_COLUMNS,
    classify_tract_mapping,
    stable_measure_mapping,
)


@pytest.mark.parametrize(
    ("source_targets", "target_sources", "expected"),
    [
        (1, 1, "one_to_one"),
        (2, 1, "split"),
        (1, 2, "merge"),
        (2, 2, "complex"),
    ],
)
def test_classify_tract_mapping_uses_both_edge_degrees(
    source_targets: int,
    target_sources: int,
    expected: str,
) -> None:
    assert classify_tract_mapping(source_targets, target_sources) == expected


def test_stable_measure_mapping_requires_same_geoid_and_two_sided_overlap() -> None:
    assert stable_measure_mapping(
        same_geoid=True,
        source_land_share=0.99,
        target_land_share=0.98,
    )
    assert not stable_measure_mapping(
        same_geoid=False,
        source_land_share=0.99,
        target_land_share=0.99,
    )
    assert not stable_measure_mapping(
        same_geoid=True,
        source_land_share=0.99,
        target_land_share=0.90,
    )


def test_geography_contract_is_stable_and_explicit_about_weight_limits() -> None:
    assert GEOGRAPHY_SCHEMA_VERSION == "1.0.0"
    assert STABLE_LAND_SHARE_THRESHOLD == 0.95
    assert len(TRACT_RELATIONSHIP_SILVER_COLUMNS) == len(set(TRACT_RELATIONSHIP_SILVER_COLUMNS))
    assert "weight_limitation" in TRACT_RELATIONSHIP_SILVER_COLUMNS
    assert "is_stable_measure_mapping" in TRACT_RELATIONSHIP_SILVER_COLUMNS

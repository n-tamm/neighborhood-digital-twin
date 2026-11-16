"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

from __future__ import annotations

import pytest

from neighborhood_twin.similarity_visuals import (
    CASE_MATCH_KEY,
    SIMILARITY_FIGURE_SPECS,
    figure_spec,
    validate_case_records,
    validate_figure_manifest_records,
    validate_selection_methods,
)


def _case_key(rank: int) -> dict[str, object]:
    """Create one small governed case key for known-answer tests."""

    return {
        "query_geoid_2020": "26125144200",
        "query_origin_year": 2025,
        "horizon_years": 3,
        "candidate_geoid_2020": f"000000000{rank:02d}",
        "candidate_origin_year": 2020,
        "match_rank": rank,
    }


def test_figure_specs_have_stable_contiguous_names() -> None:
    assert [spec.sequence for spec in SIMILARITY_FIGURE_SPECS] == [1, 2, 3, 4, 5]
    assert figure_spec(5).file_name == "05_oakland_county_case_study.png"
    with pytest.raises(ValueError, match="Unknown"):
        figure_spec(6)


def test_selection_method_validation_requires_governed_comparators() -> None:
    with pytest.raises(ValueError, match="analogue_inverse_distance_pca"):
        validate_selection_methods(
            [
                "zero_change",
                "state_current_trend",
                "regularized_linear",
                "analogue_inverse_distance_weighted_standardized",
            ]
        )


def test_case_records_reconcile_matches_explanations_and_paths() -> None:
    matches = [_case_key(rank) for rank in (1, 2)]
    explanations = [dict(row) for row in matches]
    trajectories = [
        {
            **row,
            "trajectory_year_offset": offset,
            "is_horizon_endpoint": offset == 3,
            "trajectory_observed": True,
        }
        for row in matches
        for offset in range(4)
    ]
    validate_case_records(
        matches,
        explanations,
        trajectories,
        horizon_years=3,
        top_k=2,
    )
    assert tuple(matches[0]) == CASE_MATCH_KEY


def test_case_validation_rejects_missing_offset() -> None:
    match = _case_key(1)
    trajectories = [
        {
            **match,
            "trajectory_year_offset": offset,
            "is_horizon_endpoint": offset == 3,
            "trajectory_observed": True,
        }
        for offset in (0, 1, 3)
    ]
    with pytest.raises(ValueError, match="every declared offset"):
        validate_case_records(
            [match],
            [dict(match)],
            trajectories,
            horizon_years=3,
            top_k=1,
        )


def test_manifest_validation_requires_complete_lineage() -> None:
    records = [
        {
            "figure_sequence": spec.sequence,
            "figure_file_name": spec.file_name,
            "byte_size": 25_000,
            "similarity_figure_build_id": "build",
            "source_analogue_audit_run_id": "audit",
            "source_analogue_selection_run_id": "selection",
            "source_analogue_tree_run_id": "tree",
            "source_serving_release_id": "release",
        }
        for spec in SIMILARITY_FIGURE_SPECS
    ]
    validate_figure_manifest_records(records)
    records[-1]["source_serving_release_id"] = "other"
    with pytest.raises(ValueError, match="source_serving_release_id"):
        validate_figure_manifest_records(records)

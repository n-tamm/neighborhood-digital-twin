"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

import numpy as np
import pytest

from neighborhood_twin.analogue_serving_retrieval import (
    ANALOGUE_TREE_SCHEMA_VERSION,
    KDTreeConfiguration,
    build_exact_kd_tree,
    format_tract_geoid,
    kd_tree_array_bytes,
    kd_tree_match_key_records,
    kd_tree_scale_metrics,
    query_exact_kd_tree,
    validate_tree_configuration,
    validate_tree_inputs,
)


def _example_arrays():
    candidate_vectors = np.asarray(
        [
            [0.00, 0.00],
            [0.02, 0.00],
            [0.10, 0.00],
            [0.20, 0.00],
            [0.30, 0.00],
            [0.40, 0.00],
            [0.50, 0.00],
        ],
        dtype=np.float64,
    )
    candidate_geoids = np.asarray([1, 1, 2, 3, 4, 5, 6], dtype=np.int64)
    candidate_origin_years = np.asarray(
        [2018, 2020, 2019, 2019, 2019, 2019, 2019], dtype=np.int64
    )
    query_vectors = np.asarray([[0.01, 0.00]], dtype=np.float64)
    query_geoids = np.asarray([1], dtype=np.int64)
    return (
        candidate_vectors,
        candidate_geoids,
        candidate_origin_years,
        query_vectors,
        query_geoids,
    )


def test_tree_contract_and_configuration_validation() -> None:
    assert ANALOGUE_TREE_SCHEMA_VERSION == "1.0.0"
    validate_tree_configuration(KDTreeConfiguration(), top_k=10)
    with pytest.raises(ValueError, match="leaf_size"):
        validate_tree_configuration(KDTreeConfiguration(leaf_size=0), top_k=10)
    with pytest.raises(ValueError, match="initial_neighbors"):
        validate_tree_configuration(KDTreeConfiguration(initial_neighbors=4), top_k=10)
    with pytest.raises(ValueError, match="expansion_factor"):
        validate_tree_configuration(KDTreeConfiguration(expansion_factor=1), top_k=10)


def test_kd_tree_returns_exact_distinct_nonself_tracts() -> None:
    (
        candidate_vectors,
        candidate_geoids,
        candidate_origin_years,
        query_vectors,
        query_geoids,
    ) = _example_arrays()
    tree, build_seconds = build_exact_kd_tree(candidate_vectors, leaf_size=2)
    result = query_exact_kd_tree(
        tree,
        candidate_geoids,
        candidate_origin_years,
        query_vectors,
        query_geoids,
        top_k=3,
        configuration=KDTreeConfiguration(leaf_size=2, initial_neighbors=3),
    )

    selected_geoids = candidate_geoids[result.neighbors.candidate_indices[0]].tolist()
    assert selected_geoids == [2, 3, 4]
    assert result.neighbors.expansion_counts[0] >= 1
    assert result.neighbors.retrieved_state_counts[0] > 3
    assert result.distance_computation_count > 0
    assert result.query_elapsed_seconds >= 0
    assert build_seconds >= 0
    assert kd_tree_array_bytes(tree) > candidate_vectors.nbytes


def test_kd_tree_keeps_the_closest_state_for_each_candidate_tract() -> None:
    candidate_vectors = np.asarray(
        [[0.10], [0.20], [0.15], [0.30], [0.40]], dtype=np.float64
    )
    candidate_geoids = np.asarray([2, 2, 3, 4, 5], dtype=np.int64)
    candidate_origin_years = np.asarray([2017, 2020, 2019, 2019, 2019], dtype=np.int64)
    query_vectors = np.asarray([[0.00]], dtype=np.float64)
    query_geoids = np.asarray([1], dtype=np.int64)
    tree, _ = build_exact_kd_tree(candidate_vectors, leaf_size=2)

    result = query_exact_kd_tree(
        tree,
        candidate_geoids,
        candidate_origin_years,
        query_vectors,
        query_geoids,
        top_k=3,
        configuration=KDTreeConfiguration(leaf_size=2, initial_neighbors=4),
    )

    selected = result.neighbors.candidate_indices[0]
    assert candidate_geoids[selected].tolist() == [2, 3, 4]
    assert candidate_origin_years[selected].tolist() == [2017, 2019, 2019]


def test_kd_tree_matches_exhaustive_distinct_ranking_for_multiple_queries() -> None:
    """Compare the indexed result with the declared exhaustive ordering."""

    generator = np.random.default_rng(699)
    candidate_vectors = generator.normal(size=(240, 4)).astype(np.float64)
    candidate_geoids = np.repeat(np.arange(100, 180), 3).astype(np.int64)
    candidate_origin_years = np.tile(np.asarray([2017, 2019, 2021]), 80)
    query_vectors = generator.normal(size=(8, 4)).astype(np.float64)
    query_geoids = np.asarray([100, 101, 500, 501, 502, 503, 504, 505], dtype=np.int64)
    tree, _ = build_exact_kd_tree(candidate_vectors, leaf_size=8)

    result = query_exact_kd_tree(
        tree,
        candidate_geoids,
        candidate_origin_years,
        query_vectors,
        query_geoids,
        top_k=10,
        configuration=KDTreeConfiguration(leaf_size=8, initial_neighbors=12),
    )

    for query_position, query_vector in enumerate(query_vectors):
        distances = np.linalg.norm(candidate_vectors - query_vector, axis=1)
        best_by_tract: dict[int, tuple[float, int, int, int]] = {}
        for candidate_position, distance in enumerate(distances):
            geoid = int(candidate_geoids[candidate_position])
            if geoid == int(query_geoids[query_position]):
                continue
            candidate = (
                float(distance),
                -int(candidate_origin_years[candidate_position]),
                geoid,
                candidate_position,
            )
            if geoid not in best_by_tract or candidate < best_by_tract[geoid]:
                best_by_tract[geoid] = candidate
        expected_positions = [item[3] for item in sorted(best_by_tract.values())[:10]]
        assert result.neighbors.candidate_indices[query_position].tolist() == expected_positions


def test_tree_input_validation_rejects_misaligned_or_nonfinite_arrays() -> None:
    (
        candidate_vectors,
        candidate_geoids,
        candidate_origin_years,
        query_vectors,
        query_geoids,
    ) = _example_arrays()
    validate_tree_inputs(
        candidate_vectors,
        candidate_geoids,
        candidate_origin_years,
        query_vectors,
        query_geoids,
        top_k=3,
    )
    with pytest.raises(ValueError, match="candidate_geoids"):
        validate_tree_inputs(
            candidate_vectors,
            candidate_geoids[:-1],
            candidate_origin_years,
            query_vectors,
            query_geoids,
            top_k=3,
        )
    invalid_queries = query_vectors.copy()
    invalid_queries[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        validate_tree_inputs(
            candidate_vectors,
            candidate_geoids,
            candidate_origin_years,
            invalid_queries,
            query_geoids,
            top_k=3,
        )


def test_tree_records_and_scale_metrics_preserve_lineage_keys() -> None:
    (
        candidate_vectors,
        candidate_geoids,
        candidate_origin_years,
        query_vectors,
        query_geoids,
    ) = _example_arrays()
    tree, _ = build_exact_kd_tree(candidate_vectors, leaf_size=2)
    result = query_exact_kd_tree(
        tree,
        candidate_geoids,
        candidate_origin_years,
        query_vectors,
        query_geoids,
        top_k=3,
        configuration=KDTreeConfiguration(leaf_size=2, initial_neighbors=3),
    )

    records = kd_tree_match_key_records(
        result,
        query_geoids,
        candidate_geoids,
        candidate_origin_years,
        query_origin_year=2025,
        horizon_years=1,
    )
    metrics = kd_tree_scale_metrics(
        result,
        horizon_years=1,
        sample_name="unit_sample",
        candidate_state_count=len(candidate_geoids),
    )

    assert format_tract_geoid(1) == "00000000001"
    assert len(records) == 3
    assert records[0]["query_origin_year"] == 2025
    assert records[0]["candidate_geoid_2020"] == "00000000002"
    assert metrics["query_count"] == 1
    assert metrics["distance_computation_ratio"] > 0

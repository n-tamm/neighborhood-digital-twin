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
    kd_tree_array_bytes,
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

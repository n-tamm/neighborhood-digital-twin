"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Exact indexed retrieval utilities for current-neighborhood historical analogues.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np
from numpy.typing import NDArray

ANALOGUE_TREE_SCHEMA_VERSION = "1.0.0"
ANALOGUE_TREE_MATCH_TABLE = "analogue_tree_benchmark_match"
ANALOGUE_TREE_QUERY_EVALUATION_TABLE = "analogue_tree_query_evaluation"
ANALOGUE_TREE_SUMMARY_TABLE = "analogue_tree_summary"
ANALOGUE_TREE_SCALE_TABLE = "analogue_tree_scale_benchmark"
ANALOGUE_TREE_RETRIEVAL_CONFIG = "exact_kd_tree"

FloatMatrix = NDArray[np.float64]
IntMatrix = NDArray[np.int64]
IntVector = NDArray[np.int64]
FloatVector = NDArray[np.float64]


@dataclass(frozen=True)
class KDTreeConfiguration:
    """Settings for exact KD-tree construction and distinct-community retrieval."""

    leaf_size: int = 40
    initial_neighbors: int = 64
    expansion_factor: int = 2
    tie_tolerance: float = 1e-12
    query_batch_size: int = 250


DEFAULT_KD_TREE_CONFIGURATION = KDTreeConfiguration()


@dataclass(frozen=True)
class DistinctNeighborResult:
    """Ranked candidate states and work diagnostics for every query vector."""

    candidate_indices: IntMatrix
    distances: FloatMatrix
    retrieved_state_counts: IntVector
    expansion_counts: IntVector


@dataclass(frozen=True)
class KDTreeQueryResult:
    """Distinct-neighbor results plus measured query work and elapsed time."""

    neighbors: DistinctNeighborResult
    distance_computation_count: int
    query_elapsed_seconds: float


def format_tract_geoid(value: int) -> str:
    """Format a numeric U.S. census tract identifier as an 11-character GEOID."""

    if value < 0 or value > 99_999_999_999:
        raise ValueError("tract GEOID integers must fit within eleven decimal digits")
    return f"{value:011d}"


def validate_tree_configuration(configuration: KDTreeConfiguration, *, top_k: int) -> None:
    """Reject settings that cannot produce a stable distinct-community top-k."""

    if top_k < 3:
        raise ValueError("top_k must be at least three")
    if configuration.leaf_size <= 0:
        raise ValueError("leaf_size must be positive")
    if configuration.initial_neighbors < top_k:
        raise ValueError("initial_neighbors must be at least top_k")
    if configuration.expansion_factor < 2:
        raise ValueError("expansion_factor must be at least two")
    if configuration.tie_tolerance < 0:
        raise ValueError("tie_tolerance must not be negative")
    if configuration.query_batch_size <= 0:
        raise ValueError("query_batch_size must be positive")


def validate_tree_inputs(
    candidate_vectors: FloatMatrix,
    candidate_geoids: IntVector,
    candidate_origin_years: IntVector,
    query_vectors: FloatMatrix,
    query_geoids: IntVector,
    *,
    top_k: int,
) -> None:
    """Validate aligned, finite vector and identifier arrays before index construction."""

    if candidate_vectors.ndim != 2 or query_vectors.ndim != 2:
        raise ValueError("candidate_vectors and query_vectors must be two-dimensional")
    if candidate_vectors.shape[1] != query_vectors.shape[1]:
        raise ValueError("candidate and query vector dimensions must match")
    if candidate_vectors.shape[0] != len(candidate_geoids):
        raise ValueError("candidate_geoids must align with candidate_vectors")
    if candidate_vectors.shape[0] != len(candidate_origin_years):
        raise ValueError("candidate_origin_years must align with candidate_vectors")
    if query_vectors.shape[0] != len(query_geoids):
        raise ValueError("query_geoids must align with query_vectors")
    if candidate_vectors.shape[0] < top_k:
        raise ValueError("the candidate matrix contains fewer rows than top_k")
    if query_vectors.shape[0] == 0:
        raise ValueError("at least one query vector is required")
    if not np.isfinite(candidate_vectors).all() or not np.isfinite(query_vectors).all():
        raise ValueError("candidate and query vectors must contain only finite values")


def build_exact_kd_tree(candidate_vectors: FloatMatrix, *, leaf_size: int) -> tuple[Any, float]:
    """Build an exact Euclidean KD-tree and return it with measured build time."""

    from sklearn.neighbors import KDTree  # type: ignore[import-untyped]

    if leaf_size <= 0:
        raise ValueError("leaf_size must be positive")
    if candidate_vectors.ndim != 2 or candidate_vectors.shape[0] == 0:
        raise ValueError("candidate_vectors must be a nonempty two-dimensional matrix")
    if not np.isfinite(candidate_vectors).all():
        raise ValueError("candidate_vectors must contain only finite values")
    started = perf_counter()
    tree = KDTree(candidate_vectors, leaf_size=leaf_size, metric="euclidean")
    return tree, perf_counter() - started


def kd_tree_array_bytes(tree: Any) -> int:
    """Return bytes used by the NumPy arrays that make up a fitted scikit-learn KD-tree."""

    return int(sum(np.asarray(array).nbytes for array in tree.get_arrays()))


def _rank_retrieved_states(
    indices: IntVector,
    distances: FloatVector,
    *,
    query_geoid: int,
    candidate_geoids: IntVector,
    candidate_origin_years: IntVector,
) -> list[tuple[float, int, int, int]]:
    """Collapse retrieved states to each tract's best year and apply deterministic ranking."""

    best_by_tract: dict[int, tuple[float, int, int, int]] = {}
    for index, distance in zip(indices.tolist(), distances.tolist(), strict=True):
        geoid = int(candidate_geoids[index])
        if geoid == query_geoid:
            continue
        origin_year = int(candidate_origin_years[index])
        candidate = (float(distance), -origin_year, geoid, int(index))
        current = best_by_tract.get(geoid)
        if current is None or candidate < current:
            best_by_tract[geoid] = candidate
    return sorted(best_by_tract.values())


def rank_distinct_kd_tree_neighbors(
    tree: Any,
    candidate_geoids: IntVector,
    candidate_origin_years: IntVector,
    query_vectors: FloatMatrix,
    query_geoids: IntVector,
    *,
    top_k: int,
    configuration: KDTreeConfiguration = DEFAULT_KD_TREE_CONFIGURATION,
) -> DistinctNeighborResult:
    """Return the exact top-k distinct tracts while expanding through distance-boundary ties."""

    validate_tree_configuration(configuration, top_k=top_k)
    candidate_count = len(candidate_geoids)
    if candidate_count != len(candidate_origin_years):
        raise ValueError("candidate identifiers and origin years must align")
    if query_vectors.ndim != 2 or len(query_geoids) != query_vectors.shape[0]:
        raise ValueError("query identifiers and vectors must align")
    if candidate_count < top_k:
        raise ValueError("the candidate index contains fewer rows than top_k")

    query_count = query_vectors.shape[0]
    selected_indices = np.full((query_count, top_k), -1, dtype=np.int64)
    selected_distances = np.full((query_count, top_k), np.nan, dtype=np.float64)
    retrieved_counts = np.zeros(query_count, dtype=np.int64)
    expansion_counts = np.zeros(query_count, dtype=np.int64)
    pending = np.arange(query_count, dtype=np.int64)
    requested = min(configuration.initial_neighbors, candidate_count)

    while len(pending):
        distances, indices = tree.query(
            query_vectors[pending],
            k=requested,
            return_distance=True,
            dualtree=False,
            breadth_first=False,
            sort_results=True,
        )
        unresolved: list[int] = []
        for row_position, query_position_value in enumerate(pending.tolist()):
            query_position = int(query_position_value)
            ranked = _rank_retrieved_states(
                np.asarray(indices[row_position], dtype=np.int64),
                np.asarray(distances[row_position], dtype=np.float64),
                query_geoid=int(query_geoids[query_position]),
                candidate_geoids=candidate_geoids,
                candidate_origin_years=candidate_origin_years,
            )
            retrieved_counts[query_position] = requested
            if len(ranked) < top_k:
                if requested == candidate_count:
                    raise ValueError(
                        "fewer than top_k distinct non-self candidate tracts are available"
                    )
                unresolved.append(query_position)
                expansion_counts[query_position] += 1
                continue

            cutoff = ranked[top_k - 1][0]
            farthest_retrieved = float(distances[row_position, -1])
            boundary_is_complete = (
                requested == candidate_count
                or farthest_retrieved > cutoff + configuration.tie_tolerance
            )
            if not boundary_is_complete:
                unresolved.append(query_position)
                expansion_counts[query_position] += 1
                continue

            selected = ranked[:top_k]
            selected_distances[query_position] = np.asarray(
                [item[0] for item in selected], dtype=np.float64
            )
            selected_indices[query_position] = np.asarray(
                [item[3] for item in selected], dtype=np.int64
            )

        if not unresolved:
            break
        if requested == candidate_count:
            raise RuntimeError("KD-tree retrieval could not resolve all queries")
        pending = np.asarray(unresolved, dtype=np.int64)
        requested = min(candidate_count, requested * configuration.expansion_factor)

    if (selected_indices < 0).any() or not np.isfinite(selected_distances).all():
        raise RuntimeError("KD-tree retrieval left an incomplete query result")
    return DistinctNeighborResult(
        candidate_indices=selected_indices,
        distances=selected_distances,
        retrieved_state_counts=retrieved_counts,
        expansion_counts=expansion_counts,
    )


def query_exact_kd_tree(
    tree: Any,
    candidate_geoids: IntVector,
    candidate_origin_years: IntVector,
    query_vectors: FloatMatrix,
    query_geoids: IntVector,
    *,
    top_k: int,
    configuration: KDTreeConfiguration = DEFAULT_KD_TREE_CONFIGURATION,
) -> KDTreeQueryResult:
    """Measure batched exact retrieval without overflowing the tree's distance-call counter."""

    validate_tree_configuration(configuration, top_k=top_k)
    if query_vectors.ndim != 2 or len(query_geoids) != query_vectors.shape[0]:
        raise ValueError("query identifiers and vectors must align")
    if len(query_geoids) == 0:
        raise ValueError("at least one query vector is required")
    started = perf_counter()
    neighbor_batches = []
    distance_computation_count = 0
    for start in range(0, len(query_geoids), configuration.query_batch_size):
        stop = min(start + configuration.query_batch_size, len(query_geoids))
        tree.reset_n_calls()
        neighbor_batches.append(
            rank_distinct_kd_tree_neighbors(
                tree,
                candidate_geoids,
                candidate_origin_years,
                query_vectors[start:stop],
                query_geoids[start:stop],
                top_k=top_k,
                configuration=configuration,
            )
        )
        batch_calls = int(tree.get_n_calls())
        if batch_calls < 0:
            raise OverflowError(
                "KD-tree distance-call counter overflowed within one query batch"
            )
        distance_computation_count += batch_calls
    neighbors = DistinctNeighborResult(
        candidate_indices=np.concatenate(
            [batch.candidate_indices for batch in neighbor_batches], axis=0
        ),
        distances=np.concatenate([batch.distances for batch in neighbor_batches], axis=0),
        retrieved_state_counts=np.concatenate(
            [batch.retrieved_state_counts for batch in neighbor_batches]
        ),
        expansion_counts=np.concatenate(
            [batch.expansion_counts for batch in neighbor_batches]
        ),
    )
    elapsed = perf_counter() - started
    return KDTreeQueryResult(
        neighbors=neighbors,
        distance_computation_count=distance_computation_count,
        query_elapsed_seconds=elapsed,
    )


def kd_tree_match_key_records(
    result: KDTreeQueryResult,
    query_geoids: IntVector,
    candidate_geoids: IntVector,
    candidate_origin_years: IntVector,
    *,
    query_origin_year: int,
    horizon_years: int,
) -> list[dict[str, int | float | str]]:
    """Convert ranked array positions into stable Spark-ready query and candidate keys."""

    query_count, top_k = result.neighbors.candidate_indices.shape
    if len(query_geoids) != query_count:
        raise ValueError("query_geoids must align with the neighbor result")
    records: list[dict[str, int | float | str]] = []
    for query_position in range(query_count):
        for rank_position in range(top_k):
            candidate_position = int(
                result.neighbors.candidate_indices[query_position, rank_position]
            )
            records.append(
                {
                    "query_geoid_2020": format_tract_geoid(
                        int(query_geoids[query_position])
                    ),
                    "query_origin_year": int(query_origin_year),
                    "horizon_years": int(horizon_years),
                    "candidate_geoid_2020": format_tract_geoid(
                        int(candidate_geoids[candidate_position])
                    ),
                    "candidate_origin_year": int(
                        candidate_origin_years[candidate_position]
                    ),
                    "similarity_distance": float(
                        result.neighbors.distances[query_position, rank_position]
                    ),
                    "match_rank": rank_position + 1,
                    "retrieved_state_count": int(
                        result.neighbors.retrieved_state_counts[query_position]
                    ),
                    "tree_expansion_count": int(
                        result.neighbors.expansion_counts[query_position]
                    ),
                }
            )
    return records


def kd_tree_scale_metrics(
    result: KDTreeQueryResult,
    *,
    horizon_years: int,
    sample_name: str,
    candidate_state_count: int,
) -> dict[str, int | float | str]:
    """Summarize measured indexed work for a declared current-query sample."""

    query_count = result.neighbors.candidate_indices.shape[0]
    if not sample_name.strip():
        raise ValueError("sample_name must not be blank")
    if candidate_state_count <= 0 or query_count <= 0:
        raise ValueError("candidate and query counts must be positive")
    possible_pair_count = candidate_state_count * query_count
    seconds = result.query_elapsed_seconds
    return {
        "horizon_years": int(horizon_years),
        "sample_name": sample_name,
        "query_count": query_count,
        "candidate_state_count": int(candidate_state_count),
        "possible_pair_count": int(possible_pair_count),
        "distance_computation_count": int(result.distance_computation_count),
        "distance_computation_ratio": (
            result.distance_computation_count / possible_pair_count
        ),
        "query_elapsed_seconds": float(seconds),
        "queries_per_second": query_count / seconds if seconds > 0 else 0.0,
        "mean_retrieved_state_count": float(
            np.mean(result.neighbors.retrieved_state_counts)
        ),
        "maximum_retrieved_state_count": int(
            np.max(result.neighbors.retrieved_state_counts)
        ),
        "expanded_query_share": float(
            np.mean(result.neighbors.expansion_counts > 0)
        ),
        "maximum_tree_expansion_count": int(
            np.max(result.neighbors.expansion_counts)
        ),
    }

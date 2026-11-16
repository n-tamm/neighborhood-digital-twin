"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Governed contracts for the similarity communication figure set.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

SIMILARITY_FIGURE_COUNT = 5
DEFAULT_CASE_QUERY_GEOID = "26125144200"
DEFAULT_CASE_HORIZON_YEARS = 3
DEFAULT_CASE_TOP_K = 10


@dataclass(frozen=True)
class SimilarityFigureSpec:
    """Stable identity and plain-language purpose for one governed similarity figure."""

    sequence: int
    stem: str
    title: str
    purpose: str

    @property
    def file_name(self) -> str:
        """Return the stable PNG file name used inside each versioned build."""

        return f"{self.sequence:02d}_{self.stem}.png"


SIMILARITY_FIGURE_SPECS = (
    SimilarityFigureSpec(
        1,
        "similarity_workflow",
        "How a current neighborhood is matched with earlier communities",
        "Explains the governed feature, preprocessing, time-safety, retrieval, and outcome flow.",
    ),
    SimilarityFigureSpec(
        2,
        "similarity_stability_and_selection",
        "Why weighted standardized matching was selected",
        "Combines neighbor-list stability with the weighted-versus-PCA validation comparison.",
    ),
    SimilarityFigureSpec(
        3,
        "analogue_outcome_utility",
        "Historical analogues add context but not the strongest point forecast",
        "Compares analogue later-outcome error with transparent forecast comparators.",
    ),
    SimilarityFigureSpec(
        4,
        "current_analogue_coverage",
        "Historical analogue availability is broad but not universal",
        "Shows supported tracts and explicit unavailable-result reasons at each horizon.",
    ),
    SimilarityFigureSpec(
        5,
        "oakland_county_case_study",
        "One current Michigan neighborhood and its historical analogues",
        "Locates the matches, explains the closest result, and shows observed later paths.",
    ),
)

REQUIRED_SELECTION_METHODS = frozenset(
    {
        "zero_change",
        "state_current_trend",
        "regularized_linear",
        "analogue_inverse_distance_weighted_standardized",
        "analogue_inverse_distance_pca",
    }
)

CASE_MATCH_KEY = (
    "query_geoid_2020",
    "query_origin_year",
    "horizon_years",
    "candidate_geoid_2020",
    "candidate_origin_year",
    "match_rank",
)


def figure_spec(sequence: int) -> SimilarityFigureSpec:
    """Return one governed figure specification by sequence number."""

    for spec in SIMILARITY_FIGURE_SPECS:
        if spec.sequence == sequence:
            return spec
    raise ValueError(f"Unknown similarity figure sequence: {sequence}")


def validate_selection_methods(available_methods: Sequence[str]) -> None:
    """Require every method needed for the outcome and representation comparisons."""

    missing = REQUIRED_SELECTION_METHODS - set(available_methods)
    if missing:
        raise ValueError("Similarity scorecard is missing methods: " + ", ".join(sorted(missing)))


def _row_key(row: Mapping[str, object]) -> tuple[object, ...]:
    """Build the governed query-to-candidate key from a collected serving row."""

    return tuple(row.get(column) for column in CASE_MATCH_KEY)


def validate_case_records(
    matches: Sequence[Mapping[str, object]],
    explanations: Sequence[Mapping[str, object]],
    trajectories: Sequence[Mapping[str, object]],
    *,
    horizon_years: int,
    top_k: int,
) -> None:
    """Reconcile a case-study extract before any presentation figure is rendered."""

    if len(matches) != top_k:
        raise ValueError(f"Case study requires {top_k} matches, found {len(matches)}")
    ranks = {int(str(row["match_rank"])) for row in matches}
    if ranks != set(range(1, top_k + 1)):
        raise ValueError("Case-study match ranks are incomplete")
    match_keys = {_row_key(row) for row in matches}
    explanation_keys = {_row_key(row) for row in explanations}
    if explanation_keys != match_keys or len(explanations) != top_k:
        raise ValueError("Case-study explanations do not reconcile one-to-one with matches")
    expected_offsets = set(range(horizon_years + 1))
    path_offsets: dict[tuple[object, ...], set[int]] = {key: set() for key in match_keys}
    endpoint_counts: dict[tuple[object, ...], int] = {key: 0 for key in match_keys}
    for row in trajectories:
        key = _row_key(row)
        if key not in path_offsets:
            raise ValueError("Case-study trajectory contains a match outside the selected top-k")
        offset = int(str(row["trajectory_year_offset"]))
        if offset in path_offsets[key]:
            raise ValueError("Case-study trajectory contains a duplicate year offset")
        path_offsets[key].add(offset)
        if bool(row["is_horizon_endpoint"]):
            endpoint_counts[key] += 1
            if not bool(row["trajectory_observed"]):
                raise ValueError("Case-study trajectory endpoint is not observed")
    if any(offsets != expected_offsets for offsets in path_offsets.values()):
        raise ValueError("Case-study trajectories do not contain every declared offset")
    if any(count != 1 for count in endpoint_counts.values()):
        raise ValueError("Case-study trajectories do not contain one endpoint per match")


def validate_figure_manifest_records(
    records: Sequence[Mapping[str, object]],
    *,
    minimum_byte_size: int = 20_000,
) -> None:
    """Validate figure identity, lineage, and file-size evidence before publication."""

    if len(records) != SIMILARITY_FIGURE_COUNT:
        raise ValueError(
            f"Expected {SIMILARITY_FIGURE_COUNT} similarity figures, found {len(records)}"
        )
    by_sequence = {int(str(row["figure_sequence"])): row for row in records}
    if set(by_sequence) != set(range(1, SIMILARITY_FIGURE_COUNT + 1)):
        raise ValueError("Similarity figure sequences must be unique and contiguous")
    for spec in SIMILARITY_FIGURE_SPECS:
        row = by_sequence[spec.sequence]
        if row.get("figure_file_name") != spec.file_name:
            raise ValueError(f"Unexpected file name for figure {spec.sequence}")
        if int(str(row["byte_size"])) < minimum_byte_size:
            raise ValueError(f"Figure {spec.file_name} is unexpectedly small")
    lineage_fields = (
        "similarity_figure_build_id",
        "source_analogue_audit_run_id",
        "source_analogue_selection_run_id",
        "source_analogue_tree_run_id",
        "source_serving_release_id",
    )
    for field in lineage_fields:
        values = {str(row.get(field) or "") for row in records}
        if len(values) != 1 or "" in values:
            raise ValueError(f"Similarity figure manifest has inconsistent {field}")

"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

from datetime import UTC, datetime

import pytest

from neighborhood_twin.validate import (
    ACS_SPECIAL_VALUES,
    QualityMetric,
    hard_failures,
    new_quality_run_id,
)


def _metric(status: str) -> QualityMetric:
    return QualityMetric(
        quality_run_id="20261023T120000000000Z",
        profiled_at_utc="2026-10-23T12:00:00.000000Z",
        table_name="workspace.neighborhood_twin_dev.example",
        metric_group="integrity",
        metric_name="example_count",
        dimension="all",
        metric_value=0.0,
        status=status,
        expectation="= 0",
        notes="",
    )


def test_quality_run_id_normalizes_to_utc() -> None:
    run_id, timestamp = new_quality_run_id(
        datetime(2026, 10, 23, 12, 0, tzinfo=UTC)
    )

    assert run_id == "20261023T120000000000Z"
    assert timestamp == "2026-10-23T12:00:00.000000Z"


def test_quality_run_id_requires_timezone() -> None:
    with pytest.raises(ValueError, match="timezone"):
        new_quality_run_id(datetime(2026, 10, 23, 12, 0))


def test_quality_metric_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="Unsupported quality status"):
        _metric("unknown")


def test_hard_failures_excludes_warnings_and_information() -> None:
    assert hard_failures([_metric("pass"), _metric("warn"), _metric("info")]) == []
    assert hard_failures([_metric("fail")]) == [_metric("fail")]


def test_census_special_values_include_estimate_and_moe_placeholders() -> None:
    assert -666_666_666 in ACS_SPECIAL_VALUES
    assert -555_555_555 in ACS_SPECIAL_VALUES
    assert -222_222_222 in ACS_SPECIAL_VALUES

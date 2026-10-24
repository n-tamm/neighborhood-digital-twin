"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5
"""

from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request

import pytest

from neighborhood_twin.data.acquisition import (
    SourceRequest,
    acquire_http_snapshot,
    register_existing_snapshot,
)
from neighborhood_twin.data.catalog import SourceDefinition
from neighborhood_twin.data.manifest import SourceManifest


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body
        self._position = 0
        self.status = 200
        self.headers = {
            "Content-Type": "text/csv; charset=utf-8",
            "ETag": '"fixture"',
            "Last-Modified": "Wed, 21 Oct 2026 12:00:00 GMT",
        }

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, size: int) -> bytes:
        if self._position >= len(self._body):
            return b""
        chunk = self._body[self._position : self._position + size]
        self._position += len(chunk)
        return chunk


def _source() -> SourceDefinition:
    return SourceDefinition(
        source_id="fixture",
        name="Fixture source",
        publisher="Fixture publisher",
        landing_page="https://example.org/landing",
        download_url="https://example.org/data.csv",
        file_name="data.csv",
        file_format="csv",
        geographic_grain="fixture row",
        geography_vintage=None,
        intended_use="Test acquisition.",
        terms_url="https://example.org/terms",
        expected_content_types=("text/csv",),
        minimum_bytes=1,
        limitations=("Fixture only.",),
    )


def test_acquisition_hashes_places_and_redacts_snapshot(tmp_path: Path) -> None:
    body = b"id,value\n1,2\n"
    request = SourceRequest(
        source=_source(),
        url="https://example.org/data.csv?key=secret-value&year=2024",
        file_name="data.csv",
        request_parameters={"key": "[REDACTED]", "year": "2024"},
        secret_query_parameters=frozenset({"key"}),
        reference_period="2024",
    )

    def opener(http_request: Request, *, timeout: int) -> FakeResponse:
        assert timeout == 30
        assert http_request.full_url.endswith("key=secret-value&year=2024")
        return FakeResponse(body)

    manifest = acquire_http_snapshot(
        request,
        tmp_path,
        retrieved_at=datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc),  # noqa: UP017
        timeout_seconds=30,
        opener=opener,
    )

    snapshot_path = Path(manifest.file_path)
    assert snapshot_path.read_bytes() == body
    assert manifest.sha256[:16] in manifest.snapshot_id
    assert "secret-value" not in manifest.endpoint
    assert "key=%5BREDACTED%5D" in manifest.endpoint
    assert snapshot_path.with_name("data.csv.manifest.json").exists()


def test_acquisition_requires_timezone(tmp_path: Path) -> None:
    request = SourceRequest(
        source=_source(), url="https://example.org/data.csv", file_name="data.csv"
    )
    with pytest.raises(ValueError, match="timezone"):
        acquire_http_snapshot(
            request,
            tmp_path,
            retrieved_at=datetime(2026, 10, 22),
            opener=lambda *_args, **_kwargs: FakeResponse(b"x"),
        )


def test_manual_registration_preserves_upload_and_records_method(tmp_path: Path) -> None:
    uploaded_path = tmp_path / "incoming" / "data.csv"
    uploaded_path.parent.mkdir()
    uploaded_path.write_bytes(b"id,value\n1,2\n")
    destination_root = tmp_path / "volume"
    request = SourceRequest(
        source=_source(), url="https://example.org/data.csv", file_name="data.csv"
    )

    manifest = register_existing_snapshot(
        request,
        uploaded_path,
        destination_root,
        retrieved_at=datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc),  # noqa: UP017
    )

    assert uploaded_path.exists()
    assert Path(manifest.file_path).read_bytes() == uploaded_path.read_bytes()
    assert manifest.request_parameters["acquisition_method"] == "manual_upload"
    assert manifest.validation_status == "registered"


def test_manifest_sidecar_round_trip_preserves_tuple_fields(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    request = SourceRequest(
        source=_source(), url="https://example.org/data.csv", file_name="data.csv"
    )
    manifest = acquire_http_snapshot(
        request,
        tmp_path / "volume",
        retrieved_at=datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc),  # noqa: UP017
        opener=lambda *_args, **_kwargs: FakeResponse(b"id,value\n1,2\n"),
    )
    manifest.write_json(manifest_path)

    restored = SourceManifest.read_json(manifest_path)

    assert restored == manifest
    assert isinstance(restored.known_limitations, tuple)
    assert isinstance(restored.validation_messages, tuple)

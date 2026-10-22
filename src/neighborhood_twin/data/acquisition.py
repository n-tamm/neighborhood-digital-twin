"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Content-addressed HTTP acquisition for local paths and Unity Catalog volumes.
"""

import hashlib
import os
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from neighborhood_twin import __version__
from neighborhood_twin.data.catalog import SourceDefinition, get_source
from neighborhood_twin.data.manifest import SourceManifest


class AcquisitionError(RuntimeError):
    """Raised when a response cannot be accepted as a source snapshot."""


@dataclass(frozen=True)
class SourceRequest:
    """One concrete request derived from a stable source definition."""

    source: SourceDefinition
    url: str
    file_name: str
    request_parameters: Mapping[str, str] = field(default_factory=dict)
    secret_query_parameters: frozenset[str] = field(default_factory=frozenset)
    reference_period: str | None = None
    publication_date: str | None = None


def request_for_static_source(source_id: str) -> SourceRequest:
    """Build a request for a catalog source with one stable download URL."""

    source = get_source(source_id)
    return SourceRequest(source=source, url=source.download_url, file_name=source.file_name)


def redact_url(url: str, secret_parameters: frozenset[str]) -> str:
    """Remove query-secret values before a URL enters a manifest or log."""

    if not secret_parameters:
        return url
    parts = urlsplit(url)
    redacted_query = [
        (key, "[REDACTED]" if key in secret_parameters else value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
    ]
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(redacted_query), parts.fragment)
    )


def _header(response: Any, name: str) -> str | None:
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    return headers.get(name)


def _status(response: Any) -> int:
    status = getattr(response, "status", None)
    if status is None:
        status = response.getcode()
    return int(status)


def _validate_response(request: SourceRequest, response: Any) -> tuple[int, str | None]:
    status = _status(response)
    if status < 200 or status >= 300:
        raise AcquisitionError(f"{request.source.source_id} returned HTTP {status}")

    content_type = _header(response, "Content-Type")
    base_content_type = content_type.split(";", maxsplit=1)[0].strip() if content_type else None
    expected = request.source.expected_content_types
    if base_content_type and expected and base_content_type not in expected:
        raise AcquisitionError(
            f"{request.source.source_id} returned {base_content_type!r}; expected one of {expected}"
        )
    return status, content_type


def acquire_http_snapshot(
    request: SourceRequest,
    destination_root: Path,
    *,
    retrieved_at: datetime | None = None,
    timeout_seconds: int = 120,
    chunk_size: int = 1024 * 1024,
    opener: Callable[..., Any] = urlopen,
) -> SourceManifest:
    """Download, validate, hash, and immutably place one raw source object."""

    retrieved_at = retrieved_at or datetime.now(timezone.utc)  # noqa: UP017
    if retrieved_at.tzinfo is None:
        raise ValueError("retrieved_at must include a timezone")

    source_root = destination_root / "bronze" / request.source.source_id
    staging_root = destination_root / "_staging" / request.source.source_id
    staging_root.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None

    http_request = Request(
        request.url,
        headers={"User-Agent": "neighborhood-digital-twin/0.1 (academic capstone)"},
    )
    try:
        with opener(http_request, timeout=timeout_seconds) as response:
            status, content_type = _validate_response(request, response)
            hasher = hashlib.sha256()
            byte_size = 0
            with tempfile.NamedTemporaryFile(
                mode="wb", delete=False, dir=staging_root, prefix="download-"
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    temporary_file.write(chunk)
                    hasher.update(chunk)
                    byte_size += len(chunk)

            if byte_size < request.source.minimum_bytes:
                raise AcquisitionError(
                    f"{request.source.source_id} returned {byte_size:,} bytes; "
                    f"expected at least {request.source.minimum_bytes:,}"
                )

            sha256 = hasher.hexdigest()
            retrieval_date = retrieved_at.date().isoformat()
            snapshot_directory = source_root / f"retrieval_date={retrieval_date}" / sha256[:16]
            snapshot_directory.mkdir(parents=True, exist_ok=True)
            snapshot_path = snapshot_directory / request.file_name
            if snapshot_path.exists():
                temporary_path.unlink()
            else:
                os.replace(temporary_path, snapshot_path)
            temporary_path = None

            timestamp = retrieved_at.astimezone(timezone.utc).isoformat()  # noqa: UP017
            snapshot_id = f"{request.source.source_id}:{retrieval_date}:{sha256[:16]}"
            manifest = SourceManifest(
                snapshot_id=snapshot_id,
                source_id=request.source.source_id,
                source_name=request.source.name,
                publisher=request.source.publisher,
                landing_page=request.source.landing_page,
                endpoint=redact_url(request.url, request.secret_query_parameters),
                request_parameters=dict(request.request_parameters),
                reference_period=request.reference_period,
                publication_date=request.publication_date,
                retrieval_timestamp_utc=timestamp,
                geographic_grain=request.source.geographic_grain,
                geography_vintage=request.source.geography_vintage,
                file_format=request.source.file_format,
                file_path=str(snapshot_path),
                byte_size=byte_size,
                sha256=sha256,
                http_status=status,
                content_type=content_type,
                etag=_header(response, "ETag"),
                last_modified=_header(response, "Last-Modified"),
                terms_url=request.source.terms_url,
                known_limitations=request.source.limitations,
                code_version=__version__,
            )
            manifest.write_sidecar()
            return manifest
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

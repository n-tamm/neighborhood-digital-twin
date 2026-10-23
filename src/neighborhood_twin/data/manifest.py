"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Serializable lineage record for an immutable source snapshot.
"""

import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SourceManifest:
    """Lineage and validation metadata for one acquired source object."""

    snapshot_id: str
    source_id: str
    source_name: str
    publisher: str
    landing_page: str
    endpoint: str
    request_parameters: dict[str, str]
    reference_period: str | None
    publication_date: str | None
    retrieval_timestamp_utc: str
    geographic_grain: str
    geography_vintage: str | None
    file_format: str
    file_path: str
    byte_size: int
    sha256: str
    http_status: int
    content_type: str | None
    etag: str | None
    last_modified: str | None
    terms_url: str
    known_limitations: tuple[str, ...]
    code_version: str
    row_count: int | None = None
    schema_fingerprint: str | None = None
    validation_status: str = "acquired"
    validation_messages: tuple[str, ...] = field(default_factory=tuple)

    def with_profile(
        self,
        *,
        row_count: int,
        schema_fingerprint: str,
        validation_status: str,
        validation_messages: tuple[str, ...] = (),
    ) -> "SourceManifest":
        """Return a copy populated with parse and validation results."""

        return replace(
            self,
            row_count=row_count,
            schema_fingerprint=schema_fingerprint,
            validation_status=validation_status,
            validation_messages=validation_messages,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible dictionary."""

        value = asdict(self)
        value["known_limitations"] = list(self.known_limitations)
        value["validation_messages"] = list(self.validation_messages)
        return value

    def to_spark_record(self) -> dict[str, Any]:
        """Flatten nested fields so Spark can append a stable Delta record."""

        value = self.to_dict()
        value["request_parameters_json"] = json.dumps(
            value.pop("request_parameters"), sort_keys=True
        )
        value["known_limitations_json"] = json.dumps(value.pop("known_limitations"))
        value["validation_messages_json"] = json.dumps(value.pop("validation_messages"))
        return value

    def write_json(self, path: Path) -> None:
        """Atomically write the manifest beside its raw source object."""

        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(f"{path.suffix}.tmp")
        temporary_path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)

    def write_sidecar(self) -> None:
        """Write the conventional manifest path next to the raw payload."""

        source_path = Path(self.file_path)
        self.write_json(source_path.with_name(f"{source_path.name}.manifest.json"))

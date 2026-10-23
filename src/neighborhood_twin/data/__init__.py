"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Public interfaces for source discovery and acquisition.
"""

from neighborhood_twin.data.acquisition import (
    AcquisitionError,
    SourceRequest,
    acquire_http_snapshot,
    register_existing_snapshot,
    request_for_static_source,
)
from neighborhood_twin.data.catalog import CORE_FILE_SOURCES, SourceDefinition, get_source
from neighborhood_twin.data.manifest import SourceManifest

__all__ = [
    "AcquisitionError",
    "CORE_FILE_SOURCES",
    "SourceDefinition",
    "SourceManifest",
    "SourceRequest",
    "acquire_http_snapshot",
    "get_source",
    "register_existing_snapshot",
    "request_for_static_source",
]

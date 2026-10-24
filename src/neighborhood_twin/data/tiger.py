"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Small reader for reviewed state tract TIGER/Line archives.
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TIGER_TRACT_FIELDS = (
    "STATEFP",
    "COUNTYFP",
    "TRACTCE",
    "GEOID",
    "NAME",
    "NAMELSAD",
    "MTFCC",
    "FUNCSTAT",
    "ALAND",
    "AWATER",
    "INTPTLAT",
    "INTPTLON",
)


@dataclass(frozen=True)
class TigerTractArchive:
    """Selected tract attributes from one TIGER/Line shapefile archive."""

    rows: list[dict[str, Any]]
    archive_stem: str


def read_tiger_tract_archive(path: Path) -> TigerTractArchive:
    """Read only the governed attributes needed for tract identity reconciliation."""

    try:
        import shapefile  # type: ignore[import-not-found]
    except ImportError as error:
        raise RuntimeError("TIGER tract parsing requires the pinned pyshp dependency") from error

    with zipfile.ZipFile(path) as zipped:
        shapefile_members = sorted(name for name in zipped.namelist() if name.endswith(".shp"))
        if len(shapefile_members) != 1:
            raise ValueError(
                "Expected exactly one shapefile in TIGER tract archive; "
                f"found {shapefile_members}"
            )
        stem = shapefile_members[0][:-4]
        required = {f"{stem}{extension}" for extension in (".shp", ".shx", ".dbf")}
        missing = sorted(required - set(zipped.namelist()))
        if missing:
            raise ValueError(f"TIGER tract archive is missing required members: {missing}")

        reader = shapefile.Reader(
            shp=io.BytesIO(zipped.read(f"{stem}.shp")),
            shx=io.BytesIO(zipped.read(f"{stem}.shx")),
            dbf=io.BytesIO(zipped.read(f"{stem}.dbf")),
            encoding="utf-8",
        )
        available_fields = tuple(field[0] for field in reader.fields[1:])
        missing_fields = sorted(set(TIGER_TRACT_FIELDS) - set(available_fields))
        if missing_fields:
            raise ValueError(f"TIGER tract attributes are missing fields: {missing_fields}")

        rows = []
        for record in reader.iterRecords():
            source = record.as_dict()
            rows.append({field: source[field] for field in TIGER_TRACT_FIELDS})
    return TigerTractArchive(rows=rows, archive_stem=stem)

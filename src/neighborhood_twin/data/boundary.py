"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Reader for the registered 2020 Census tract cartographic-boundary archive.
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BOUNDARY_STEM = "cb_2020_us_tract_500k"
BOUNDARY_ATTRIBUTE_FIELDS = (
    "STATEFP",
    "COUNTYFP",
    "TRACTCE",
    "AFFGEOID",
    "GEOID",
    "NAME",
    "NAMELSAD",
    "STUSPS",
    "NAMELSADCO",
    "STATE_NAME",
    "LSAD",
    "ALAND",
    "AWATER",
)
BOUNDARY_REQUIRED_EXTENSIONS = (".shp", ".shx", ".dbf", ".prj")


@dataclass(frozen=True)
class BoundaryArchive:
    """Parsed source rows and archive-level metadata."""

    rows: list[dict[str, Any]]
    crs_wkt: str


def valid_boundary_identity(
    *, state_fips: str, county_fips: str, tract_code: str, geoid: str
) -> bool:
    """Check the Census hierarchy encoded by a tract GEOID."""

    return (
        len(state_fips) == 2
        and state_fips.isdigit()
        and len(county_fips) == 3
        and county_fips.isdigit()
        and len(tract_code) == 6
        and tract_code.isdigit()
        and geoid == f"{state_fips}{county_fips}{tract_code}"
    )


def read_boundary_archive(path: Path) -> BoundaryArchive:
    """Read the reviewed zipped shapefile into typed records with WKB geometry."""

    try:
        import shapefile  # type: ignore[import-not-found]
        from shapely.geometry import shape  # type: ignore[import-not-found,import-untyped]
    except ImportError as error:
        raise RuntimeError(
            "Boundary parsing requires the pinned pyshp and Shapely job dependencies"
        ) from error

    with zipfile.ZipFile(path) as zipped:
        names = set(zipped.namelist())
        required = {f"{BOUNDARY_STEM}{extension}" for extension in BOUNDARY_REQUIRED_EXTENSIONS}
        missing = sorted(required - names)
        if missing:
            raise ValueError(f"Boundary archive is missing required members: {missing}")

        reader = shapefile.Reader(
            shp=io.BytesIO(zipped.read(f"{BOUNDARY_STEM}.shp")),
            shx=io.BytesIO(zipped.read(f"{BOUNDARY_STEM}.shx")),
            dbf=io.BytesIO(zipped.read(f"{BOUNDARY_STEM}.dbf")),
            encoding="utf-8",
        )
        fields = tuple(field[0] for field in reader.fields[1:])
        if fields != BOUNDARY_ATTRIBUTE_FIELDS:
            raise ValueError(
                "Census tract boundary attributes changed: "
                f"expected={BOUNDARY_ATTRIBUTE_FIELDS}, actual={fields}"
            )

        rows: list[dict[str, Any]] = []
        for source in reader.iterShapeRecords():
            attributes = source.record.as_dict()
            geometry = shape(source.shape.__geo_interface__)
            minimum_x, minimum_y, maximum_x, maximum_y = geometry.bounds
            rows.append(
                {
                    **attributes,
                    "GEOMETRY_WKB": bytes(geometry.wkb),
                    "GEOMETRY_TYPE": geometry.geom_type,
                    "GEOMETRY_IS_VALID": bool(geometry.is_valid),
                    "GEOMETRY_IS_EMPTY": bool(geometry.is_empty),
                    "MINIMUM_LONGITUDE": float(minimum_x),
                    "MINIMUM_LATITUDE": float(minimum_y),
                    "MAXIMUM_LONGITUDE": float(maximum_x),
                    "MAXIMUM_LATITUDE": float(maximum_y),
                }
            )
        crs_wkt = zipped.read(f"{BOUNDARY_STEM}.prj").decode("utf-8").strip()
    return BoundaryArchive(rows=rows, crs_wkt=crs_wkt)

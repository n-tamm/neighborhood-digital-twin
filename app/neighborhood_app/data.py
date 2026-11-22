"""
AI Assistance:
OpenAI ChatGPT was used for code debugging, code generation, code/repo organization,
and code methodological brainstorming. All final modeling, implementation,
validation, commentary, and interpretation were performed and verified by the authors.
Model used: GPT-5

Typed configuration, contract validation, and read-only data access for the application.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import pandas as pd

SUPPORTED_HORIZONS = (1, 3)
REQUIRED_RELEASE_COMPONENTS = frozenset(
    {
        "serving_analogue_availability_current",
        "serving_analogue_summary_current",
        "serving_analogue_match_current",
        "serving_analogue_explanation_current",
        "serving_analogue_trajectory_current",
    }
)
REQUIRED_FORECAST_RELEASE_COMPONENTS = frozenset(
    {"serving_forecast_current", "serving_forecast_availability_current"}
)
GEOID_PATTERN = re.compile(r"^[0-9]{11}$")
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class AppSettings:
    """Environment-backed application configuration with validated SQL identifiers."""

    data_mode: str = "sample"
    catalog: str = "workspace"
    gold_schema: str = "neighborhood_twin_gold"
    silver_schema: str = "neighborhood_twin_silver"
    serving_schema: str = "neighborhood_twin_serving"
    warehouse_id: str | None = None
    sample_path: Path | None = None

    @classmethod
    def from_environment(cls) -> AppSettings:
        """Build settings from environment variables without reading credentials directly."""

        app_root = Path(__file__).resolve().parents[1]
        mode = os.getenv("NEIGHBORHOOD_TWIN_DATA_MODE", "sample").strip().lower()
        return cls(
            data_mode=mode,
            catalog=os.getenv("NEIGHBORHOOD_TWIN_CATALOG", "workspace"),
            gold_schema=os.getenv("NEIGHBORHOOD_TWIN_GOLD_SCHEMA", "neighborhood_twin_gold"),
            silver_schema=os.getenv("NEIGHBORHOOD_TWIN_SILVER_SCHEMA", "neighborhood_twin_silver"),
            serving_schema=os.getenv(
                "NEIGHBORHOOD_TWIN_SERVING_SCHEMA", "neighborhood_twin_serving"
            ),
            warehouse_id=os.getenv("DATABRICKS_WAREHOUSE_ID"),
            sample_path=app_root / "sample_data" / "autauga_demo.json",
        )

    def validate(self) -> None:
        """Reject unsupported modes, unsafe SQL identifiers, or incomplete live settings."""

        if self.data_mode not in {"live", "sample"}:
            raise ValueError("NEIGHBORHOOD_TWIN_DATA_MODE must be 'live' or 'sample'.")
        for label, value in (
            ("catalog", self.catalog),
            ("gold_schema", self.gold_schema),
            ("silver_schema", self.silver_schema),
            ("serving_schema", self.serving_schema),
        ):
            if not IDENTIFIER_PATTERN.fullmatch(value):
                raise ValueError(f"Unsafe SQL identifier configured for {label}.")
        if self.data_mode == "live" and not self.warehouse_id:
            raise ValueError("Live mode requires DATABRICKS_WAREHOUSE_ID.")
        if self.data_mode == "sample" and (
            self.sample_path is None or not self.sample_path.exists()
        ):
            raise ValueError("Sample mode requires the committed application demonstration file.")


@dataclass(frozen=True)
class NeighborhoodData:
    """All current, historical, and analogue evidence needed for one selected tract."""

    release: Mapping[str, Any]
    profile: Mapping[str, Any]
    bounds: Mapping[str, Any]
    map_context: pd.DataFrame
    history: pd.DataFrame
    availability: pd.DataFrame
    summaries: pd.DataFrame
    matches: pd.DataFrame
    trajectories: pd.DataFrame
    forecast_release: Mapping[str, Any]
    forecast_availability: pd.DataFrame
    forecasts: pd.DataFrame
    data_mode: str

    def horizon_available(self, horizon_years: int) -> bool:
        """Return whether the selected tract has a complete analogue result for a horizon."""

        rows = self.availability.loc[
            self.availability["horizon_years"] == horizon_years, "analogue_available"
        ]
        return bool(rows.iloc[0]) if not rows.empty else False

    def forecast_horizon_available(self, horizon_years: int) -> bool:
        """Return whether an approved current forecast exists for the horizon."""

        if self.forecast_availability.empty:
            return False
        rows = self.forecast_availability.loc[
            self.forecast_availability["horizon_years"] == horizon_years,
            "forecast_available",
        ]
        return bool(rows.iloc[0]) if not rows.empty else False


class NeighborhoodRepository(Protocol):
    """Read-only repository contract used by the Streamlit interface."""

    def search_places(self, search_text: str, limit: int = 12) -> pd.DataFrame:
        """Return matching current tract identities in display order."""

    def list_states(self) -> pd.DataFrame:
        """Return current state coverage used by the geographic browser."""

    def list_counties(self, state_abbreviation: str) -> pd.DataFrame:
        """Return counties and tract coverage for one selected state."""

    def list_tracts(self, county_geoid: str) -> pd.DataFrame:
        """Return current tract identities for one selected county."""

    def load_neighborhood(self, geoid_2020: str) -> NeighborhoodData:
        """Return the complete approved application evidence for one tract."""


class QueryExecutor(Protocol):
    """Minimal SQL execution contract that keeps connector details out of query logic."""

    def fetch_frame(
        self, statement: str, parameters: Mapping[str, Any] | None = None
    ) -> pd.DataFrame:
        """Execute a read-only statement and return named columns."""

    def fetch_frames(
        self,
        queries: Sequence[tuple[str, Mapping[str, Any] | None]],
    ) -> list[pd.DataFrame]:
        """Execute several read-only statements over one warehouse connection."""


class DatabricksSqlExecutor:
    """Read-only Databricks SQL executor using the app service principal when deployed."""

    def __init__(self, warehouse_id: str) -> None:
        self._warehouse_id = warehouse_id

    def fetch_frame(
        self, statement: str, parameters: Mapping[str, Any] | None = None
    ) -> pd.DataFrame:
        """Execute parameterized SQL and convert rows to a pandas frame."""

        return self.fetch_frames([(statement, parameters)])[0]

    def fetch_frames(
        self,
        queries: Sequence[tuple[str, Mapping[str, Any] | None]],
    ) -> list[pd.DataFrame]:
        """Execute a query group on one connection to avoid repeated startup latency."""

        from databricks import sql
        from databricks.sdk.core import Config

        config = Config()
        hostname = config.host.removeprefix("https://").removeprefix("http://")
        http_path = f"/sql/1.0/warehouses/{self._warehouse_id}"
        frames: list[pd.DataFrame] = []
        with sql.connect(
            server_hostname=hostname,
            http_path=http_path,
            credentials_provider=lambda: config.authenticate,
            _use_arrow_native_complex_types=False,
        ) as connection:
            with connection.cursor() as cursor:
                for statement, parameters in queries:
                    cursor.execute(statement, parameters=parameters or {})
                    rows = cursor.fetchall()
                    description = cursor.description
                    if description is None:
                        raise RuntimeError("The Databricks SQL query did not return a result set.")
                    columns = [item[0] for item in description]
                    frames.append(pd.DataFrame.from_records(rows, columns=columns))
        return frames


class DatabricksNeighborhoodRepository:
    """Application repository that reads only approved serving and compact profile tables."""

    def __init__(self, settings: AppSettings, executor: QueryExecutor) -> None:
        settings.validate()
        self._settings = settings
        self._executor = executor
        self._release = self._load_active_release()
        self._forecast_release = self._load_active_forecast_release()

    def _table(self, schema: str, table: str) -> str:
        return f"{self._settings.catalog}.{schema}.{table}"

    def _load_active_release(self) -> dict[str, Any]:
        manifest = self._executor.fetch_frame(
            f"""
            SELECT *
            FROM {self._table(self._settings.serving_schema, "serving_release_manifest")}
            WHERE component_name = 'historical_analogues'
              AND release_status = 'validated'
            ORDER BY serving_built_at_utc DESC, serving_release_id DESC
            """
        )
        if manifest.empty:
            raise RuntimeError("No validated historical-analogue release is available.")
        for release_id in manifest["serving_release_id"].drop_duplicates():
            candidate = manifest.loc[manifest["serving_release_id"] == release_id]
            components = set(candidate["table_name"].astype(str))
            if REQUIRED_RELEASE_COMPONENTS.issubset(components):
                first = candidate.iloc[0].to_dict()
                first["component_count"] = len(components)
                return first
        raise RuntimeError("No validated serving release contains all five required components.")

    def _load_active_forecast_release(self) -> dict[str, Any]:
        """Select the newest complete forecast release, or retain an explicit pending state."""

        manifest = self._executor.fetch_frame(
            f"""
            SELECT *
            FROM {self._table(self._settings.serving_schema, "serving_release_manifest")}
            WHERE component_name = 'forecasts'
              AND release_status = 'validated'
            ORDER BY serving_built_at_utc DESC, serving_release_id DESC
            """
        )
        if manifest.empty:
            return {}
        for release_id in manifest["serving_release_id"].drop_duplicates():
            candidate = manifest.loc[manifest["serving_release_id"] == release_id]
            components = set(candidate["table_name"].astype(str))
            if REQUIRED_FORECAST_RELEASE_COMPONENTS.issubset(components):
                first = candidate.iloc[0].to_dict()
                first["component_count"] = len(components)
                return first
        return {}

    def search_places(self, search_text: str, limit: int = 12) -> pd.DataFrame:
        """Search readable tract context and both active model-availability contracts."""

        cleaned = " ".join(search_text.strip().split())
        if not cleaned:
            cleaned = "01001020300"
        if len(cleaned) > 80:
            raise ValueError("Place search is limited to 80 characters.")
        availability_table = self._table(
            self._settings.serving_schema,
            "serving_analogue_availability_current",
        )
        forecast_availability_table = self._table(
            self._settings.serving_schema,
            "serving_forecast_availability_current",
        )
        profile_table = self._table(
            self._settings.gold_schema,
            "gold_tract_profile_current",
        )
        forecast_release_id = str(self._forecast_release.get("serving_release_id", "unpublished"))
        return self._executor.fetch_frame(
            f"""
            SELECT DISTINCT
              a.geoid_2020,
              a.state_abbreviation,
              a.state_name,
              a.county_name,
              a.tract_name,
              a.analogue_available,
              coalesce(f.forecast_available, false) AS forecast_available,
              p.population_total_estimate,
              p.housing_units_total_estimate
            FROM {availability_table} a
            LEFT JOIN {forecast_availability_table} f
              ON a.geoid_2020 = f.geoid_2020
             AND f.serving_release_id = :forecast_release_id
             AND f.horizon_years = 1
            LEFT JOIN {profile_table} p
              ON a.geoid_2020 = p.geoid_2020
            WHERE a.serving_release_id = :release_id
              AND a.horizon_years = 1
              AND (
                a.geoid_2020 = :exact_text
                OR lower(a.county_name) LIKE :search_pattern
                OR lower(a.state_name) LIKE :search_pattern
                OR lower(concat(a.county_name, ', ', a.state_abbreviation, ' ', a.tract_name))
                   LIKE :search_pattern
              )
            ORDER BY
              forecast_available DESC,
              a.analogue_available DESC,
              a.state_abbreviation,
              a.county_name,
              a.tract_name
            LIMIT {int(limit)}
            """,
            {
                "release_id": self._release["serving_release_id"],
                "forecast_release_id": forecast_release_id,
                "exact_text": cleaned,
                "search_pattern": f"%{cleaned.lower()}%",
            },
        )

    def list_states(self) -> pd.DataFrame:
        """Summarize current tract, analogue, and approved forecast coverage by state."""

        availability_table = self._table(
            self._settings.serving_schema,
            "serving_analogue_availability_current",
        )
        forecast_availability_table = self._table(
            self._settings.serving_schema,
            "serving_forecast_availability_current",
        )
        forecast_release_id = str(self._forecast_release.get("serving_release_id", "unpublished"))
        return self._executor.fetch_frame(
            f"""
            WITH analogue AS (
              SELECT *
              FROM {availability_table}
              WHERE serving_release_id = :release_id
                AND horizon_years = 1
            ),
            forecast AS (
              SELECT geoid_2020, forecast_available
              FROM {forecast_availability_table}
              WHERE serving_release_id = :forecast_release_id
                AND horizon_years = 1
            )
            SELECT
              a.state_fips,
              a.state_abbreviation,
              a.state_name,
              count(DISTINCT a.geoid_2020) AS tract_count,
              count(DISTINCT CASE WHEN a.analogue_available THEN a.geoid_2020 END)
                AS analogue_ready_tract_count,
              count(DISTINCT CASE WHEN a.analogue_available THEN a.geoid_2020 END)
                / count(DISTINCT a.geoid_2020) AS analogue_ready_share,
              count(DISTINCT CASE WHEN f.forecast_available THEN a.geoid_2020 END)
                AS forecast_ready_tract_count,
              count(DISTINCT CASE WHEN f.forecast_available THEN a.geoid_2020 END)
                / count(DISTINCT a.geoid_2020) AS forecast_ready_share
            FROM analogue a
            LEFT JOIN forecast f ON a.geoid_2020 = f.geoid_2020
            WHERE a.state_abbreviation IS NOT NULL
              AND a.state_name IS NOT NULL
              AND CAST(a.state_fips AS INT) <= 56
            GROUP BY a.state_fips, a.state_abbreviation, a.state_name
            ORDER BY a.state_name
            """,
            {
                "release_id": self._release["serving_release_id"],
                "forecast_release_id": forecast_release_id,
            },
        )

    def list_counties(self, state_abbreviation: str) -> pd.DataFrame:
        """List county-level tract and model coverage without loading analytical outputs."""

        cleaned = state_abbreviation.strip().upper()
        if len(cleaned) != 2 or not cleaned.isalpha():
            raise ValueError("A state abbreviation must contain exactly two letters.")
        availability_table = self._table(
            self._settings.serving_schema,
            "serving_analogue_availability_current",
        )
        forecast_availability_table = self._table(
            self._settings.serving_schema,
            "serving_forecast_availability_current",
        )
        forecast_release_id = str(self._forecast_release.get("serving_release_id", "unpublished"))
        return self._executor.fetch_frame(
            f"""
            WITH analogue AS (
              SELECT *
              FROM {availability_table}
              WHERE serving_release_id = :release_id
                AND horizon_years = 1
                AND state_abbreviation = :state_abbreviation
            ),
            forecast AS (
              SELECT geoid_2020, forecast_available
              FROM {forecast_availability_table}
              WHERE serving_release_id = :forecast_release_id
                AND horizon_years = 1
            )
            SELECT
              a.county_geoid,
              a.county_name,
              a.state_abbreviation,
              count(DISTINCT a.geoid_2020) AS tract_count,
              count(DISTINCT CASE WHEN a.analogue_available THEN a.geoid_2020 END)
                AS analogue_ready_tract_count,
              count(DISTINCT CASE WHEN f.forecast_available THEN a.geoid_2020 END)
                AS forecast_ready_tract_count
            FROM analogue a
            LEFT JOIN forecast f ON a.geoid_2020 = f.geoid_2020
            GROUP BY a.county_geoid, a.county_name, a.state_abbreviation
            ORDER BY a.county_name, a.county_geoid
            """,
            {
                "release_id": self._release["serving_release_id"],
                "forecast_release_id": forecast_release_id,
                "state_abbreviation": cleaned,
            },
        )

    def list_tracts(self, county_geoid: str) -> pd.DataFrame:
        """List readable tract context and both model-availability flags within one county."""

        cleaned = county_geoid.strip()
        if len(cleaned) != 5 or not cleaned.isdigit():
            raise ValueError("A county GEOID must contain exactly five digits.")
        availability_table = self._table(
            self._settings.serving_schema,
            "serving_analogue_availability_current",
        )
        forecast_availability_table = self._table(
            self._settings.serving_schema,
            "serving_forecast_availability_current",
        )
        profile_table = self._table(
            self._settings.gold_schema,
            "gold_tract_profile_current",
        )
        forecast_release_id = str(self._forecast_release.get("serving_release_id", "unpublished"))
        return self._executor.fetch_frame(
            f"""
            SELECT DISTINCT
              a.geoid_2020,
              a.state_abbreviation,
              a.state_name,
              a.county_geoid,
              a.county_name,
              a.tract_name,
              a.analogue_available,
              coalesce(f.forecast_available, false) AS forecast_available,
              p.population_total_estimate,
              p.housing_units_total_estimate
            FROM {availability_table} a
            LEFT JOIN {forecast_availability_table} f
              ON a.geoid_2020 = f.geoid_2020
             AND f.serving_release_id = :forecast_release_id
             AND f.horizon_years = 1
            LEFT JOIN {profile_table} p
              ON a.geoid_2020 = p.geoid_2020
            WHERE a.serving_release_id = :release_id
              AND a.horizon_years = 1
              AND a.county_geoid = :county_geoid
            ORDER BY a.tract_name, a.geoid_2020
            """,
            {
                "release_id": self._release["serving_release_id"],
                "forecast_release_id": forecast_release_id,
                "county_geoid": cleaned,
            },
        )

    def load_neighborhood(self, geoid_2020: str) -> NeighborhoodData:
        """Read the selected tract without performing model inference or broad table scans."""

        if not GEOID_PATTERN.fullmatch(geoid_2020):
            raise ValueError("A census tract GEOID must contain exactly 11 digits.")
        release_id = str(self._release["serving_release_id"])
        common = {"geoid": geoid_2020, "release_id": release_id}
        availability_table = self._table(
            self._settings.serving_schema,
            "serving_analogue_availability_current",
        )
        match_table = self._table(
            self._settings.serving_schema,
            "serving_analogue_match_current",
        )
        explanation_table = self._table(
            self._settings.serving_schema,
            "serving_analogue_explanation_current",
        )
        geometry_table = self._table(
            self._settings.silver_schema,
            "silver_tract_display_geometry_2020",
        )
        profile_query = f"""
            SELECT *
            FROM {self._table(self._settings.gold_schema, "gold_tract_profile_current")}
            WHERE geoid_2020 = :geoid
            """
        map_context_query = f"""
            WITH selected AS (
              SELECT
                minimum_longitude,
                minimum_latitude,
                maximum_longitude,
                maximum_latitude,
                (minimum_longitude + maximum_longitude) / 2.0 AS center_longitude,
                (minimum_latitude + maximum_latitude) / 2.0 AS center_latitude
              FROM {geometry_table}
              WHERE geoid_2020 = :geoid
            )
            SELECT
              g.geoid_2020,
              g.state_abbreviation,
              g.county_name,
              g.tract_name,
              g.land_area_sqm,
              g.minimum_longitude,
              g.minimum_latitude,
              g.maximum_longitude,
              g.maximum_latitude,
              g.geography_build_id,
              st_asgeojson(st_geomfromwkb(g.geometry_wkb, 4326)) AS geometry_geojson
            FROM {geometry_table} g
            CROSS JOIN selected s
            WHERE g.maximum_longitude >= s.minimum_longitude
                    - greatest((s.maximum_longitude - s.minimum_longitude) * 2.0, 0.03)
              AND g.minimum_longitude <= s.maximum_longitude
                    + greatest((s.maximum_longitude - s.minimum_longitude) * 2.0, 0.03)
              AND g.maximum_latitude >= s.minimum_latitude
                    - greatest((s.maximum_latitude - s.minimum_latitude) * 2.0, 0.03)
              AND g.minimum_latitude <= s.maximum_latitude
                    + greatest((s.maximum_latitude - s.minimum_latitude) * 2.0, 0.03)
            ORDER BY
              pow(
                ((g.minimum_longitude + g.maximum_longitude) / 2.0) - s.center_longitude,
                2
              ) + pow(
                ((g.minimum_latitude + g.maximum_latitude) / 2.0) - s.center_latitude,
                2
              )
            LIMIT 80
            """
        history_query = f"""
            SELECT
              h.observation_year,
              h.annual_change_pct,
              h.hpi,
              h.hpi_available,
              h.annual_change_available,
              h.silver_build_id
            FROM {self._table(self._settings.silver_schema, "silver_fhfa_tract_year")} h
            LEFT JOIN {
                self._table(
                    self._settings.silver_schema,
                    "silver_connecticut_tract_bridge_2020_2024",
                )
            } b
              ON h.geoid = b.geoid_current
            WHERE coalesce(b.geoid_2020, h.geoid) = :geoid
            ORDER BY h.observation_year
            """
        availability_query = f"""
            SELECT *
            FROM {availability_table}
            WHERE geoid_2020 = :geoid AND serving_release_id = :release_id
            ORDER BY horizon_years
            """
        summary_query = f"""
            SELECT *
            FROM {self._table(self._settings.serving_schema, "serving_analogue_summary_current")}
            WHERE query_geoid_2020 = :geoid AND serving_release_id = :release_id
            ORDER BY horizon_years
            """
        match_query = f"""
            SELECT
              m.horizon_years, m.candidate_geoid_2020, m.candidate_origin_year,
              m.candidate_target_end_year, m.candidate_state_abbreviation,
              m.candidate_state_name, m.candidate_county_name, m.candidate_tract_name,
              m.candidate_target_annualized_change_pct, m.similarity_distance, m.match_rank,
              m.candidate_age_years, m.serving_release_id,
              e.community_scale_mean_absolute_standardized_gap,
              e.occupancy_tenure_mean_absolute_standardized_gap,
              e.housing_structure_mean_absolute_standardized_gap,
              e.affordability_mean_absolute_standardized_gap,
              e.market_trajectory_mean_absolute_standardized_gap,
              e.strongest_shared_family_display_name, e.strongest_shared_family_gap,
              e.largest_difference_family_display_name, e.largest_difference_family_gap,
              e.strongest_shared_feature_display_name, e.strongest_shared_query_value,
              e.strongest_shared_candidate_value, e.largest_difference_feature_display_name,
              e.largest_difference_query_value, e.largest_difference_candidate_value,
              e.query_imputed_feature_count, e.candidate_imputed_feature_count,
              (g.minimum_longitude + g.maximum_longitude) / 2.0 AS candidate_longitude,
              (g.minimum_latitude + g.maximum_latitude) / 2.0 AS candidate_latitude,
              g.land_area_sqm AS candidate_land_area_sqm,
              g.minimum_longitude AS candidate_minimum_longitude,
              g.minimum_latitude AS candidate_minimum_latitude,
              g.maximum_longitude AS candidate_maximum_longitude,
              g.maximum_latitude AS candidate_maximum_latitude,
              st_asgeojson(st_geomfromwkb(g.geometry_wkb, 4326)) AS candidate_geometry_geojson
            FROM {match_table} m
            LEFT JOIN {explanation_table} e
              ON m.serving_release_id = e.serving_release_id
             AND m.query_geoid_2020 = e.query_geoid_2020
             AND m.horizon_years = e.horizon_years
             AND m.candidate_geoid_2020 = e.candidate_geoid_2020
             AND m.candidate_origin_year = e.candidate_origin_year
             AND m.match_rank = e.match_rank
            LEFT JOIN {geometry_table} g
              ON m.candidate_geoid_2020 = g.geoid_2020
            WHERE m.query_geoid_2020 = :geoid AND m.serving_release_id = :release_id
            ORDER BY m.horizon_years, m.match_rank
            """
        trajectory_query = f"""
            SELECT *
            FROM {self._table(self._settings.serving_schema, "serving_analogue_trajectory_current")}
            WHERE query_geoid_2020 = :geoid AND serving_release_id = :release_id
            ORDER BY horizon_years, match_rank, trajectory_year_offset
            """
        queries: list[tuple[str, Mapping[str, Any] | None]] = [
            (profile_query, {"geoid": geoid_2020}),
            (map_context_query, {"geoid": geoid_2020}),
            (history_query, {"geoid": geoid_2020}),
            (availability_query, common),
            (summary_query, common),
            (match_query, common),
            (trajectory_query, common),
        ]
        if self._forecast_release:
            forecast_availability_table = self._table(
                self._settings.serving_schema,
                "serving_forecast_availability_current",
            )
            forecast_table = self._table(
                self._settings.serving_schema,
                "serving_forecast_current",
            )
            forecast_common = {
                "geoid": geoid_2020,
                "forecast_release_id": self._forecast_release["serving_release_id"],
            }
            queries.extend(
                [
                    (
                        f"""
                        SELECT *
                        FROM {forecast_availability_table}
                        WHERE geoid_2020 = :geoid
                          AND serving_release_id = :forecast_release_id
                        ORDER BY horizon_years
                        """,
                        forecast_common,
                    ),
                    (
                        f"""
                        SELECT *
                        FROM {forecast_table}
                        WHERE geoid_2020 = :geoid
                          AND serving_release_id = :forecast_release_id
                        ORDER BY horizon_years
                        """,
                        forecast_common,
                    ),
                ]
            )
        frames = self._executor.fetch_frames(queries)
        (
            profile,
            map_context,
            history,
            availability,
            summaries,
            matches,
            trajectories,
        ) = frames[:7]
        if self._forecast_release:
            forecast_availability, forecasts = frames[7:9]
        else:
            forecast_availability, forecasts = pd.DataFrame(), pd.DataFrame()
        if len(profile) != 1:
            raise LookupError(f"No unique current profile exists for tract {geoid_2020}.")
        selected_geometry = map_context.loc[map_context["geoid_2020"] == geoid_2020]
        bounds = selected_geometry.iloc[0].to_dict() if not selected_geometry.empty else {}
        return NeighborhoodData(
            release=dict(self._release),
            profile={str(key): value for key, value in profile.iloc[0].to_dict().items()},
            bounds=({str(key): value for key, value in bounds.items()} if bounds else {}),
            map_context=map_context,
            history=history,
            availability=availability,
            summaries=summaries,
            matches=matches,
            trajectories=trajectories,
            forecast_release=dict(self._forecast_release),
            forecast_availability=forecast_availability,
            forecasts=forecasts,
            data_mode="live",
        )


class SampleNeighborhoodRepository:
    """Small, explicit local demonstration repository backed by a public-data fixture."""

    def __init__(self, sample_path: Path) -> None:
        payload = json.loads(sample_path.read_text(encoding="utf-8"))
        self._payload = payload

    def search_places(self, search_text: str, limit: int = 12) -> pd.DataFrame:
        """Search the single committed demonstration tract."""

        places = pd.DataFrame(self._payload["places"])
        profile = self._payload["profile"]
        places["forecast_available"] = False
        places["population_total_estimate"] = profile.get("population_total_estimate")
        places["housing_units_total_estimate"] = profile.get("housing_units_total_estimate")
        cleaned = search_text.strip().lower()
        if cleaned:
            labels = (
                places["geoid_2020"].astype(str)
                + " "
                + places["county_name"].astype(str)
                + " "
                + places["state_name"].astype(str)
                + " "
                + places["tract_name"].astype(str)
            ).str.lower()
            places = places.loc[labels.str.contains(cleaned, regex=False)]
        return places.head(limit).reset_index(drop=True)

    def list_states(self) -> pd.DataFrame:
        """Return the one-state coverage represented by the reduced local fixture."""

        profile = self._payload["profile"]
        return pd.DataFrame(
            [
                {
                    "state_fips": profile["state_fips"],
                    "state_abbreviation": profile["state_abbreviation"],
                    "state_name": profile["state_name"],
                    "tract_count": 1,
                    "analogue_ready_tract_count": 1,
                    "analogue_ready_share": 1.0,
                    "forecast_ready_tract_count": 0,
                    "forecast_ready_share": 0.0,
                }
            ]
        )

    def list_counties(self, state_abbreviation: str) -> pd.DataFrame:
        """Return the one county represented by the reduced local fixture."""

        profile = self._payload["profile"]
        if state_abbreviation.upper() != profile["state_abbreviation"]:
            return pd.DataFrame()
        return pd.DataFrame(
            [
                {
                    "county_geoid": profile["county_geoid"],
                    "county_name": profile["county_name"],
                    "state_abbreviation": profile["state_abbreviation"],
                    "tract_count": 1,
                    "analogue_ready_tract_count": 1,
                    "forecast_ready_tract_count": 0,
                }
            ]
        )

    def list_tracts(self, county_geoid: str) -> pd.DataFrame:
        """Return the one tract represented by the reduced local fixture."""

        profile = self._payload["profile"]
        if county_geoid != profile["county_geoid"]:
            return pd.DataFrame()
        return pd.DataFrame(
            [
                {
                    "geoid_2020": profile["geoid_2020"],
                    "state_abbreviation": profile["state_abbreviation"],
                    "state_name": profile["state_name"],
                    "county_geoid": profile["county_geoid"],
                    "county_name": profile["county_name"],
                    "tract_name": profile["tract_name"],
                    "analogue_available": True,
                    "forecast_available": False,
                    "population_total_estimate": profile.get("population_total_estimate"),
                    "housing_units_total_estimate": profile.get("housing_units_total_estimate"),
                }
            ]
        )

    def load_neighborhood(self, geoid_2020: str) -> NeighborhoodData:
        """Load the demonstration tract and preserve its reduced-fixture status."""

        if geoid_2020 != self._payload["profile"]["geoid_2020"]:
            raise LookupError(f"The local sample does not contain tract {geoid_2020}.")
        return NeighborhoodData(
            release=self._payload["release"],
            profile=self._payload["profile"],
            bounds=self._payload["bounds"],
            map_context=pd.DataFrame(),
            history=pd.DataFrame(self._payload["history"]),
            availability=pd.DataFrame(self._payload["availability"]),
            summaries=pd.DataFrame(self._payload["summaries"]),
            matches=pd.DataFrame(self._payload["matches"]),
            trajectories=pd.DataFrame(self._payload["trajectories"]),
            forecast_release={},
            forecast_availability=pd.DataFrame(),
            forecasts=pd.DataFrame(),
            data_mode="sample",
        )


def create_repository(settings: AppSettings) -> NeighborhoodRepository:
    """Create the configured repository without silently falling back between modes."""

    settings.validate()
    if settings.data_mode == "sample":
        assert settings.sample_path is not None
        return SampleNeighborhoodRepository(settings.sample_path)
    assert settings.warehouse_id is not None
    return DatabricksNeighborhoodRepository(
        settings,
        DatabricksSqlExecutor(settings.warehouse_id),
    )


def validate_release_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    """Validate one five-component release manifest for tests and exported bundles."""

    if not rows:
        raise ValueError("A serving release manifest cannot be empty.")
    release_ids = {str(row["serving_release_id"]) for row in rows}
    if len(release_ids) != 1:
        raise ValueError("Serving components must belong to one release ID.")
    components = {str(row["table_name"]) for row in rows}
    missing = REQUIRED_RELEASE_COMPONENTS - components
    if missing:
        raise ValueError(f"Serving release is missing components: {sorted(missing)}")
    if any(str(row.get("release_status")) != "validated" for row in rows):
        raise ValueError("Every serving component must have validated status.")

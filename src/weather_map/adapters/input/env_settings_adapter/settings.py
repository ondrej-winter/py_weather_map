"""Pydantic-backed environment parsing for runtime settings."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from weather_map.application.exceptions import ConfigurationError


def _normalize_optional_text(value: object) -> object:
    """Strip surrounding whitespace from optional text values."""
    if isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value:
            msg = "value must not be blank"
            raise ValueError(msg)
        return stripped_value
    return value


def _normalize_required_text(value: object) -> object:
    """Strip surrounding whitespace from required text values."""
    if isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value:
            msg = "value must not be blank"
            raise ValueError(msg)
        return stripped_value
    return value


class EnvSettings(BaseSettings):
    """Adapter-facing environment settings model."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    openmeteo_base_url: str | None = Field(default=None, alias="WEATHER_MAP_OPENMETEO_BASE_URL")
    request_timeout_seconds: float | None = Field(default=None, alias="WEATHER_MAP_REQUEST_TIMEOUT_SECONDS")
    local_weather_data_directory: Path | None = Field(default=None, alias="WEATHER_MAP_LOCAL_WEATHER_DATA_DIRECTORY")
    local_weather_coordinate_precision: int | None = Field(
        default=None,
        alias="WEATHER_MAP_LOCAL_WEATHER_COORDINATE_PRECISION",
    )
    host: str | None = Field(default=None, alias="WEATHER_MAP_HOST")
    port: int | None = Field(default=None, alias="WEATHER_MAP_PORT")
    default_grid_rows: int | None = Field(default=None, alias="WEATHER_MAP_DEFAULT_GRID_ROWS")
    default_grid_columns: int | None = Field(default=None, alias="WEATHER_MAP_DEFAULT_GRID_COLUMNS")
    max_grid_rows: int | None = Field(default=None, alias="WEATHER_MAP_MAX_GRID_ROWS")
    max_grid_columns: int | None = Field(default=None, alias="WEATHER_MAP_MAX_GRID_COLUMNS")

    @field_validator("openmeteo_base_url", "host", mode="before")
    @classmethod
    def normalize_text_fields(cls, value: object) -> object:
        """Normalize text fields before validation."""
        return _normalize_optional_text(value)

    @field_validator("openmeteo_base_url", "host", mode="after")
    @classmethod
    def validate_non_blank_text_fields(cls, value: str | None) -> str | None:
        """Reject blank text values when a field is explicitly configured."""
        if value is None:
            return value
        return cast("str", _normalize_required_text(value))

    @model_validator(mode="after")
    def validate_ranges(self) -> EnvSettings:
        """Validate numeric bounds and grouped grid settings."""
        if self.request_timeout_seconds is not None and self.request_timeout_seconds <= 0:
            msg = "WEATHER_MAP_REQUEST_TIMEOUT_SECONDS must be positive"
            raise ValueError(msg)
        if self.local_weather_coordinate_precision is not None and self.local_weather_coordinate_precision < 0:
            msg = "WEATHER_MAP_LOCAL_WEATHER_COORDINATE_PRECISION must be non-negative"
            raise ValueError(msg)
        if self.port is not None and not 1 <= self.port <= 65535:
            msg = "WEATHER_MAP_PORT must be between 1 and 65535"
            raise ValueError(msg)
        if self.default_grid_rows is not None and self.default_grid_rows < 2:
            msg = "WEATHER_MAP_DEFAULT_GRID_ROWS must be at least 2"
            raise ValueError(msg)
        if self.default_grid_columns is not None and self.default_grid_columns < 2:
            msg = "WEATHER_MAP_DEFAULT_GRID_COLUMNS must be at least 2"
            raise ValueError(msg)
        if (
            self.max_grid_rows is not None
            and self.default_grid_rows is not None
            and self.max_grid_rows < self.default_grid_rows
        ):
            msg = "WEATHER_MAP_MAX_GRID_ROWS must be greater than or equal to WEATHER_MAP_DEFAULT_GRID_ROWS"
            raise ValueError(msg)
        if (
            self.max_grid_columns is not None
            and self.default_grid_columns is not None
            and self.max_grid_columns < self.default_grid_columns
        ):
            msg = "WEATHER_MAP_MAX_GRID_COLUMNS must be greater than or equal to WEATHER_MAP_DEFAULT_GRID_COLUMNS"
            raise ValueError(msg)
        return self


def load_settings_from_env() -> EnvSettings:
    """Load validated settings from environment variables or `.env`."""
    try:
        return EnvSettings()
    except ValidationError as exc:
        error_messages = "; ".join(error["msg"] for error in exc.errors())
        message = f"Invalid configuration: {error_messages}"
        raise ConfigurationError(message) from exc

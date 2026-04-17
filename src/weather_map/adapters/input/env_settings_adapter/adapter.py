"""Thin adapter converting env settings into application settings."""

from __future__ import annotations

from weather_map.adapters.input.env_settings_adapter.settings import EnvSettings, load_settings_from_env
from weather_map.application.dtos import WeatherMapSettings


def _to_app_settings(settings: EnvSettings) -> WeatherMapSettings:
    """Convert adapter-facing settings into the application DTO."""
    return WeatherMapSettings(**settings.model_dump(exclude_none=True))


class EnvSettingsAdapter:
    """Load application settings from the process environment."""

    def load(self) -> WeatherMapSettings:
        """Return validated application settings."""
        return _to_app_settings(load_settings_from_env())

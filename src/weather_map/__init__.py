"""Application package for weather_map."""

from __future__ import annotations

import uvicorn

from weather_map.adapters.input.env_settings_adapter import EnvSettingsAdapter
from weather_map.bootstrap import build_application


def main() -> None:
    """Run the local weather-map web server."""
    settings = EnvSettingsAdapter().load()
    app = build_application(settings)
    uvicorn.run(app, host=settings.host, port=settings.port)

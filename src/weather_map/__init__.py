"""Application package for weather_map."""

from __future__ import annotations

import uvicorn

from weather_map.bootstrap import build_application
from weather_map.config import load_settings


def main() -> None:
    """Run the local weather-map web server."""
    settings = load_settings()
    app = build_application(settings)
    uvicorn.run(app, host=settings.host, port=settings.port)

"""Smoke tests for the application package entrypoint."""

import pytest

from weather_map import main

DEFAULT_PORT = 8000


def test_main_starts_uvicorn_with_loaded_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """The entrypoint should bootstrap the app and delegate to Uvicorn."""
    captured: dict[str, object] = {}

    def fake_build_application(settings: object) -> str:
        captured["settings"] = settings
        return "app"

    def fake_run(app: object, host: str, port: int) -> None:
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port

    monkeypatch.setattr("weather_map.build_application", fake_build_application)
    monkeypatch.setattr("weather_map.uvicorn.run", fake_run)

    main()

    assert captured["app"] == "app"
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == DEFAULT_PORT

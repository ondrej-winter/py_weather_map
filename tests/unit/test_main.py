"""Smoke tests for the application package."""

import pytest

from weather_map import main


def test_main_prints_default_message(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify the default entry point prints the scaffold message."""
    main()
    captured = capsys.readouterr()
    assert captured.out == "Hello from weather_map!\n"

"""Tests for geographic domain value objects."""

import pytest

from weather_map.domain.exceptions import InvalidViewportError
from weather_map.domain.geo import GeoPoint, GridSpec, MapViewport


def test_geo_point_accepts_valid_coordinates() -> None:
    """Valid coordinates should construct successfully."""
    point = GeoPoint(latitude=50.0, longitude=14.0)

    assert point.latitude == 50.0
    assert point.longitude == 14.0


def test_geo_point_rejects_invalid_latitude() -> None:
    """Latitude outside world bounds should be rejected."""
    with pytest.raises(InvalidViewportError):
        GeoPoint(latitude=100.0, longitude=14.0)


def test_map_viewport_requires_north_above_south() -> None:
    """A viewport with inverted latitude bounds is invalid."""
    with pytest.raises(InvalidViewportError):
        MapViewport(north=40.0, south=50.0, east=15.0, west=14.0)


def test_grid_spec_rejects_too_small_dimensions() -> None:
    """Grid dimensions must be at least two in each direction."""
    with pytest.raises(InvalidViewportError):
        GridSpec(rows=1, columns=2)

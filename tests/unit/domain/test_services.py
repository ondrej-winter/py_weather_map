"""Tests for pure weather-map domain services."""

from datetime import date, datetime, timezone

from weather_map.domain.geo import GeoPoint, GridSpec, MapViewport
from weather_map.domain.services import aggregate_series_values, generate_viewport_grid, normalize_heatmap_points
from weather_map.domain.weather import AnalysisMode, LocationWeatherSeries, TimeAggregation


def test_generate_viewport_grid_returns_expected_number_of_points() -> None:
    """Grid generation should produce rows * columns points."""
    points = generate_viewport_grid(
        viewport=MapViewport(north=50.0, south=49.0, east=15.0, west=14.0),
        grid_spec=GridSpec(rows=3, columns=4),
    )

    assert len(points) == 12
    assert points[0] == GeoPoint(latitude=49.0, longitude=14.0)
    assert points[-1] == GeoPoint(latitude=50.0, longitude=15.0)


def test_aggregate_series_values_uses_snapshot_hour() -> None:
    """Snapshot mode should return the exact hourly value for the selected time."""
    series = LocationWeatherSeries(
        location=GeoPoint(latitude=50.0, longitude=14.0),
        timestamps_utc=(
            datetime(2024, 1, 1, 10, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 11, tzinfo=timezone.utc),
        ),
        values=(2.0, 3.5),
    )

    value = aggregate_series_values(
        series=series,
        mode=AnalysisMode.SNAPSHOT,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
        snapshot_hour=11,
        aggregation=None,
    )

    assert value == 3.5


def test_aggregate_series_values_uses_sum_for_range_mode() -> None:
    """Range mode should honor the requested aggregation."""
    series = LocationWeatherSeries(
        location=GeoPoint(latitude=50.0, longitude=14.0),
        timestamps_utc=(
            datetime(2024, 1, 1, 10, tzinfo=timezone.utc),
            datetime(2024, 1, 2, 10, tzinfo=timezone.utc),
        ),
        values=(1.5, 2.5),
    )

    value = aggregate_series_values(
        series=series,
        mode=AnalysisMode.RANGE,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        snapshot_hour=None,
        aggregation=TimeAggregation.SUM,
    )

    assert value == 4.0


def test_normalize_heatmap_points_scales_values_into_unit_interval() -> None:
    """Heatmap intensities should be normalized between zero and one."""
    points = normalize_heatmap_points(
        [
            (GeoPoint(latitude=50.0, longitude=14.0), 10.0),
            (GeoPoint(latitude=50.5, longitude=14.5), 20.0),
        ]
    )

    assert points[0].intensity == 0.0
    assert points[1].intensity == 1.0

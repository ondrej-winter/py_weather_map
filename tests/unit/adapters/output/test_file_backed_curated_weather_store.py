"""Tests for the file-backed curated weather store."""

from datetime import date, datetime, timezone
from pathlib import Path

from weather_map.adapters.output.curated_weather.file_store import FileBackedCuratedHistoricalWeatherStore
from weather_map.application.dtos.weather_heatmap import HistoricalWeatherSampleRequest
from weather_map.domain.geo import GeoPoint
from weather_map.domain.weather import LocationWeatherSeries, WeatherLayer


def test_file_backed_curated_store_returns_available_series(tmp_path: Path) -> None:
    """Stored series should be available for later offline lookup."""
    store = FileBackedCuratedHistoricalWeatherStore(tmp_path)
    request = HistoricalWeatherSampleRequest(
        locations=(GeoPoint(latitude=50.12341, longitude=14.98764),),
        layer=WeatherLayer.TEMPERATURE,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
    )
    series = [
        LocationWeatherSeries(
            location=GeoPoint(latitude=50.12341, longitude=14.98764),
            timestamps_utc=(datetime(2024, 1, 1, 12, tzinfo=timezone.utc),),
            values=(3.5,),
        )
    ]

    store.save(request, series)

    assert store.fetch_available(request) == series


def test_file_backed_curated_store_returns_partial_matches(tmp_path: Path) -> None:
    """The store should return only locally available series for a multi-location request."""
    store = FileBackedCuratedHistoricalWeatherStore(tmp_path)
    stored_request = HistoricalWeatherSampleRequest(
        locations=(GeoPoint(latitude=50.0, longitude=14.0),),
        layer=WeatherLayer.TEMPERATURE,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
    )
    requested = HistoricalWeatherSampleRequest(
        locations=(GeoPoint(latitude=50.0, longitude=14.0), GeoPoint(latitude=51.0, longitude=15.0)),
        layer=WeatherLayer.TEMPERATURE,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
    )
    stored_series = [
        LocationWeatherSeries(
            location=GeoPoint(latitude=50.0, longitude=14.0),
            timestamps_utc=(datetime(2024, 1, 1, 12, tzinfo=timezone.utc),),
            values=(4.0,),
        )
    ]

    store.save(stored_request, stored_series)

    assert store.fetch_available(requested) == stored_series

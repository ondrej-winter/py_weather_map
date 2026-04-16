"""Tests for the in-memory weather cache adapter."""

from datetime import date, datetime, timezone

from weather_map.adapters.output.weather_cache.in_memory import InMemoryHistoricalWeatherCache
from weather_map.application.dtos.weather_heatmap import HistoricalWeatherSampleRequest
from weather_map.domain.geo import GeoPoint
from weather_map.domain.weather import LocationWeatherSeries, WeatherLayer


def test_in_memory_cache_round_trips_series() -> None:
    """Stored series should be returned for the same request."""
    cache = InMemoryHistoricalWeatherCache()
    request = HistoricalWeatherSampleRequest(
        locations=(GeoPoint(latitude=50.0, longitude=14.0),),
        layer=WeatherLayer.TEMPERATURE,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
    )
    series = [
        LocationWeatherSeries(
            location=GeoPoint(latitude=50.0, longitude=14.0),
            timestamps_utc=(datetime(2024, 1, 1, 12, tzinfo=timezone.utc),),
            values=(5.0,),
        )
    ]

    cache.set(request, series)

    assert cache.get(request) == series

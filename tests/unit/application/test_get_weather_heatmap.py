"""Tests for weather heatmap application orchestration."""

from datetime import date, datetime, timezone

from weather_map.application.dtos.weather_heatmap import HeatmapQuery, HistoricalWeatherSampleRequest
from weather_map.application.use_cases.get_weather_heatmap import GetWeatherHeatmapUseCase
from weather_map.domain.geo import GeoPoint, GridSpec, MapViewport
from weather_map.domain.weather import AnalysisMode, LocationWeatherSeries, WeatherLayer


class FakeProvider:
    """Fake historical weather provider for deterministic tests."""

    def __init__(self, series: list[LocationWeatherSeries]) -> None:
        self.series = series
        self.requests: list[HistoricalWeatherSampleRequest] = []

    def fetch(self, request: HistoricalWeatherSampleRequest) -> list[LocationWeatherSeries]:
        self.requests.append(request)
        return self.series


class FakeCache:
    """Fake cache that can be preloaded with a value."""

    def __init__(self, cached: list[LocationWeatherSeries] | None = None) -> None:
        self.cached = cached
        self.stored: list[LocationWeatherSeries] | None = None

    def get(self, request: HistoricalWeatherSampleRequest) -> list[LocationWeatherSeries] | None:
        return self.cached

    def set(self, request: HistoricalWeatherSampleRequest, series: list[LocationWeatherSeries]) -> None:
        self.stored = series


def test_get_weather_heatmap_queries_provider_and_returns_points() -> None:
    """The use case should call the provider and normalize returned samples."""
    provider = FakeProvider(
        series=[
            LocationWeatherSeries(
                location=GeoPoint(latitude=49.0, longitude=14.0),
                timestamps_utc=(datetime(2024, 1, 1, 12, tzinfo=timezone.utc),),
                values=(2.0,),
            ),
            LocationWeatherSeries(
                location=GeoPoint(latitude=50.0, longitude=15.0),
                timestamps_utc=(datetime(2024, 1, 1, 12, tzinfo=timezone.utc),),
                values=(8.0,),
            ),
        ]
    )
    cache = FakeCache()
    use_case = GetWeatherHeatmapUseCase(provider=provider, cache=cache)

    response = use_case.execute(
        HeatmapQuery(
            viewport=MapViewport(north=50.0, south=49.0, east=15.0, west=14.0),
            layer=WeatherLayer.TEMPERATURE,
            mode=AnalysisMode.SNAPSHOT,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            snapshot_hour=12,
            aggregation=None,
            grid_spec=GridSpec(rows=2, columns=2),
        )
    )

    assert len(provider.requests) == 1
    assert cache.stored is not None
    assert response.sample_count == 2
    assert response.points[0].intensity == 0.0
    assert response.points[1].intensity == 1.0
    assert response.from_cache is False


def test_get_weather_heatmap_uses_cache_when_available() -> None:
    """Cached responses should avoid provider calls."""
    cached_series = [
        LocationWeatherSeries(
            location=GeoPoint(latitude=49.0, longitude=14.0),
            timestamps_utc=(datetime(2024, 1, 1, 12, tzinfo=timezone.utc),),
            values=(5.0,),
        )
    ]
    provider = FakeProvider(series=[])
    cache = FakeCache(cached=cached_series)
    use_case = GetWeatherHeatmapUseCase(provider=provider, cache=cache)

    response = use_case.execute(
        HeatmapQuery(
            viewport=MapViewport(north=50.0, south=49.0, east=15.0, west=14.0),
            layer=WeatherLayer.TEMPERATURE,
            mode=AnalysisMode.SNAPSHOT,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            snapshot_hour=12,
            aggregation=None,
            grid_spec=GridSpec(rows=2, columns=2),
        )
    )

    assert provider.requests == []
    assert response.from_cache is True

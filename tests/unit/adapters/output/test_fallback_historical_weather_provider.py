"""Tests for the offline-first historical weather provider."""

from datetime import date, datetime, timezone

from weather_map.adapters.output.historical_weather.fallback_provider import FallbackHistoricalWeatherProvider
from weather_map.application.dtos.weather_heatmap import HistoricalWeatherSampleRequest
from weather_map.domain.geo import GeoPoint
from weather_map.domain.weather import LocationWeatherSeries, WeatherLayer


class FakeCuratedStore:
    """Fake curated local store for fallback-provider tests."""

    def __init__(self, available: list[LocationWeatherSeries] | None = None) -> None:
        self.available = available or []
        self.saved_requests: list[HistoricalWeatherSampleRequest] = []
        self.saved_series: list[list[LocationWeatherSeries]] = []

    def fetch_available(self, request: HistoricalWeatherSampleRequest) -> list[LocationWeatherSeries]:
        return self.available

    def save(self, request: HistoricalWeatherSampleRequest, series: list[LocationWeatherSeries]) -> None:
        self.saved_requests.append(request)
        self.saved_series.append(series)


class FakeRemoteProvider:
    """Fake remote provider used to capture missing-location requests."""

    def __init__(self, result: list[LocationWeatherSeries]) -> None:
        self.result = result
        self.requests: list[HistoricalWeatherSampleRequest] = []

    def fetch(self, request: HistoricalWeatherSampleRequest) -> list[LocationWeatherSeries]:
        self.requests.append(request)
        return self.result


def test_fallback_provider_uses_local_series_before_remote_fetch() -> None:
    """Only missing locations should be fetched online and then persisted locally."""
    local_series = LocationWeatherSeries(
        location=GeoPoint(latitude=50.0, longitude=14.0),
        timestamps_utc=(datetime(2024, 1, 1, 12, tzinfo=timezone.utc),),
        values=(2.0,),
    )
    remote_series = LocationWeatherSeries(
        location=GeoPoint(latitude=51.0, longitude=15.0),
        timestamps_utc=(datetime(2024, 1, 1, 12, tzinfo=timezone.utc),),
        values=(8.0,),
    )
    store = FakeCuratedStore(available=[local_series])
    remote_provider = FakeRemoteProvider(result=[remote_series])
    provider = FallbackHistoricalWeatherProvider(curated_store=store, remote_provider=remote_provider)
    request = HistoricalWeatherSampleRequest(
        locations=(GeoPoint(latitude=50.0, longitude=14.0), GeoPoint(latitude=51.0, longitude=15.0)),
        layer=WeatherLayer.TEMPERATURE,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
    )

    result = provider.fetch(request)

    assert [series.location for series in result] == list(request.locations)
    assert len(remote_provider.requests) == 1
    assert remote_provider.requests[0].locations == (GeoPoint(latitude=51.0, longitude=15.0),)
    assert store.saved_series == [[remote_series]]


def test_fallback_provider_skips_remote_when_all_locations_are_local() -> None:
    """No remote call should be made when curated storage satisfies the request."""
    local_series = LocationWeatherSeries(
        location=GeoPoint(latitude=50.0, longitude=14.0),
        timestamps_utc=(datetime(2024, 1, 1, 12, tzinfo=timezone.utc),),
        values=(2.0,),
    )
    store = FakeCuratedStore(available=[local_series])
    remote_provider = FakeRemoteProvider(result=[])
    provider = FallbackHistoricalWeatherProvider(curated_store=store, remote_provider=remote_provider)
    request = HistoricalWeatherSampleRequest(
        locations=(GeoPoint(latitude=50.0, longitude=14.0),),
        layer=WeatherLayer.TEMPERATURE,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
    )

    result = provider.fetch(request)

    assert result == [local_series]
    assert remote_provider.requests == []
    assert store.saved_series == []

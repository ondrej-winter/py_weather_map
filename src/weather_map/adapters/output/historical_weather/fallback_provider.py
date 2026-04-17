"""Offline-first historical weather provider composition."""

from __future__ import annotations

from weather_map.application.dtos.weather_heatmap import HistoricalWeatherSampleRequest
from weather_map.application.ports.output import CuratedHistoricalWeatherStorePort, HistoricalWeatherProviderPort
from weather_map.domain.weather import LocationWeatherSeries


class FallbackHistoricalWeatherProvider:
    """Resolve historical weather from local curated data before remote fetches."""

    def __init__(
        self,
        curated_store: CuratedHistoricalWeatherStorePort,
        remote_provider: HistoricalWeatherProviderPort,
    ) -> None:
        """Initialize the offline-first provider."""
        self._curated_store = curated_store
        self._remote_provider = remote_provider

    def fetch(self, request: HistoricalWeatherSampleRequest) -> list[LocationWeatherSeries]:
        """Fetch all requested series from local storage first, then online when missing."""
        available_series = self._curated_store.fetch_available(request)
        available_by_location = {series.location: series for series in available_series}
        missing_locations = tuple(location for location in request.locations if location not in available_by_location)

        if missing_locations:
            missing_request = HistoricalWeatherSampleRequest(
                locations=missing_locations,
                layer=request.layer,
                start_date=request.start_date,
                end_date=request.end_date,
            )
            missing_series = self._remote_provider.fetch(missing_request)
            if missing_series:
                self._curated_store.save(missing_request, missing_series)
                available_by_location.update({series.location: series for series in missing_series})

        return [available_by_location[location] for location in request.locations if location in available_by_location]

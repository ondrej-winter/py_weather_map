"""Use case for generating weather heatmap data for a map viewport."""

from __future__ import annotations

from datetime import UTC, datetime

from weather_map.application.dtos.weather_heatmap import (
    HeatmapPointDTO,
    HeatmapQuery,
    HeatmapResponse,
    HistoricalWeatherSampleRequest,
)
from weather_map.application.ports.output import HistoricalWeatherCachePort, HistoricalWeatherProviderPort
from weather_map.domain.services import aggregate_series_values, generate_viewport_grid, normalize_heatmap_points
from weather_map.domain.weather import get_layer_definition


class GetWeatherHeatmapUseCase:
    """Generate normalized heatmap points for a viewport weather query."""

    def __init__(
        self,
        provider: HistoricalWeatherProviderPort,
        cache: HistoricalWeatherCachePort | None = None,
    ) -> None:
        """Initialize the use case with output ports."""
        self._provider = provider
        self._cache = cache

    def execute(self, query: HeatmapQuery) -> HeatmapResponse:
        """Execute the heatmap workflow."""
        layer_definition = get_layer_definition(query.layer)
        locations = tuple(generate_viewport_grid(query.viewport, query.grid_spec))
        request = HistoricalWeatherSampleRequest(
            locations=locations,
            layer=query.layer,
            start_date=query.start_date,
            end_date=query.end_date,
        )

        cached_series = self._cache.get(request) if self._cache is not None else None
        from_cache = cached_series is not None
        series_list = cached_series if cached_series is not None else self._provider.fetch(request)
        if self._cache is not None and cached_series is None:
            self._cache.set(request, series_list)

        sampled_values = []
        aggregation = query.aggregation or layer_definition.default_range_aggregation
        for series in series_list:
            aggregated_value = aggregate_series_values(
                series=series,
                mode=query.mode,
                start_date=query.start_date,
                end_date=query.end_date,
                snapshot_hour=query.snapshot_hour,
                aggregation=aggregation,
            )
            if aggregated_value is not None:
                sampled_values.append((series.location, aggregated_value))

        heatmap_points = normalize_heatmap_points(sampled_values)
        raw_values = [point.value for point in heatmap_points]
        return HeatmapResponse(
            layer=query.layer,
            mode=query.mode,
            aggregation=aggregation if query.mode.value == "range" else None,
            unit=layer_definition.unit,
            points=[
                HeatmapPointDTO(
                    latitude=point.latitude,
                    longitude=point.longitude,
                    value=point.value,
                    intensity=point.intensity,
                )
                for point in heatmap_points
            ],
            min_value=min(raw_values) if raw_values else None,
            max_value=max(raw_values) if raw_values else None,
            sample_count=len(heatmap_points),
            generated_at_utc=datetime.now(UTC),
            from_cache=from_cache,
        )

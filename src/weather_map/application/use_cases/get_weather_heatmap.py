"""Use case for generating weather heatmap data for a map viewport."""

from __future__ import annotations

from datetime import UTC, datetime

from weather_map.application.dtos.geometry import GridSpec, MapViewport
from weather_map.application.dtos.weather_heatmap import (
    HeatmapPointDTO,
    HeatmapQuery,
    HeatmapResponse,
    HistoricalWeatherSampleRequest,
)
from weather_map.application.ports.output import HistoricalWeatherCachePort, HistoricalWeatherProviderPort
from weather_map.domain.geo import GeoPoint
from weather_map.domain.services import aggregate_series_values, normalize_heatmap_points
from weather_map.domain.weather import get_layer_definition


def generate_viewport_grid(viewport: MapViewport, grid_spec: GridSpec) -> list[GeoPoint]:
    """Generate evenly spaced sample points over the viewport."""
    lat_step = (viewport.north - viewport.south) / (grid_spec.rows - 1)
    lon_step = (viewport.east - viewport.west) / (grid_spec.columns - 1)
    points: list[GeoPoint] = []
    for row in range(grid_spec.rows):
        latitude = viewport.south + (row * lat_step)
        for column in range(grid_spec.columns):
            longitude = viewport.west + (column * lon_step)
            points.append(GeoPoint(latitude=latitude, longitude=longitude))
    return points


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
        location_indices = {
            location: divmod(index, query.grid_spec.columns) for index, location in enumerate(locations)
        }
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

        aggregated_by_location = {}
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
                aggregated_by_location[series.location] = aggregated_value

        sampled_values = [
            (location, aggregated_by_location[location]) for location in locations if location in aggregated_by_location
        ]

        indexed_sampled_values = [(location_indices[location], location, value) for location, value in sampled_values]
        heatmap_points = normalize_heatmap_points([(location, value) for _, location, value in indexed_sampled_values])
        raw_values = [point.value for point in heatmap_points]
        return HeatmapResponse(
            layer=query.layer,
            mode=query.mode,
            aggregation=aggregation if query.mode.value == "range" else None,
            unit=layer_definition.unit,
            viewport=query.viewport,
            grid_spec=query.grid_spec,
            points=[
                HeatmapPointDTO(
                    row_index=grid_index[0],
                    column_index=grid_index[1],
                    latitude=point.latitude,
                    longitude=point.longitude,
                    value=point.value,
                    intensity=point.intensity,
                )
                for (grid_index, _, _), point in zip(indexed_sampled_values, heatmap_points, strict=True)
            ],
            min_value=min(raw_values) if raw_values else None,
            max_value=max(raw_values) if raw_values else None,
            sample_count=len(heatmap_points),
            generated_at_utc=datetime.now(UTC),
            from_cache=from_cache,
        )

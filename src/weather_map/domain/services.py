"""Pure domain services for weather map sampling and aggregation."""

from __future__ import annotations

from datetime import date
from statistics import fmean

from weather_map.domain.geo import GeoPoint
from weather_map.domain.weather import AnalysisMode, HeatmapPoint, LocationWeatherSeries, TimeAggregation


def aggregate_series_values(
    series: LocationWeatherSeries,
    mode: AnalysisMode,
    start_date: date,
    end_date: date,
    snapshot_hour: int | None,
    aggregation: TimeAggregation | None,
) -> float | None:
    """Aggregate a single location time series for the requested temporal mode."""
    matching_values = [
        value
        for timestamp, value in zip(series.timestamps_utc, series.values, strict=True)
        if start_date <= timestamp.date() <= end_date
    ]

    if mode is AnalysisMode.SNAPSHOT:
        snapshot_values = [
            value
            for timestamp, value in zip(series.timestamps_utc, series.values, strict=True)
            if timestamp.date() == start_date and timestamp.hour == snapshot_hour
        ]
        return snapshot_values[0] if snapshot_values else None

    if not matching_values:
        return None
    if aggregation is TimeAggregation.SUM:
        return float(sum(matching_values))
    if aggregation is TimeAggregation.MIN:
        return min(matching_values)
    if aggregation is TimeAggregation.MAX:
        return max(matching_values)
    return float(fmean(matching_values))


def normalize_heatmap_points(values: list[tuple[GeoPoint, float]]) -> list[HeatmapPoint]:
    """Normalize raw sampled values into heatmap points with intensities."""
    if not values:
        return []
    raw_values = [value for _, value in values]
    min_value = min(raw_values)
    max_value = max(raw_values)
    range_value = max_value - min_value
    if range_value == 0:
        return [
            HeatmapPoint(
                latitude=point.latitude,
                longitude=point.longitude,
                value=value,
                intensity=1.0,
            )
            for point, value in values
        ]
    return [
        HeatmapPoint(
            latitude=point.latitude,
            longitude=point.longitude,
            value=value,
            intensity=(value - min_value) / range_value,
        )
        for point, value in values
    ]

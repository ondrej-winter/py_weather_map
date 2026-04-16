"""Domain weather types and supported layer metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from weather_map.domain.exceptions import InvalidHeatmapQueryError, UnsupportedWeatherLayerError
from weather_map.domain.geo import GeoPoint


class WeatherLayer(StrEnum):
    """Supported weather layers for visualization."""

    TEMPERATURE = "temperature"
    PRECIPITATION = "precipitation"
    HUMIDITY = "humidity"
    WIND_SPEED = "wind_speed"


class AnalysisMode(StrEnum):
    """Supported temporal analysis modes."""

    SNAPSHOT = "snapshot"
    RANGE = "range"


class TimeAggregation(StrEnum):
    """Supported range aggregations."""

    MEAN = "mean"
    SUM = "sum"
    MIN = "min"
    MAX = "max"


@dataclass(frozen=True)
class LayerDefinition:
    """Metadata describing a supported weather layer."""

    layer: WeatherLayer
    label: str
    unit: str
    openmeteo_hourly_variable: str
    default_range_aggregation: TimeAggregation
    supported_range_aggregations: tuple[TimeAggregation, ...]

    def __post_init__(self) -> None:
        """Validate the layer definition."""
        if self.default_range_aggregation not in self.supported_range_aggregations:
            msg = "default_range_aggregation must be one of supported_range_aggregations"
            raise InvalidHeatmapQueryError(msg)


@dataclass(frozen=True)
class LocationWeatherSeries:
    """Normalized weather time series for a single location."""

    location: GeoPoint
    timestamps_utc: tuple[datetime, ...]
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        """Validate timestamps and values."""
        if len(self.timestamps_utc) != len(self.values):
            msg = "timestamps and values must have equal length"
            raise InvalidHeatmapQueryError(msg)
        for timestamp in self.timestamps_utc:
            if timestamp.tzinfo is None or timestamp.utcoffset() != UTC.utcoffset(timestamp):
                msg = "timestamps must be timezone-aware UTC datetimes"
                raise InvalidHeatmapQueryError(msg)


@dataclass(frozen=True)
class HeatmapPoint:
    """Heatmap point with normalized intensity."""

    latitude: float
    longitude: float
    value: float
    intensity: float

    def __post_init__(self) -> None:
        """Validate intensity bounds."""
        if not 0.0 <= self.intensity <= 1.0:
            msg = "intensity must be between 0 and 1"
            raise InvalidHeatmapQueryError(msg)


LAYER_DEFINITIONS: dict[WeatherLayer, LayerDefinition] = {
    WeatherLayer.TEMPERATURE: LayerDefinition(
        layer=WeatherLayer.TEMPERATURE,
        label="Temperature",
        unit="°C",
        openmeteo_hourly_variable="temperature_2m",
        default_range_aggregation=TimeAggregation.MEAN,
        supported_range_aggregations=(TimeAggregation.MEAN, TimeAggregation.MIN, TimeAggregation.MAX),
    ),
    WeatherLayer.PRECIPITATION: LayerDefinition(
        layer=WeatherLayer.PRECIPITATION,
        label="Precipitation",
        unit="mm",
        openmeteo_hourly_variable="precipitation",
        default_range_aggregation=TimeAggregation.SUM,
        supported_range_aggregations=(TimeAggregation.SUM, TimeAggregation.MEAN, TimeAggregation.MAX),
    ),
    WeatherLayer.HUMIDITY: LayerDefinition(
        layer=WeatherLayer.HUMIDITY,
        label="Relative humidity",
        unit="%",
        openmeteo_hourly_variable="relative_humidity_2m",
        default_range_aggregation=TimeAggregation.MEAN,
        supported_range_aggregations=(TimeAggregation.MEAN, TimeAggregation.MIN, TimeAggregation.MAX),
    ),
    WeatherLayer.WIND_SPEED: LayerDefinition(
        layer=WeatherLayer.WIND_SPEED,
        label="Wind speed",
        unit="km/h",
        openmeteo_hourly_variable="wind_speed_10m",
        default_range_aggregation=TimeAggregation.MEAN,
        supported_range_aggregations=(TimeAggregation.MEAN, TimeAggregation.MAX, TimeAggregation.MIN),
    ),
}


def get_layer_definition(layer: WeatherLayer) -> LayerDefinition:
    """Return metadata for a supported weather layer."""
    try:
        return LAYER_DEFINITIONS[layer]
    except KeyError as error:
        msg = f"Unsupported weather layer: {layer}"
        raise UnsupportedWeatherLayerError(msg) from error

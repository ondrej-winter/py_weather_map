"""Domain layer for business entities, value objects, and rules."""

from weather_map.domain.exceptions import (
    InvalidHeatmapQueryError,
    InvalidViewportError,
    UnsupportedWeatherLayerError,
    WeatherDataUnavailableError,
    WeatherMapError,
)
from weather_map.domain.geo import GeoPoint
from weather_map.domain.weather import (
    AnalysisMode,
    HeatmapPoint,
    LayerDefinition,
    LocationWeatherSeries,
    TimeAggregation,
    WeatherLayer,
)

__all__ = [
    "AnalysisMode",
    "GeoPoint",
    "HeatmapPoint",
    "InvalidHeatmapQueryError",
    "InvalidViewportError",
    "LayerDefinition",
    "LocationWeatherSeries",
    "TimeAggregation",
    "UnsupportedWeatherLayerError",
    "WeatherDataUnavailableError",
    "WeatherLayer",
    "WeatherMapError",
]

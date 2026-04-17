"""Open-Meteo historical weather adapter package."""

from weather_map.adapters.output.open_meteo.client import OpenMeteoHistoricalWeatherClient
from weather_map.adapters.output.open_meteo.dtos import (
    OpenMeteoArchiveLocationData,
    OpenMeteoArchiveRequest,
    OpenMeteoDailyData,
    OpenMeteoDailyVariable,
    OpenMeteoHourlyData,
    OpenMeteoHourlyVariable,
)
from weather_map.adapters.output.open_meteo.provider import OpenMeteoHistoricalWeatherProvider
from weather_map.adapters.output.open_meteo.settings import OpenMeteoClientSettings

__all__ = [
    "OpenMeteoArchiveLocationData",
    "OpenMeteoArchiveRequest",
    "OpenMeteoClientSettings",
    "OpenMeteoDailyData",
    "OpenMeteoDailyVariable",
    "OpenMeteoHistoricalWeatherClient",
    "OpenMeteoHistoricalWeatherProvider",
    "OpenMeteoHourlyData",
    "OpenMeteoHourlyVariable",
]

"""Composition root for the weather-map application."""

from __future__ import annotations

from fastapi import FastAPI

from weather_map.adapters.input.http.app import create_app
from weather_map.adapters.output.open_meteo.client import OpenMeteoHistoricalWeatherClient
from weather_map.adapters.output.weather_cache.in_memory import InMemoryHistoricalWeatherCache
from weather_map.application.use_cases.get_available_layers import GetAvailableWeatherLayersUseCase
from weather_map.application.use_cases.get_weather_heatmap import GetWeatherHeatmapUseCase
from weather_map.config import WeatherMapSettings, load_settings


def build_application(settings: WeatherMapSettings | None = None) -> FastAPI:
    """Build the configured FastAPI application."""
    resolved_settings = settings or load_settings()
    cache = InMemoryHistoricalWeatherCache()
    provider = OpenMeteoHistoricalWeatherClient(resolved_settings)
    heatmap_use_case = GetWeatherHeatmapUseCase(provider=provider, cache=cache)
    layers_use_case = GetAvailableWeatherLayersUseCase()
    return create_app(
        heatmap_use_case=heatmap_use_case,
        available_layers_use_case=layers_use_case,
        settings=resolved_settings,
    )

"""Use case for listing supported weather layers."""

from __future__ import annotations

from weather_map.application.dtos.weather_heatmap import LayerOptionDTO
from weather_map.domain.weather import LAYER_DEFINITIONS


class GetAvailableWeatherLayersUseCase:
    """Provide the UI with supported layer metadata."""

    def execute(self) -> list[LayerOptionDTO]:
        """Return supported weather layer definitions."""
        return [
            LayerOptionDTO(
                layer=definition.layer,
                label=definition.label,
                unit=definition.unit,
                default_range_aggregation=definition.default_range_aggregation,
                supported_range_aggregations=definition.supported_range_aggregations,
            )
            for definition in LAYER_DEFINITIONS.values()
        ]

"""Tests for the FastAPI HTTP adapter."""

from datetime import UTC, datetime
from http import HTTPStatus

from fastapi.testclient import TestClient

from weather_map.adapters.input.http.app import create_app
from weather_map.application.dtos import WeatherMapSettings
from weather_map.application.dtos.geometry import GridSpec, MapViewport
from weather_map.application.dtos.weather_heatmap import HeatmapPointDTO, HeatmapQuery, HeatmapResponse, LayerOptionDTO
from weather_map.domain.weather import AnalysisMode, TimeAggregation, WeatherLayer


class FakeHeatmapUseCase:
    """Fake heatmap use case for HTTP tests."""

    def execute(self, query: HeatmapQuery) -> HeatmapResponse:
        del query
        return HeatmapResponse(
            layer=WeatherLayer.TEMPERATURE,
            mode=AnalysisMode.SNAPSHOT,
            aggregation=None,
            unit="°C",
            viewport=MapViewport(north=50.0, south=49.0, east=15.0, west=14.0),
            grid_spec=GridSpec(rows=2, columns=2),
            points=[
                HeatmapPointDTO(
                    row_index=0,
                    column_index=0,
                    latitude=50.0,
                    longitude=14.0,
                    value=5.0,
                    intensity=1.0,
                )
            ],
            min_value=5.0,
            max_value=5.0,
            sample_count=1,
            generated_at_utc=datetime(2024, 1, 1, 12, tzinfo=UTC),
            from_cache=False,
        )


class FakeLayersUseCase:
    """Fake layer-metadata use case for HTTP tests."""

    def execute(self) -> list[LayerOptionDTO]:
        return [
            LayerOptionDTO(
                layer=WeatherLayer.TEMPERATURE,
                label="Temperature",
                unit="°C",
                default_range_aggregation=TimeAggregation.MEAN,
                supported_range_aggregations=(TimeAggregation.MEAN, TimeAggregation.MAX),
            )
        ]


def test_http_app_serves_layers_and_heatmap() -> None:
    """The HTTP adapter should expose both metadata and heatmap endpoints."""
    app = create_app(FakeHeatmapUseCase(), FakeLayersUseCase(), WeatherMapSettings())
    client = TestClient(app)

    layers_response = client.get("/api/layers")
    heatmap_response = client.get(
        "/api/heatmap",
        params={
            "north": 50.0,
            "south": 49.0,
            "east": 15.0,
            "west": 14.0,
            "layer": "temperature",
            "mode": "snapshot",
            "start_date": "2024-01-01",
            "end_date": "2024-01-01",
            "snapshot_hour": 12,
        },
    )

    assert layers_response.status_code == HTTPStatus.OK
    assert layers_response.json()[0]["layer"] == "temperature"
    assert heatmap_response.status_code == HTTPStatus.OK
    assert heatmap_response.json()["grid_spec"] == {"rows": 2, "columns": 2}
    assert heatmap_response.json()["points"][0]["row_index"] == 0
    assert heatmap_response.json()["sample_count"] == 1


def test_http_app_rejects_invalid_snapshot_query() -> None:
    """Invalid input should produce a client error."""
    app = create_app(FakeHeatmapUseCase(), FakeLayersUseCase(), WeatherMapSettings())
    client = TestClient(app)

    response = client.get(
        "/api/heatmap",
        params={
            "north": 50.0,
            "south": 49.0,
            "east": 15.0,
            "west": 14.0,
            "layer": "temperature",
            "mode": "snapshot",
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

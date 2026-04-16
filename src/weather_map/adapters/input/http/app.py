"""FastAPI HTTP adapter and static UI routes."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from weather_map.adapters.input.http.schemas import (
    HeatmapQueryRequestModel,
    HeatmapResponseModel,
    LayerOptionResponseModel,
    map_layer_option_to_model,
    map_request_to_query,
    map_response_to_model,
)
from weather_map.domain.exceptions import WeatherMapError

if TYPE_CHECKING:
    from weather_map.application.ports.input import AvailableWeatherLayersPort, WeatherHeatmapQueryPort
    from weather_map.config import WeatherMapSettings

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(
    heatmap_use_case: WeatherHeatmapQueryPort,
    available_layers_use_case: AvailableWeatherLayersPort,
    settings: WeatherMapSettings,
) -> FastAPI:
    """Create the FastAPI application for the local weather map UI."""
    app = FastAPI(title="weather-map", version="0.1.0")
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", response_class=FileResponse)
    def serve_index_html() -> FileResponse:
        """Serve the single-page browser shell."""
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/layers", response_model=list[LayerOptionResponseModel])
    def list_layer_options() -> list[LayerOptionResponseModel]:
        """Return supported weather layers for the UI."""
        return [map_layer_option_to_model(option) for option in available_layers_use_case.execute()]

    @app.get("/api/heatmap", response_model=HeatmapResponseModel)
    def get_heatmap_data(
        north: float = Query(...),
        south: float = Query(...),
        east: float = Query(...),
        west: float = Query(...),
        layer: str = Query(...),
        mode: str = Query(...),
        start_date: date = Query(...),
        end_date: date | None = Query(default=None),
        snapshot_hour: int | None = Query(default=None),
        aggregation: str | None = Query(default=None),
        grid_rows: int | None = Query(default=None),
        grid_columns: int | None = Query(default=None),
    ) -> HeatmapResponseModel:
        """Execute the heatmap query and return JSON for the browser UI."""
        try:
            request_model = HeatmapQueryRequestModel(
                north=north,
                south=south,
                east=east,
                west=west,
                layer=layer,
                mode=mode,
                start_date=start_date,
                end_date=end_date,
                snapshot_hour=snapshot_hour,
                aggregation=aggregation,
                grid_rows=grid_rows,
                grid_columns=grid_columns,
            )
            query = map_request_to_query(request_model, settings)
            return map_response_to_model(heatmap_use_case.execute(query))
        except ValidationError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except WeatherMapError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    return app

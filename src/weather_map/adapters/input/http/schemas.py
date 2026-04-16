"""Transport models and mapping helpers for the HTTP adapter."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

from weather_map.application.dtos.weather_heatmap import HeatmapPointDTO, HeatmapQuery, HeatmapResponse, LayerOptionDTO
from weather_map.config import WeatherMapSettings
from weather_map.domain.geo import GridSpec, MapViewport
from weather_map.domain.weather import AnalysisMode, TimeAggregation, WeatherLayer, get_layer_definition


class HeatmapQueryRequestModel(BaseModel):
    """HTTP request model for heatmap queries."""

    north: float
    south: float
    east: float
    west: float
    layer: str
    mode: str
    start_date: date
    end_date: date | None = None
    snapshot_hour: int | None = None
    aggregation: str | None = None
    grid_rows: int | None = Field(default=None, ge=2)
    grid_columns: int | None = Field(default=None, ge=2)

    @field_validator("layer")
    @classmethod
    def validate_layer(cls, value: str) -> str:
        """Validate the requested layer."""
        WeatherLayer(value)
        return value

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        """Validate the requested analysis mode."""
        AnalysisMode(value)
        return value

    @field_validator("aggregation")
    @classmethod
    def validate_aggregation(cls, value: str | None) -> str | None:
        """Validate the requested aggregation, when provided."""
        if value is not None:
            TimeAggregation(value)
        return value

    @model_validator(mode="after")
    def validate_temporal_parameters(self) -> "HeatmapQueryRequestModel":
        """Validate date and snapshot constraints."""
        if self.end_date is None:
            self.end_date = self.start_date
        if self.end_date < self.start_date:
            msg = "end_date must be greater than or equal to start_date"
            raise ValueError(msg)
        if self.mode == AnalysisMode.SNAPSHOT.value:
            if self.start_date != self.end_date:
                msg = "snapshot mode requires start_date and end_date to match"
                raise ValueError(msg)
            if self.snapshot_hour is None or not 0 <= self.snapshot_hour <= 23:
                msg = "snapshot mode requires snapshot_hour between 0 and 23"
                raise ValueError(msg)
        return self


class HeatmapPointResponseModel(BaseModel):
    """JSON model for a single heatmap point."""

    row_index: int
    column_index: int
    latitude: float
    longitude: float
    value: float
    intensity: float


class ViewportResponseModel(BaseModel):
    """JSON model for the viewport used to generate the surface."""

    north: float
    south: float
    east: float
    west: float


class GridSpecResponseModel(BaseModel):
    """JSON model for the sampling grid."""

    rows: int
    columns: int


class HeatmapResponseModel(BaseModel):
    """JSON model for heatmap query responses."""

    layer: str
    mode: str
    aggregation: str | None
    unit: str
    viewport: ViewportResponseModel
    grid_spec: GridSpecResponseModel
    points: list[HeatmapPointResponseModel]
    min_value: float | None
    max_value: float | None
    sample_count: int
    generated_at_utc: str
    from_cache: bool


class LayerOptionResponseModel(BaseModel):
    """JSON model for available weather layers."""

    layer: str
    label: str
    unit: str
    default_range_aggregation: str
    supported_range_aggregations: list[str]


def map_request_to_query(model: HeatmapQueryRequestModel, settings: WeatherMapSettings) -> HeatmapQuery:
    """Convert an HTTP query model into an application DTO."""
    layer = WeatherLayer(model.layer)
    mode = AnalysisMode(model.mode)
    aggregation = TimeAggregation(model.aggregation) if model.aggregation is not None else None
    grid_rows = min(model.grid_rows or settings.default_grid_rows, settings.max_grid_rows)
    grid_columns = min(model.grid_columns or settings.default_grid_columns, settings.max_grid_columns)
    query = HeatmapQuery(
        viewport=MapViewport(north=model.north, south=model.south, east=model.east, west=model.west),
        layer=layer,
        mode=mode,
        start_date=model.start_date,
        end_date=model.end_date or model.start_date,
        snapshot_hour=model.snapshot_hour,
        aggregation=aggregation or get_layer_definition(layer).default_range_aggregation,
        grid_spec=GridSpec(rows=grid_rows, columns=grid_columns),
    )
    return query


def map_response_to_model(response: HeatmapResponse) -> HeatmapResponseModel:
    """Convert an application response DTO into a JSON response model."""
    return HeatmapResponseModel(
        layer=response.layer.value,
        mode=response.mode.value,
        aggregation=response.aggregation.value if response.aggregation is not None else None,
        unit=response.unit,
        viewport=ViewportResponseModel(
            north=response.viewport.north,
            south=response.viewport.south,
            east=response.viewport.east,
            west=response.viewport.west,
        ),
        grid_spec=GridSpecResponseModel(rows=response.grid_spec.rows, columns=response.grid_spec.columns),
        points=[map_point_to_model(point) for point in response.points],
        min_value=response.min_value,
        max_value=response.max_value,
        sample_count=response.sample_count,
        generated_at_utc=response.generated_at_utc.isoformat(),
        from_cache=response.from_cache,
    )


def map_point_to_model(point: HeatmapPointDTO) -> HeatmapPointResponseModel:
    """Convert a heatmap point DTO into JSON form."""
    return HeatmapPointResponseModel(
        row_index=point.row_index,
        column_index=point.column_index,
        latitude=point.latitude,
        longitude=point.longitude,
        value=point.value,
        intensity=point.intensity,
    )


def map_layer_option_to_model(option: LayerOptionDTO) -> LayerOptionResponseModel:
    """Convert a layer option DTO into JSON form."""
    return LayerOptionResponseModel(
        layer=option.layer.value,
        label=option.label,
        unit=option.unit,
        default_range_aggregation=option.default_range_aggregation.value,
        supported_range_aggregations=[aggregation.value for aggregation in option.supported_range_aggregations],
    )

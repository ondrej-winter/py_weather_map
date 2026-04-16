"""Application DTOs for weather heatmap queries and results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from weather_map.domain.exceptions import InvalidHeatmapQueryError
from weather_map.domain.geo import GeoPoint, GridSpec, MapViewport
from weather_map.domain.weather import AnalysisMode, TimeAggregation, WeatherLayer


@dataclass(frozen=True)
class HeatmapQuery:
    """Input DTO for the weather heatmap use case."""

    viewport: MapViewport
    layer: WeatherLayer
    mode: AnalysisMode
    start_date: date
    end_date: date
    snapshot_hour: int | None
    aggregation: TimeAggregation | None
    grid_spec: GridSpec

    def __post_init__(self) -> None:
        """Validate query invariants."""
        if self.end_date < self.start_date:
            msg = "end_date must be greater than or equal to start_date"
            raise InvalidHeatmapQueryError(msg)
        if self.mode is AnalysisMode.SNAPSHOT:
            if self.start_date != self.end_date:
                msg = "snapshot mode requires start_date and end_date to match"
                raise InvalidHeatmapQueryError(msg)
            if self.snapshot_hour is None or not 0 <= self.snapshot_hour <= 23:
                msg = "snapshot mode requires snapshot_hour between 0 and 23"
                raise InvalidHeatmapQueryError(msg)


@dataclass(frozen=True)
class HistoricalWeatherSampleRequest:
    """Request DTO for retrieving weather time series for many locations."""

    locations: tuple[GeoPoint, ...]
    layer: WeatherLayer
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        """Validate retrieval request."""
        if not self.locations:
            msg = "locations must not be empty"
            raise InvalidHeatmapQueryError(msg)
        if self.end_date < self.start_date:
            msg = "end_date must be greater than or equal to start_date"
            raise InvalidHeatmapQueryError(msg)


@dataclass(frozen=True)
class HeatmapPointDTO:
    """A serialized heatmap point."""

    row_index: int
    column_index: int
    latitude: float
    longitude: float
    value: float
    intensity: float


@dataclass(frozen=True)
class HeatmapResponse:
    """Output DTO for the weather heatmap use case."""

    layer: WeatherLayer
    mode: AnalysisMode
    aggregation: TimeAggregation | None
    unit: str
    viewport: MapViewport
    grid_spec: GridSpec
    points: list[HeatmapPointDTO]
    min_value: float | None
    max_value: float | None
    sample_count: int
    generated_at_utc: datetime
    from_cache: bool

    def __post_init__(self) -> None:
        """Validate response invariants."""
        if self.generated_at_utc.tzinfo is None or self.generated_at_utc.utcoffset() != UTC.utcoffset(
            self.generated_at_utc
        ):
            msg = "generated_at_utc must be a timezone-aware UTC datetime"
            raise InvalidHeatmapQueryError(msg)
        if self.sample_count != len(self.points):
            msg = "sample_count must match the number of points"
            raise InvalidHeatmapQueryError(msg)
        for point in self.points:
            if not 0 <= point.row_index < self.grid_spec.rows:
                msg = "point row_index must fall within the grid bounds"
                raise InvalidHeatmapQueryError(msg)
            if not 0 <= point.column_index < self.grid_spec.columns:
                msg = "point column_index must fall within the grid bounds"
                raise InvalidHeatmapQueryError(msg)


@dataclass(frozen=True)
class LayerOptionDTO:
    """Layer metadata exposed to driving adapters."""

    layer: WeatherLayer
    label: str
    unit: str
    default_range_aggregation: TimeAggregation
    supported_range_aggregations: tuple[TimeAggregation, ...]

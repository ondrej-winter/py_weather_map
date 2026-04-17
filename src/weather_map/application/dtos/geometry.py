"""Application-layer geometry DTOs for heatmap queries and responses."""

from __future__ import annotations

from dataclasses import dataclass

from weather_map.domain.exceptions import InvalidViewportError


@dataclass(frozen=True)
class MapViewport:
    """Represents the current visible map bounds."""

    north: float
    south: float
    east: float
    west: float

    def __post_init__(self) -> None:
        """Validate viewport bounds."""
        if not -90.0 <= self.south <= 90.0 or not -90.0 <= self.north <= 90.0:
            msg = "latitude bounds must be between -90 and 90"
            raise InvalidViewportError(msg)
        if not -180.0 <= self.west <= 180.0 or not -180.0 <= self.east <= 180.0:
            msg = "longitude bounds must be between -180 and 180"
            raise InvalidViewportError(msg)
        if self.north <= self.south:
            msg = "north must be greater than south"
            raise InvalidViewportError(msg)
        if self.east <= self.west:
            msg = "east must be greater than west"
            raise InvalidViewportError(msg)


@dataclass(frozen=True)
class GridSpec:
    """Defines the regular viewport sampling density."""

    rows: int
    columns: int

    def __post_init__(self) -> None:
        """Validate grid dimensions."""
        if self.rows < 2 or self.columns < 2:
            msg = "grid dimensions must be at least 2"
            raise InvalidViewportError(msg)
        if self.rows > 50 or self.columns > 50:
            msg = "grid dimensions must be less than or equal to 50"
            raise InvalidViewportError(msg)

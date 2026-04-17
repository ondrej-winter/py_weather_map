"""Geographic value objects used by weather analysis."""

from __future__ import annotations

from dataclasses import dataclass

from weather_map.domain.exceptions import InvalidViewportError


@dataclass(frozen=True)
class GeoPoint:
    """Represents a point on Earth."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        """Validate coordinate bounds."""
        if not -90.0 <= self.latitude <= 90.0:
            msg = "latitude must be between -90 and 90"
            raise InvalidViewportError(msg)
        if not -180.0 <= self.longitude <= 180.0:
            msg = "longitude must be between -180 and 180"
            raise InvalidViewportError(msg)

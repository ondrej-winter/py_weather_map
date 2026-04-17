"""Adapter-specific settings for the Open-Meteo historical archive client."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OpenMeteoClientSettings:
    """Runtime settings owned by the Open-Meteo output adapter."""

    base_url: str
    request_timeout_seconds: float

    def __post_init__(self) -> None:
        """Validate adapter-specific configuration invariants."""
        if not self.base_url.strip():
            msg = "base_url must not be blank"
            raise ValueError(msg)
        if self.request_timeout_seconds <= 0:
            msg = "request_timeout_seconds must be positive"
            raise ValueError(msg)

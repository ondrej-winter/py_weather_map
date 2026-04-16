"""Domain and application-safe exceptions for weather-map workflows."""


class WeatherMapError(Exception):
    """Base exception for weather map errors."""


class InvalidViewportError(WeatherMapError):
    """Raised when a viewport or coordinate is invalid."""


class InvalidHeatmapQueryError(WeatherMapError):
    """Raised when a heatmap query violates application constraints."""


class UnsupportedWeatherLayerError(WeatherMapError):
    """Raised when a requested weather layer is unsupported."""


class WeatherDataUnavailableError(WeatherMapError):
    """Raised when historical weather data cannot be retrieved."""

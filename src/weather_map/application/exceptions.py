"""Application-layer exceptions."""


class ApplicationError(Exception):
    """Base application-layer error."""


class ConfigurationError(ApplicationError):
    """Raised when runtime configuration is missing or invalid."""

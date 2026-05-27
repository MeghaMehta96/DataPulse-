"""Custom exceptions for DataPulse."""


class InvalidMetricError(Exception):
    """Raised when a metric dict has missing keys or wrong value types."""
    pass


class MetricValidationError(InvalidMetricError):
    """Raised when a metric value is outside the expected range."""
    pass
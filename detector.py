import functools
from collections import deque
from exceptions import InvalidMetricError
from typing import Optional

_METRIC_KEYS = frozenset({
    "timestamp",
    "service_name",
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "latency_ms"
})

_NUMERIC_METRICS = frozenset({
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "latency_ms"
})

class AnomalyDetector:

    THRESHOLDS = {
        "cpu_percent": 90.0,
        "memory_percent": 85.0,
        "disk_percent": 90.0,
        "latency_ms": 800.0
    }

    def __init__(self, window_size: int = 5):
        self._window_size = window_size
        self._total_alerts = 0
        self._windows = {
            "cpu_percent":    deque(maxlen=window_size),
            "memory_percent": deque(maxlen=window_size),
            "disk_percent":   deque(maxlen=window_size),
            "latency_ms":     deque(maxlen=window_size),
        
    }
        
    def _validate_metric(self, metric: dict) -> None:
        """Raise InvalidMetricError for missing keys or wrong numeric types."""
        missing = _METRIC_KEYS - metric.keys()
        if missing:
            raise InvalidMetricError(f"Metric missing required keys: {missing}")
        for key in _NUMERIC_METRICS:
            if not isinstance(metric[key], (int, float)):
                raise InvalidMetricError(
                    f"Metric '{key}' must be numeric, got {type(metric[key]).__name__}"
                )
    @staticmethod
    def decorate_log(func):
        """
        Decorator that logs every anomaly detected with format:
        [ALERT] <timestamp> | <service> | <metric>=<value> (<severity>)
        """
        @functools.wraps(func)
        def wrapper(self: "AnomalyDetector", metric: dict) -> list[dict]:
            anomalies = func(self, metric)
            for anomaly in anomalies:
                print(
                    f"[ALERT] {anomaly['timestamp']} | {anomaly['service_name']} | "
                    f"{anomaly['metric']}={anomaly['value']} ({anomaly['severity']})"
                )
            return anomalies
        
        return wrapper

    @decorate_log
    def check_anomaly(self, metric: dict) -> list[dict]:
        """Check if the metric exceeds thresholds and return list of anomalies."""
        self._validate_metric(metric)
        anomalies: list[dict] = []
        for key in _NUMERIC_METRICS:
            value = metric[key]
            self._windows[key].append(value)
            if value > self.THRESHOLDS[key]:
                severity = "CRITICAL" if value > self.THRESHOLDS[key] * 1.1 else "WARNING"
                anomalies.append({
                    "timestamp": metric["timestamp"],
                    "service_name": metric["service_name"],
                    "metric": key,
                    "value": value,
                    "severity": severity
                })
        return anomalies
    
    def moving_average(self, metric_name: str) -> Optional[float]:
        """Calculate moving average for a given metric name."""
        window = self._windows.get(metric_name)
        if window and len(window) > 0:
            return sum(window) / len(window)
        return None
    
    def __len__(self) -> int:
        """Return total number of alerts detected so far."""
        return self._total_alerts

    def __repr__(self) -> str:
        return (
            f"AnomalyDetector(window_size={self._window_size}, "
            f"total_alerts={self._total_alerts})"
        )
    

# if __name__ == "__main__":
#     from generator import generate_metrics

#     detector = AnomalyDetector(window_size=5)
#     for metric in generate_metrics(num_records=20, interval=0):
#         anomalies = detector.check_anomaly(metric)

#     print(repr(detector))
#     print(f"Total alerts: {len(detector)}")
#     print(f"CPU moving avg: {detector.moving_average('cpu_percent')}")
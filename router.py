from abc import ABC, abstractmethod
from typing import Callable



class BaseHandler(ABC):
    
    @abstractmethod
    def send(self, anomaly: dict) -> None:
        ...

class SlackHandler(BaseHandler):
    def send(self, anomaly: dict) -> None:
        print(
            f"[SLACK]      #{anomaly['service_name']} — "
            f"{anomaly['metric']}={anomaly['value']} "
            f"| {anomaly['severity']} | {anomaly['timestamp']}"
        )


class PagerDutyHandler(BaseHandler):
    def send(self, anomaly: dict) -> None:
        print(
            f"[PAGERDUTY]  Incident triggered: {anomaly['service_name']} | "
            f"{anomaly['metric']}={anomaly['value']} ({anomaly['severity']})"
        )


class EmailHandler(BaseHandler):
    def send(self, anomaly: dict) -> None:
        print(
            f"[EMAIL]      Alert: {anomaly['severity']} on {anomaly['service_name']} — "
            f"{anomaly['metric']}={anomaly['value']} at {anomaly['timestamp']}"
        )


class AlertDispatcher:
    def __init__(self) -> None:
        self._handlers = {
            "slack": SlackHandler(),
            "pagerduty": PagerDutyHandler(),
            "email": EmailHandler(),
        }

    def dispatch(self, anomaly: dict, channels: list[str]) -> None:
        for channel in channels:
            handler = self._handlers.get(channel)
            if handler:
                handler.send(anomaly)

def create_alert_router(team_config: dict) -> Callable[[dict], None]:

    dispatcher = AlertDispatcher()   

    def route(anomaly: dict) -> None:
    
        service = anomaly.get("service_name", "")

        for team, config in team_config.items():
            if service in config.get("services", []):
                channels = config.get("channels", [])
                print(f"Routing anomaly for service '{service}' to team '{team}' with channels: {channels}")
                dispatcher.dispatch(anomaly, channels)
                return       # stop after finding the right team

        print(f"No team found for service: {service}")   # fallback

    return route  

if __name__ == "__main__":

    TEAM_CONFIG = {
        "infra-team": {
            "services": ["auth-service", "gateway"],
            "channels": ["slack", "pagerduty"],
        },
        "data-team": {
            "services": ["etl-service", "ml-pipeline"],
            "channels": ["slack", "email"],
        },
    }

    router = create_alert_router(TEAM_CONFIG)

    # Fake anomaly — same shape as what detector.py produces
    test_anomaly = {
        "timestamp":    "2026-05-27T10:32:01",
        "service_name": "auth-service",
        "metric":       "cpu_percent",
        "value":        95.3,
        "severity":     "WARNING",
    }

    router(test_anomaly)

    # Test unknown service
    test_anomaly["service_name"] = "unknown-service"
    router(test_anomaly)
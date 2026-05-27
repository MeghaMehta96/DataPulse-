import json
from datetime import datetime
from typing import Any

class ReportWriter:
    def __init__(self, filename: str) -> None:
        self._filename: str = filename
        self._sections: dict[str, Any] = {}
        self._generated_at: str = datetime.now().isoformat(timespec="seconds")
    def __enter__(self) -> "ReportWriter":
        return self
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._save()
        return False
    
    def add_section(self, title: str, data: Any) -> None:
        self._sections[title] = data
    def _save(self) -> None:
        report: dict[str, Any] = {
            "generated_at": self._generated_at,
            **self._sections,
        }
        try:
            with open(self._filename, "w", encoding="utf-8") as fh:
                json.dump(report, fh, indent=2)
            print(f"\n[REPORT] Saved → '{self._filename}'")
        except OSError as exc:
            print(f"[ERROR]  Failed to write report: {exc}")

if __name__ == "__main__":

    with ReportWriter("test_report.json") as writer:
        writer.add_section("total_records_processed", 50)
        writer.add_section("anomaly_summary", {
            "total_alerts": 5,
            "by_severity": {"WARNING": 3, "CRITICAL": 2},
            "by_service":  {"auth-service": 3, "gateway": 2},
            "by_metric":   {"cpu_percent": 3, "latency_ms": 2},
        })
        writer.add_section("top_5_critical_alerts", [])
        writer.add_section("moving_averages", {
            "cpu_percent":    52.3,
            "memory_percent": 61.8,
            "disk_percent":   54.2,
            "latency_ms":     145.7,
        })

    # file should now exist — open it and check
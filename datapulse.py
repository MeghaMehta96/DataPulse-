import argparse
import sys
from collections import defaultdict
from exceptions import InvalidMetricError
from generator import generate_metrics
from detector import AnomalyDetector
from router import create_alert_router
from reporter import ReportWriter


TEAM_CONFIG: dict = {
    "infra-team": {
        "services": ["auth-service", "gateway"],
        "channels": ["slack", "pagerduty"],
    },
    "data-team": {
        "services": ["etl-service", "ml-pipeline"],
        "channels": ["slack", "email"],
    },
    "payments-team": {
        "services": ["payment-service"],
        "channels": ["pagerduty", "email"],
    },
}

def _build_report_data(
    detector: AnomalyDetector,
    all_anomalies: list[dict],
    records_processed: int,
) -> dict:
    by_severity: dict[str, int] = defaultdict(int)
    by_service: dict[str, int] = defaultdict(int)
    by_metric: dict[str, int] = defaultdict(int)

    for anomaly in all_anomalies:
        by_severity[anomaly["severity"]] += 1
        by_service[anomaly["service_name"]] += 1
        by_metric[anomaly["metric"]] += 1

    critical_alerts = sorted(
        [a for a in all_anomalies if a["severity"] == "CRITICAL"],
        key=lambda x: x["value"],
        reverse=True,
    )[:5]

    moving_avgs = {
        m: detector.moving_average(m)
        for m in ["cpu_percent", "memory_percent", "disk_percent", "latency_ms"]
    }

    return {
        "total_records_processed": records_processed,
        "anomaly_summary": {
            "total_alerts": len(detector),
            "by_severity": dict(by_severity),
            "by_service": dict(by_service),
            "by_metric": dict(by_metric),
        },
        "top_5_critical_alerts": critical_alerts,
        "moving_averages": moving_avgs,
    }

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="datapulse",
        description="DataPulse — real-time system health monitoring CLI",
    )

    parser.add_argument(
        "--records", type=int, default=100, metavar="N",
        help="Number of metric records to generate (default: 100)",
    )
    parser.add_argument(
        "--interval", type=float, default=0.1, metavar="SEC",
        help="Seconds to sleep between records (default: 0.1)",
    )
    parser.add_argument(
        "--output", type=str, default="health_report.json", metavar="FILE",
        help="Output JSON report filename (default: health_report.json)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print each metric record as it is processed",
    )
    args = parser.parse_args()

    detector = AnomalyDetector(window_size=5)
    router   = create_alert_router(TEAM_CONFIG)
    all_anomalies: list[dict] = []
    records_processed: int = 0

    print(f"[DataPulse] Starting  — records={args.records}  interval={args.interval}s")
    print(f"[DataPulse] Output    → {args.output}\n")

    try:
        for metric in generate_metrics(args.records, args.interval):
            records_processed += 1
            if args.verbose:
                print(f"  [{metric['timestamp']}] {metric['service_name']:<20} ...")

            try:
                anomalies = detector.check_anomaly(metric)
                for anomaly in anomalies:
                    router(anomaly)
                    all_anomalies.extend(anomalies)

            except InvalidMetricError as exc:
                print(f"[ERROR] Invalid metric: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n[DataPulse] Interrupted by user. Generating report with collected data...")

    print(f"\n[DataPulse] Done — {records_processed} records, {len(detector)} alert(s).")
    print(repr(detector))

    report_data = _build_report_data(detector, all_anomalies, records_processed)

    with ReportWriter(args.output) as writer:
        for section, data in report_data.items():
          writer.add_section(section, data)

if __name__ == "__main__":
    main()
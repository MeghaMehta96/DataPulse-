# DataPulse

A lightweight, real-time system health monitoring CLI tool that simulates CPU, Memory, Disk, and Latency metrics, detects anomalies against configurable thresholds, routes alerts to the correct team channels, and saves a JSON summary report.

## How to run

```bash
cd datapulse_v1
python datapulse.py --records 100 --interval 0.1
python datapulse.py --records 50 --interval 0 --output report.json --verbose
```

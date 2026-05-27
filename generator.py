import random
import time
from datetime import datetime
from typing import Generator

services = [
    "auth-service",
    "gateway",
    "etl-service",
    "ml-pipeline",
    "payment-service",

]

def generate_metrics(num_records: int, interval: float) -> Generator[dict, None, None]:
  for _ in range(num_records):
    is_spike = random.random() < 0.10

    if is_spike:
      cpu = round(random.uniform(88.0, 100.0), 1)
      memory = round(random.uniform(80.0, 100.0), 1)
      disk = round(random.uniform(85.0, 100.0), 1)
      latency = round(random.uniform(900.0, 1600.0), 1)

    else:
      cpu = round(max(0.0, min(87.0, random.gauss(45.0, 15.0))), 1)
      memory = round(max(0.0, min(84.0, random.gauss(60.0, 12.0))), 1)
      disk = round(max(0.0, min(89.0, random.gauss(55.0, 10.0))), 1)
      latency = round(max(10.0, min(799.0, random.gauss(150.0, 60.0))), 1)      
    
    yield {
      "timestamp": datetime.now().isoformat(timespec="seconds"),
      "service": random.choice(services),
      "cpu": cpu,
      "memory": memory,
      "disk": disk,
      "latency": latency
    }

    if interval > 0:
        time.sleep(interval)

if __name__ == "__main__":
    for metric in generate_metrics(num_records=5, interval=0):
        print(metric)
    


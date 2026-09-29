from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio
from app.metrics import percentile


INCIDENT_START = datetime.fromisoformat("2026-09-29T09:06:12+00:00")
INCIDENT_END = datetime.fromisoformat("2026-09-29T09:06:28+00:00")
SLO_LATENCY_MS = 3000
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"


def main() -> None:
    configure_utf8_stdio()
    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("event") != "response_sent":
            continue
        timestamp = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
        if INCIDENT_START <= timestamp <= INCIDENT_END:
            records.append(record)

    latencies = [float(record["latency_ms"]) for record in records]
    ttfts = [float(record["ttft_ms"]) for record in records]
    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    ttft_p95 = percentile(ttfts, 95)

    print("=" * 76)
    print("CP3 INCIDENT METRIC EVIDENCE")
    print("Challenge ID : day13-k4-l3a-monitoring-llmops-v1")
    print("Panel        : Latency percentiles and TTFT")
    print("Time range   : 2026-09-29 09:06:12--09:06:27 UTC")
    print(f"Requests     : {len(records)}")
    print(f"Latency      : P50={p50:.0f} ms | P95={p95:.0f} ms | P99={p99:.0f} ms")
    print(f"TTFT         : P95={ttft_p95:.0f} ms")
    print(f"SLO line     : P95 <= {SLO_LATENCY_MS} ms")
    print(f"Status       : {'BREACHED' if p95 > SLO_LATENCY_MS else 'OK'}")
    print("=" * 76)


if __name__ == "__main__":
    main()

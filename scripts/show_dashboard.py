from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio
from app.dashboard import dashboard_metrics, load_recent_records


def main() -> None:
    configure_utf8_stdio()
    records = load_recent_records(minutes=60)
    metric = dashboard_metrics(records)

    panels = (
        (
            "1. Latency percentiles and TTFT",
            f"P50={metric['latency_p50']:.0f}, P95={metric['latency_p95']:.0f}, "
            f"P99={metric['latency_p99']:.0f}, TTFT P95={metric['ttft_p95']:.0f}",
            "ms",
            "P95 <= 3000 ms",
        ),
        (
            "2. Request traffic",
            f"count={metric['request_count']}, rate={metric['rate_per_minute']:.2f}",
            "requests / requests_per_minute",
            "rate >= 1 request/min",
        ),
        (
            "3. Error rate and retrieval success",
            f"error_rate={metric['error_rate']:.2f}, "
            f"retrieval_success={metric['retrieval_success']:.2f}, "
            f"breakdown={json.dumps(metric['error_breakdown'])}",
            "percent",
            "error_rate <= 2%",
        ),
        (
            "4. Cost over time",
            f"total=${metric['cost']:.6f}",
            "USD / 60 minutes",
            "total <= $2.50",
        ),
        (
            "5. Input and output tokens",
            f"input={metric['tokens_in']}, output={metric['tokens_out']}",
            "tokens",
            "total <= 50000 tokens",
        ),
        (
            "6. Quality proxy",
            f"average={metric['quality']:.2f}",
            "score 0..1",
            "average >= 0.75",
        ),
    )

    print("=" * 78)
    print("K4-L3A MONITORING & LLMOPS DASHBOARD")
    print("Source: data/logs.jsonl | Time range: last 60 minutes | Refresh: manual")
    print(f"Log records in window: {len(records)}")
    print("=" * 78)
    for title, value, unit, threshold in panels:
        print(f"\n{title}")
        print(f"  Value     : {value}")
        print(f"  Unit      : {unit}")
        print(f"  Threshold : {threshold}")
    print("\n" + "=" * 78)
    print("Panels: 6/6")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path


LOG_PATH = Path("data/logs.jsonl")
CORRELATION_ID = "req-5b00f9eb"
DISPLAY_FIELDS = (
    "ts",
    "event",
    "correlation_id",
    "feature",
    "model",
    "latency_ms",
    "ttft_ms",
    "tool_name",
    "tool_success",
)


def main() -> None:
    records = [
        json.loads(line)
        for line in LOG_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    matches = [
        record for record in records if record.get("correlation_id") == CORRELATION_ID
    ]

    print("=" * 76)
    print("CP3 INCIDENT LOG EVIDENCE")
    print(f"Correlation ID: {CORRELATION_ID}")
    print("=" * 76)
    for record in matches:
        safe_record = {
            field: record[field] for field in DISPLAY_FIELDS if field in record
        }
        print(json.dumps(safe_record, ensure_ascii=False, indent=2))
    print("=" * 76)
    print(f"Matched events: {len(matches)}")


if __name__ == "__main__":
    main()

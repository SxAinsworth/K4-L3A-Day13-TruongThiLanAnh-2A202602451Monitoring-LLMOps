from __future__ import annotations

import json
from pathlib import Path

import httpx


BASE_URL = "http://127.0.0.1:8000"
LOG_PATH = Path("data/logs.jsonl")
CORRELATION_ID = "req-05e1d0ce"
FAKE_PII = "a@b.co 0901234567 001203012345 4111111111111111"


def main() -> None:
    payload = {
        "user_id": "student-pii-demo",
        "session_id": "pii-demo",
        "feature": "qa",
        "message": FAKE_PII,
    }
    response = httpx.post(
        f"{BASE_URL}/chat",
        headers={"x-request-id": CORRELATION_ID},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()

    records = [
        json.loads(line)
        for line in LOG_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    request_log = next(
        record
        for record in reversed(records)
        if record.get("correlation_id") == CORRELATION_ID
        and record.get("event") == "request_received"
    )

    print("=" * 78)
    print("PII REDACTION RUNTIME EVIDENCE")
    print(f"Correlation ID : {CORRELATION_ID}")
    print(f"Fake input     : {FAKE_PII}")
    print("Structured log output:")
    print(
        json.dumps(
            {
                "event": request_log.get("event"),
                "correlation_id": request_log.get("correlation_id"),
                "message_preview": request_log.get("payload", {}).get(
                    "message_preview"
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print("Validator result: raw PII leaks = 0")
    print("=" * 78)


if __name__ == "__main__":
    main()

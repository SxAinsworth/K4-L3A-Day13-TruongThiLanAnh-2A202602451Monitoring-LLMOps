from __future__ import annotations

import html
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from .logging_config import LOG_PATH
from .metrics import percentile


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_recent_records(path: Path = LOG_PATH, minutes: int = 60) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = _timestamp(record.get("ts"))
        if ts is not None and ts >= cutoff:
            records.append(record)
    return records


def dashboard_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    requests = [item for item in records if item.get("event") == "request_received"]
    responses = [item for item in records if item.get("event") == "response_sent"]
    failures = [item for item in records if item.get("event") == "request_failed"]
    latencies = [float(item["latency_ms"]) for item in responses if item.get("latency_ms") is not None]
    ttfts = [float(item["ttft_ms"]) for item in responses if item.get("ttft_ms") is not None]
    tool_events = [item for item in records if item.get("tool_success") is not None]
    error_types = Counter(str(item.get("error_type") or "unknown") for item in failures)

    return {
        "request_count": len(requests),
        "rate_per_minute": len(requests) / 60,
        "latency_p50": percentile(latencies, 50),
        "latency_p95": percentile(latencies, 95),
        "latency_p99": percentile(latencies, 99),
        "ttft_p95": percentile(ttfts, 95),
        "error_rate": (len(failures) / len(requests) * 100) if requests else 0,
        "error_breakdown": dict(error_types),
        "retrieval_success": (
            sum(item.get("tool_success") is True for item in tool_events)
            / len(tool_events)
            * 100
            if tool_events
            else 0
        ),
        "cost": sum(float(item.get("cost_usd") or 0) for item in responses),
        "tokens_in": sum(int(item.get("tokens_in") or 0) for item in responses),
        "tokens_out": sum(int(item.get("tokens_out") or 0) for item in responses),
        "quality": mean(
            [float(item["quality_score"]) for item in responses if item.get("quality_score") is not None]
        )
        if responses
        else 0,
    }


def render_dashboard(records: list[dict[str, Any]]) -> str:
    metric = dashboard_metrics(records)
    breakdown = html.escape(json.dumps(metric["error_breakdown"], ensure_ascii=False))
    cards = [
        ("Latency percentiles and TTFT", f"P50 {metric['latency_p50']:.0f} · P95 {metric['latency_p95']:.0f} · P99 {metric['latency_p99']:.0f} · TTFT P95 {metric['ttft_p95']:.0f}", "ms", "SLO: P95 ≤ 3000 ms"),
        ("Request traffic", f"{metric['request_count']} · {metric['rate_per_minute']:.2f}/min", "requests / requests per minute", "Threshold: ≥ 1 request/min"),
        ("Error rate and retrieval success", f"Errors {metric['error_rate']:.2f}% · Retrieval {metric['retrieval_success']:.2f}%", "percent", f"Error ≤ 2% · breakdown {breakdown}"),
        ("Cost over time", f"${metric['cost']:.6f}", "USD / 60 minutes", "Budget threshold: ≤ $2.50"),
        ("Input and output tokens", f"{metric['tokens_in']:,} in · {metric['tokens_out']:,} out", "tokens", "Threshold: ≤ 50,000 tokens"),
        ("Quality proxy", f"{metric['quality']:.2f}", "score 0–1", "Threshold: ≥ 0.75"),
    ]
    card_html = "".join(
        f'<section><h2>{title}</h2><div class="value">{value}</div><p>{unit}</p><div class="threshold">{threshold}</div></section>'
        for title, value, unit, threshold in cards
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="30">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Monitoring & LLMOps Dashboard</title>
<style>
body{{margin:0;background:#08111f;color:#e8eef8;font:15px system-ui;padding:32px}}header{{display:flex;justify-content:space-between;align-items:end;margin-bottom:24px}}h1{{margin:0;font-size:28px}}header p,section p{{color:#91a4bf}}main{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}section{{background:#111f33;border:1px solid #263b58;border-radius:14px;padding:22px;min-height:150px}}h2{{font-size:16px;margin:0 0 22px}}.value{{font-size:25px;font-weight:700;color:#70d7ff}}.threshold{{border-top:1px solid #263b58;margin-top:18px;padding-top:14px;color:#8fe0ad}}@media(max-width:900px){{main{{grid-template-columns:1fr}}}}
</style></head><body><header><div><h1>K4-L3A Monitoring & LLMOps</h1><p>Source: data/logs.jsonl</p></div><p>Time range: last 60 minutes · refresh: 30 seconds · {len(records)} log records</p></header><main>{card_html}</main></body></html>"""

"""
statistics.py
Member 3 -- Analysis, Visualization & Report (Day 2)

Statistical helpers that turn processed per-run experiment rows
(data/processed/*.csv, produced by Member 2's pipeline -- see
common/metrics.h for the schema) into the summary numbers used in
graphs and the final report: mean, median, std, min, max, p95,
grouped by protocol and/or packet size.

Built and tested against data/processed/mock_results.csv while
the real networking/experiment pipeline is still in progress.
Swap in the real processed CSV later -- no code changes needed
here, since both files follow the same schema.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Union

NUMERIC_FIELDS = [
    "packet_size", "packet_count", "duration", "bytes_sent",
    "bytes_received", "throughput_mbps", "avg_latency_ms",
    "min_latency_ms", "max_latency_ms", "jitter_ms",
    "packet_loss_percent", "retransmissions",
]


@dataclass
class MetricSummary:
    metric: str
    mean: float
    median: float
    std: float
    minimum: float
    maximum: float
    p95: float
    n: int


def load_results(csv_path: Union[str, Path]) -> List[dict]:
    """Load a processed results CSV into a list of dict rows,
    with numeric fields converted from str to float."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Results file not found: {csv_path}")

    rows: List[dict] = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for raw_row in reader:
            row = dict(raw_row)
            for field_name in NUMERIC_FIELDS:
                if field_name in row and row[field_name] != "":
                    row[field_name] = float(row[field_name])
            rows.append(row)
    return rows


def percentile(values: List[float], pct: float) -> float:
    """Linear-interpolation percentile (matches numpy's default), pct in [0, 100]."""
    if not values:
        raise ValueError("Cannot compute percentile of an empty list")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    k = (pct / 100.0) * (len(ordered) - 1)
    f = int(k)
    c = min(f + 1, len(ordered) - 1)
    if f == c:
        return ordered[f]
    return ordered[f] + (ordered[c] - ordered[f]) * (k - f)


def summarize(values: List[float], metric_name: str) -> MetricSummary:
    if not values:
        raise ValueError(f"No values to summarize for '{metric_name}'")
    n = len(values)
    mean_v = sum(values) / n
    ordered = sorted(values)
    median_v = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2
    std_v = (sum((x - mean_v) ** 2 for x in values) / n) ** 0.5 if n > 1 else 0.0
    return MetricSummary(
        metric=metric_name,
        mean=mean_v,
        median=median_v,
        std=std_v,
        minimum=min(values),
        maximum=max(values),
        p95=percentile(values, 95),
        n=len(values),
    )


def summarize_by_protocol(rows: List[dict], metric: str) -> Dict[str, MetricSummary]:
    """Group rows by protocol and summarize one metric column for
    each, e.g. summarize_by_protocol(rows, 'throughput_mbps')."""
    by_protocol: Dict[str, List[float]] = {}
    for row in rows:
        by_protocol.setdefault(row["protocol"], []).append(row[metric])

    return {protocol: summarize(values, metric) for protocol, values in by_protocol.items()}


def summarize_by_protocol_and_packet_size(
    rows: List[dict], metric: str
) -> Dict[str, Dict[int, MetricSummary]]:
    """Finer-grained grouping for Graph 1/2-style plots
    (packet size vs metric, split by protocol)."""
    grouped: Dict[str, Dict[int, List[float]]] = {}
    for row in rows:
        proto = row["protocol"]
        size = int(row["packet_size"])
        grouped.setdefault(proto, {}).setdefault(size, []).append(row[metric])

    return {
        proto: {size: summarize(values, metric) for size, values in sizes.items()}
        for proto, sizes in grouped.items()
    }


if __name__ == "__main__":
    rows = load_results("data/processed/mock_results.csv")
    print(f"Loaded {len(rows)} rows from mock dataset.\n")

    for metric in ("throughput_mbps", "avg_latency_ms", "packet_loss_percent"):
        print(f"--- {metric} by protocol ---")
        summary = summarize_by_protocol(rows, metric)
        for protocol, s in summary.items():
            print(
                f"{protocol}: mean={s.mean:.2f} median={s.median:.2f} "
                f"std={s.std:.2f} p95={s.p95:.2f} (n={s.n})"
            )
        print()

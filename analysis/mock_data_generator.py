"""
mock_data_generator.py
Member 3 -- Analysis, Visualization & Report (Day 2)

Generates data/processed/mock_results.csv in the exact schema the
real pipeline will produce (see common/metrics.h / config/experiments.yaml
output.csv_schema), with plausible-but-fabricated numbers so
statistics.py can be built and tested before the networking and
experiment-runner pipeline (Members 1 and 2) is finished.

This file must never be cited in the final report -- it exists
purely to unblock analysis/visualization development. Swap in the
real data/processed CSV once Members 1 and 2 finish; no analysis
code changes needed.
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

FIELDNAMES = [
    "experiment_id", "protocol", "packet_size", "packet_count", "duration",
    "bytes_sent", "bytes_received", "throughput_mbps", "avg_latency_ms",
    "min_latency_ms", "max_latency_ms", "jitter_ms", "packet_loss_percent",
    "retransmissions", "timestamp",
]

PACKET_SIZES = [64, 128, 256, 512, 1024, 4096]
PACKET_COUNTS = [1000, 5000, 10000]
DURATION = 10
REPETITIONS = 5


def _simulate_run(protocol: str, packet_size: int, packet_count: int, rep: int, rng: random.Random) -> dict:
    """Fabricate one plausible experiment row.

    Rough model, tuned only to look directionally realistic for
    early dashboard/graph development:
      - UDP throughput scales closer to line rate, TCP a bit lower
        due to ack/handshake overhead, more so at small packet sizes.
      - TCP latency is slightly higher (ack round trip) but has ~0%
        loss; UDP has near-0 loss on a quiet LAN but isn't guaranteed.
      - Jitter is a small fraction of latency, noisier for UDP.
    """
    bytes_total = packet_size * packet_count

    base_throughput = 940.0 * (packet_size / (packet_size + 54))  # header overhead approximation
    if protocol == "TCP":
        throughput = base_throughput * rng.uniform(0.80, 0.90)
        base_latency = rng.uniform(0.8, 2.5) + (64 / packet_size) * 0.3
        loss_percent = 0.0
        retransmissions = rng.choice([0, 0, 0, 1, 2])
    else:
        throughput = base_throughput * rng.uniform(0.92, 1.02)
        base_latency = rng.uniform(0.5, 1.8)
        loss_percent = round(rng.uniform(0.0, 0.6), 3)
        retransmissions = 0  # UDP has no retransmission mechanism

    avg_latency = round(base_latency, 3)
    min_latency = round(avg_latency * rng.uniform(0.5, 0.7), 3)
    max_latency = round(avg_latency * rng.uniform(2.5, 5.0), 3)
    jitter = round(avg_latency * rng.uniform(0.05, 0.25), 3)

    bytes_received = int(bytes_total * (1 - loss_percent / 100.0))
    timestamp = date(2026, 9, 20) + timedelta(days=rep - 1)

    return {
        "experiment_id": f"{protocol}_{packet_size}B_{packet_count}pk_d{DURATION}s_r{rep}",
        "protocol": protocol,
        "packet_size": packet_size,
        "packet_count": packet_count,
        "duration": DURATION,
        "bytes_sent": bytes_total,
        "bytes_received": bytes_received,
        "throughput_mbps": round(throughput, 2),
        "avg_latency_ms": avg_latency,
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency,
        "jitter_ms": jitter,
        "packet_loss_percent": loss_percent,
        "retransmissions": retransmissions,
        "timestamp": timestamp.isoformat(),
    }


def generate_mock_dataset(output_path: str = "data/processed/mock_results.csv", seed: int = 42) -> int:
    rng = random.Random(seed)
    rows = []
    for protocol in ("TCP", "UDP"):
        for packet_size in PACKET_SIZES:
            for packet_count in PACKET_COUNTS:
                for rep in range(1, REPETITIONS + 1):
                    rows.append(_simulate_run(protocol, packet_size, packet_count, rep, rng))

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


if __name__ == "__main__":
    n = generate_mock_dataset()
    print(f"Wrote {n} mock rows to data/processed/mock_results.csv")

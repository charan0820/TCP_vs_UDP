"""Reproducible NS-3 parameter sweeps. Run from any working directory."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import uuid
import yaml
from experiments.ns3_backend import Ns3Backend, ROOT
from metrics.collector import collect
from experiments.topology import normalize, resolve, fingerprint

DEFAULT = ROOT / "config" / "demo.yaml"


def load_plan(path):
    raw = yaml.safe_load(Path(path).read_text())
    if not isinstance(raw, dict):
        raise ValueError("Configuration must be a mapping")
    exp = raw.get("experiments", {})
    dimensions = {}
    for key, fallback in [("protocols", ["TCP"]), ("packet_sizes", [1024]),
                          ("packet_counts", [10000]), ("duration_seconds", [5]),
                          ("rates_mbps", [20])]:
        dimensions[key] = exp.get(key, fallback)
        if not isinstance(dimensions[key], list) or not dimensions[key]:
            raise ValueError(f"{key} must be a nonempty list")
    reps = exp.get("repetitions", 3)
    if type(reps) is not int or not 1 <= reps <= 100:
        raise ValueError("repetitions must be an integer from 1 to 100")
    conditions = raw.get("conditions", [{"name": "baseline", "delay_ms": 10, "loss_percent": 0, "bandwidth_mbps": 10}])
    if not isinstance(conditions, list) or not conditions:
        raise ValueError("conditions must be a nonempty list")
    plan = []
    topology=normalize(raw["topology"]) if "topology" in raw else None
    for proto, size, count, duration, rate, condition, rep in itertools.product(
        *dimensions.values(), conditions, range(1, reps+1)
    ):
        if not isinstance(condition, dict):
            raise ValueError("Each condition must be a mapping")
        settings = dict(protocol=proto, size=size, count=count, duration=duration, rate=rate,
                        delay=condition.get("delay_ms", 10), loss=condition.get("loss_percent", 0),
                        bandwidth=condition.get("bandwidth_mbps", 10), drain=raw.get("drain_seconds", 3),
                        queue=raw.get("queue_packets", 100), seed=raw.get("seed", 42), run=rep,
                        tcp=raw.get("tcp_algorithm", "TcpNewReno"), pcap=int(bool(raw.get("pcap", False))))
        validate(settings)
        settings.update(packetTraceLimit=raw.get("packet_trace_limit",50000),netanim=int(bool(raw.get("netanim",False))))
        if type(settings["packetTraceLimit"]) is not int or not 0<=settings["packetTraceLimit"]<=1_000_000:
            raise ValueError("packet_trace_limit must be an integer from 0 to 1000000")
        if topology is not None: settings["topology"]=topology
        settings["topology_id"]=fingerprint(resolve(topology,settings))
        plan.append((str(condition.get("name", "condition")), settings))
    return raw, plan


def validate(s):
    if s["protocol"] not in ("TCP", "UDP") or s["tcp"] not in ("TcpNewReno", "TcpCubic"):
        raise ValueError("Unsupported protocol or TCP algorithm")
    for key in ("size", "count", "queue", "seed", "run"):
        if type(s[key]) is not int or s[key] <= 0:
            raise ValueError(f"{key} must be a positive integer")
    if s["size"] > 8192 or s["size"]*s["count"] > 1_000_000_000:
        raise ValueError("Payload limit is 8192 bytes; run data limit is 1 GB (sequence-wrap protection)")
    for key in ("duration", "rate", "delay", "loss", "bandwidth", "drain"):
        value = s[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{key} must be a finite number")
        if value < 0 or (key not in ("delay", "loss") and value == 0):
            raise ValueError(f"Invalid {key}")
    if s["loss"] >= 100:
        raise ValueError("loss must be less than 100 percent")


def run_suite(config=DEFAULT, output=None, progress=None):
    raw, plan = load_plan(config)
    backend = Ns3Backend()
    version = backend.version()
    batch = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex[:6]
    destination = Path(output) if output else ROOT / "data" / "runs" / batch
    destination.mkdir(parents=True, exist_ok=False)
    manifest = dict(batch=batch, timestamp=datetime.now(timezone.utc).isoformat(), ns3_version=version,
                    configuration=raw, planned_runs=len(plan), completed_runs=0, status="running",
                    simulation_sha256=hashlib.sha256((ROOT/"simulation/tcp_udp.cc").read_bytes()).hexdigest())
    if raw.get("replay_of_batches"):manifest["replay_of_batches"]=raw["replay_of_batches"]
    if backend.binary.is_file():
        manifest["binary_sha256"] = hashlib.sha256(backend.binary.read_bytes()).hexdigest()
    manifest_path = destination / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    rows = []
    try:
        for index, (name, settings) in enumerate(plan, 1):
            experiment_id = f"{batch}-{index:04d}"
            prefix = destination / f"run-{index:04d}"
            stdout = backend.run(settings, prefix)
            Path(str(prefix)+"-stdout.txt").write_text(stdout)
            row = collect(prefix, settings)
            from visualization.packets import packet_spans, playback_html
            packet_file=Path(str(prefix)+"-packets.csv")
            if packet_file.exists():
                spans,total=packet_spans(packet_file)
                Path(str(prefix)+"-playback.html").write_text(playback_html(
                    resolve(settings.get("topology"),settings),spans,total,row["packet_trace_truncated"]),encoding="utf-8")
            row.update(experiment_id=experiment_id, condition=name, timestamp=manifest["timestamp"], ns3_version=version)
            rows.append(row)
            with (destination/"results.csv").open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader(); writer.writerows(rows)
            (destination/"results.json").write_text(json.dumps(rows, indent=2, allow_nan=False))
            manifest["completed_runs"] = index
            manifest_path.write_text(json.dumps(manifest, indent=2))
            if progress:
                progress(index, len(plan), row)
        manifest["status"] = "complete"
    except Exception as exc:
        manifest.update(status="failed", error=str(exc))
        raise
    finally:
        manifest_path.write_text(json.dumps(manifest, indent=2))
    from analysis.report import generate
    generate(destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    try:
        if args.plan:
            _, plan = load_plan(args.config)
            print(json.dumps(plan, indent=2)); print(f"{len(plan)} runs")
        else:
            result = run_suite(args.config, args.output, lambda i,n,r: print(f"[{i}/{n}] {r['protocol']} {r['condition']}: {r['throughput_mbps']:.3f} Mbps", flush=True))
            print(f"Results: {result}")
    except (ValueError, RuntimeError, OSError) as exc:
        parser.exit(1, f"{exc}\nSee docs/ns3-setup.md\n")


if __name__ == "__main__":
    main()

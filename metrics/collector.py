"""Convert NS-3 event traces to explicit, application-level run metrics."""
import csv
import json
from pathlib import Path
from analysis.statistics import percentile


def collect(prefix, settings):
    prefix = Path(prefix)
    summary = json.loads(Path(str(prefix) + "-summary.json").read_text())
    with Path(str(prefix) + "-events.csv").open(newline="") as f:
        events = list(csv.DictReader(f))
    delays = [float(e["value"]) for e in events if e["event"] == "delivery_ms"]
    sent = summary["messages_sent"]
    delivered = summary["messages_received"]
    window = settings["duration"] + settings["drain"]
    missing = max(0, sent-delivered)
    row = dict(settings)
    row.pop("topology",None)
    row.setdefault("topology_id","legacy-direct")
    row.update(
        backend="ns3", latency_kind="one_way_application_delivery", packet_size=settings["size"],
        packet_count=settings["count"], messages_sent=sent, messages_received=delivered,
        bytes_sent=sent*settings["size"], bytes_received=summary["bytes_received"],
        observation_seconds=window,
        throughput_mbps=summary["bytes_received"]*8/window/1e6,
        avg_latency_ms=sum(delays)/len(delays) if delays else None,
        median_latency_ms=percentile(delays, 50) if delays else None,
        p95_latency_ms=percentile(delays, 95) if delays else None,
        min_latency_ms=min(delays) if delays else None,
        max_latency_ms=max(delays) if delays else None,
        jitter_ms=sum(abs(b-a) for a, b in zip(delays, delays[1:]))/(len(delays)-1) if len(delays)>1 else None,
        packet_loss_percent=missing/sent*100 if sent else None,
        retransmissions=summary["retransmissions"] if settings["protocol"]=="TCP" else None,
        retransmitted_bytes=summary["retransmitted_bytes"] if settings["protocol"]=="TCP" else None,
        total_transfer_time_s=summary["last_delivery_s"]-1 if delivered else None,
        complete=sent==settings["count"] and delivered==sent,
        packet_trace_truncated=summary.get("packet_trace_truncated",False),
    )
    return row

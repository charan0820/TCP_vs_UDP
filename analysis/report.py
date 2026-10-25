"""Generate report and figures from one measured batch, preserving conditions."""
import csv
from dataclasses import asdict
import json
from pathlib import Path
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from analysis.statistics import summarize

METRICS = {
    "throughput_mbps": "Payload goodput (Mbps)",
    "avg_latency_ms": "Mean application delivery delay (ms)",
    "jitter_ms": "Mean absolute consecutive delay change (ms)",
    "packet_loss_percent": "Undelivered messages at cutoff (%)",
    "retransmissions": "TCP retransmitted data segments",
}
GROUP = ["protocol", "condition", "size", "count", "duration", "rate", "delay", "loss", "bandwidth", "drain", "queue", "tcp", "topology_id"]


def generate(folder):
    folder = Path(folder)
    rows = json.loads((folder/"results.json").read_text())
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row.get(k,"legacy-direct") for k in GROUP)].append(row)
    summaries = []
    for key, runs in groups.items():
        for metric in METRICS:
            values = [r[metric] for r in runs if r[metric] is not None]
            if values:
                summaries.append(dict(zip(GROUP, key), **asdict(summarize(values, metric))))
    with (folder/"statistics.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summaries[0]))
        writer.writeheader(); writer.writerows(summaries)
    lines = ["# TCP / UDP measured simulation report", "", "Source: real NS-3 runs. See manifest.json for versions, configuration, seed and source hash.", "",
             "Goodput uses received payload bytes divided by generation + drain time. Delivery delay is one-way application delay, including buffering and reassembly; it is not RTT.", "",
             "| Protocol | Condition | Payload B | Rate Mbps | Metric | Mean | Median | Std (population) | P95 across runs | n |",
             "|---|---|---:|---:|---|---:|---:|---:|---:|---:|"]
    for s in summaries:
        lines.append(f"| {s['protocol']} | {s['condition']} | {s['size']} | {s['rate']} | {s['metric']} | {s['mean']:.3f} | {s['median']:.3f} | {s['std']:.3f} | {s['p95']:.3f} | {s['n']} |")
    lines += ["", "Per-message p95 delay is stored separately in results.csv. P95 in this table describes the distribution of run summaries.", "",
              "## Observations", ""]
    for key, runs in groups.items():
        complete = sum(bool(r["complete"]) for r in runs)
        recovered = sum(r["messages_received"]==r["messages_sent"] for r in runs)
        sent = sum(r["messages_sent"] for r in runs)/len(runs)
        delivered = sum(r["messages_received"] for r in runs)/len(runs)
        goodput = sum(r["throughput_mbps"] for r in runs)/len(runs)
        lines.append(f"- {key[0]}, {key[1]}, {key[2]} B, {key[5]} Mbps offered: mean goodput {goodput:.3f} Mbps; mean {sent:.1f} messages sent and {delivered:.1f} delivered. {recovered}/{len(runs)} runs delivered every complete sent message; {complete}/{len(runs)} delivered the full requested count within the observation window.")
    lines += ["", "## Interpretation limits", "", "A missing TCP message is undelivered at the finite observation cutoff; it does not establish permanent TCP loss. A run can stop generating before the requested count because of duration or backpressure. Zero deliveries produce missing latency, never zero latency. UDP does not have transport retransmissions. Packet loss settings apply independently to received link packets in both directions, including ACKs. Large UDP messages can fragment. CPU cost is not measured; simulator wall time is not endpoint CPU usage.", "", "Random run numbers differ across repetitions. Multiple protocols and conditions share run numbers for reproducibility, not identical packet loss sequences. Conclusions apply only to the configured topology and workload."]
    (folder/"report.md").write_text("\n".join(lines), encoding="utf-8")
    for metric, title in METRICS.items():
        selected = [s for s in summaries if s["metric"]==metric]
        if not selected:
            continue
        fig, ax = plt.subplots(figsize=(max(8, len(selected)*.9), 4.6))
        labels = [f"{s['protocol']} / {s['condition']}\n{s['size']} B / {s['rate']} Mbps" for s in selected]
        ax.bar(range(len(selected)), [s["mean"] for s in selected], yerr=[s["std"] for s in selected],
               color=["#116466" if s["protocol"]=="TCP" else "#c76b31" for s in selected], capsize=4)
        ax.set_xticks(range(len(selected)), labels, fontsize=8)
        ax.set_ylabel(title); ax.set_title("Measured NS-3 results · mean ± population standard deviation")
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout(); fig.savefig(folder/f"{metric}.png", dpi=160); plt.close(fig)
    return summaries

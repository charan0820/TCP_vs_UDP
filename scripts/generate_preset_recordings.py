"""Create reproducible TCP/UDP packet demonstrations for all editor presets."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml
from experiments.ns3_backend import ROOT
from experiments.topology import preset
from experiments.experiment_runner import run_suite

PRESETS = ("Direct link", "Routed bottleneck", "Star", "Diamond")


def configuration(name):
    topology = preset(name)
    for link in topology["links"]:
        bandwidth = 100 if name == "Routed bottleneck" and link["source"] != 1 else 10
        link.update(bandwidth_mbps=bandwidth, delay_ms=10, loss_percent=0, queue_packets=100)
    return dict(
        experiments=dict(protocols=["TCP", "UDP"], packet_sizes=[1024],
                         packet_counts=[400], duration_seconds=[3], rates_mbps=[5], repetitions=1),
        conditions=[dict(name="clean", delay_ms=10, loss_percent=0, bandwidth_mbps=10),
                    dict(name="impaired", delay_ms=10, loss_percent=2, bandwidth_mbps=10)],
        drain_seconds=5, queue_packets=100, seed=42, tcp_algorithm="TcpNewReno",
        packet_trace_limit=50000, pcap=False, netanim=False, topology=topology,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Run NS-3 after writing the four configurations")
    args = parser.parse_args()
    folder = ROOT / "config" / "presets"
    folder.mkdir(parents=True, exist_ok=True)
    for name in PRESETS:
        path = folder / (name.lower().replace(" ", "-") + ".yaml")
        path.write_text(yaml.safe_dump(configuration(name), sort_keys=False), encoding="utf-8")
        print(f"{name}: {path} (TCP/UDP, clean/impaired)", flush=True)
        if args.run:
            destination = run_suite(path, progress=lambda i,n,r: print(
                f"  [{i}/{n}] {r['protocol']} {r['condition']}", flush=True))
            print(f"  Recordings: {destination}", flush=True)


if __name__ == "__main__":
    main()

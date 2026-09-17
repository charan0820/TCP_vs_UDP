"""
experiment_config.py
Member 2 -- Experiment & Metrics Engine (Day 2)

Loads config/experiments.yaml, validates it, and exposes:
  - a typed ExperimentConfig object
  - an iterator over every (protocol, packet_size, packet_count,
    duration, network_condition, repetition) combination the
    runner needs to execute

Nothing about packet sizes, counts, durations, or repetitions is
hard-coded here -- it all comes from the YAML file, per the
project principle of fully configurable experimental variables.
Member 2 consumes Member 1's networking code through its CLI
(tcp_server/tcp_client/udp_server/udp_client argv), never by
importing or modifying files under client/, server/, or common/.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Union

import yaml


@dataclass
class ServerConfig:
    address: str
    tcp_port: int
    udp_port: int


@dataclass
class NetworkCondition:
    delay_ms: int = 0
    loss_percent: float = 0.0
    bandwidth_mbps: float = 0.0

    @property
    def is_baseline(self) -> bool:
        return self.delay_ms == 0 and self.loss_percent == 0.0 and self.bandwidth_mbps == 0.0


@dataclass
class OutputConfig:
    raw_dir: str
    processed_dir: str
    csv_schema: List[str]


@dataclass
class ExperimentCondition:
    """One fully-specified experiment run the runner will execute."""
    protocol: str
    packet_size: int
    packet_count: int
    duration_seconds: int
    repetition: int
    network_condition: NetworkCondition = field(default_factory=NetworkCondition)

    @property
    def experiment_id(self) -> str:
        return (
            f"{self.protocol}_{self.packet_size}B_{self.packet_count}pk_"
            f"d{self.duration_seconds}s_r{self.repetition}"
        )


@dataclass
class ExperimentConfig:
    server: ServerConfig
    protocols: List[str]
    packet_sizes: List[int]
    packet_counts: List[int]
    duration_seconds: List[int]
    repetitions: int
    network_conditions: List[NetworkCondition]
    output: OutputConfig

    # ------------------------------------------------------------
    # Loading / validation
    # ------------------------------------------------------------
    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "ExperimentConfig":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r") as f:
            raw = yaml.safe_load(f)

        return cls._from_dict(raw)

    @classmethod
    def _from_dict(cls, raw: dict) -> "ExperimentConfig":
        server_raw = raw.get("server", {})
        server = ServerConfig(
            address=server_raw.get("address", "127.0.0.1"),
            tcp_port=int(server_raw.get("tcp_port", 5001)),
            udp_port=int(server_raw.get("udp_port", 5002)),
        )

        exp_raw = raw.get("experiments", {})
        protocols = list(exp_raw.get("protocols", []))
        packet_sizes = list(exp_raw.get("packet_sizes", []))
        packet_counts = list(exp_raw.get("packet_counts", []))
        duration_seconds = list(exp_raw.get("duration_seconds", []))
        repetitions = int(exp_raw.get("repetitions", 1))

        network_conditions = cls._build_network_conditions(raw.get("network_conditions", {}))

        out_raw = raw.get("output", {})
        output = OutputConfig(
            raw_dir=out_raw.get("raw_dir", "data/raw"),
            processed_dir=out_raw.get("processed_dir", "data/processed"),
            csv_schema=list(out_raw.get("csv_schema", [])),
        )

        cfg = cls(
            server=server,
            protocols=protocols,
            packet_sizes=packet_sizes,
            packet_counts=packet_counts,
            duration_seconds=duration_seconds,
            repetitions=repetitions,
            network_conditions=network_conditions,
            output=output,
        )
        cfg.validate()
        return cfg

    @staticmethod
    def _build_network_conditions(nc_raw: dict) -> List[NetworkCondition]:
        """Cross product of any configured delay/loss/bandwidth values.
        All-empty lists mean 'no impairment configured yet' -> a single
        baseline condition, matching Experiment Set A (normal LAN)."""
        delays = nc_raw.get("delay_ms") or [0]
        losses = nc_raw.get("loss_percent") or [0.0]
        bandwidths = nc_raw.get("bandwidth_mbps") or [0.0]

        return [
            NetworkCondition(delay_ms=d, loss_percent=l, bandwidth_mbps=b)
            for d, l, b in itertools.product(delays, losses, bandwidths)
        ]

    def validate(self) -> None:
        errors: List[str] = []

        if not self.protocols:
            errors.append("experiments.protocols must not be empty")
        for p in self.protocols:
            if p not in ("TCP", "UDP"):
                errors.append(f"Unknown protocol '{p}' (expected TCP or UDP)")

        if not self.packet_sizes:
            errors.append("experiments.packet_sizes must not be empty")
        for s in self.packet_sizes:
            if s <= 0:
                errors.append(f"Invalid packet size: {s}")
            if s > 8192:
                errors.append(f"Packet size {s} exceeds MAX_PAYLOAD_SIZE (8192, see common/protocol.h)")

        if not self.packet_counts:
            errors.append("experiments.packet_counts must not be empty")
        for c in self.packet_counts:
            if c <= 0:
                errors.append(f"Invalid packet count: {c}")

        if not self.duration_seconds:
            errors.append("experiments.duration_seconds must not be empty")
        for d in self.duration_seconds:
            if d <= 0:
                errors.append(f"Invalid duration_seconds: {d}")

        if self.repetitions < 1:
            errors.append("experiments.repetitions must be >= 1")

        if not self.output.csv_schema:
            errors.append("output.csv_schema must not be empty")

        if errors:
            raise ValueError("Invalid experiment configuration:\n  - " + "\n  - ".join(errors))

    # ------------------------------------------------------------
    # Sweep generation
    # ------------------------------------------------------------
    def iter_conditions(self) -> Iterator[ExperimentCondition]:
        """Yield every experiment condition the runner must execute,
        in deterministic order so a run is reproducible."""
        for protocol, packet_size, packet_count, duration, nc in itertools.product(
            self.protocols,
            self.packet_sizes,
            self.packet_counts,
            self.duration_seconds,
            self.network_conditions,
        ):
            for rep in range(1, self.repetitions + 1):
                yield ExperimentCondition(
                    protocol=protocol,
                    packet_size=packet_size,
                    packet_count=packet_count,
                    duration_seconds=duration,
                    repetition=rep,
                    network_condition=nc,
                )

    def total_runs(self) -> int:
        return (
            len(self.protocols)
            * len(self.packet_sizes)
            * len(self.packet_counts)
            * len(self.duration_seconds)
            * len(self.network_conditions)
            * self.repetitions
        )


if __name__ == "__main__":
    cfg = ExperimentConfig.from_yaml("config/experiments.yaml")
    print(f"Loaded config: {cfg.total_runs()} total experiment runs.\n")
    for i, cond in enumerate(cfg.iter_conditions()):
        print(cond.experiment_id)
        if i >= 9:
            print("...")
            break

"""NS-3 adapter. Native macOS/Linux, or a selected Windows WSL distribution."""
from __future__ import annotations

import os
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
from experiments.topology import resolve, simulator_text

ROOT = Path(__file__).resolve().parents[1]


class Ns3Backend:
    def __init__(self, distro=None):
        self.windows = platform.system() == "Windows"
        self.distro = distro or os.environ.get("NS3_WSL_DISTRO", "Ubuntu-22.04")

    def path(self, path):
        value = str(Path(path).resolve())
        if self.windows:
            return "/mnt/" + value[0].lower() + value[2:].replace("\\", "/")
        return value

    def execute(self, args, timeout=180):
        if self.windows:
            args = ["wsl", "-d", self.distro, "--", *args]
        environment=os.environ.copy()
        if not self.windows and environment.get("NS3_PREFIX"):
            prefix=Path(environment["NS3_PREFIX"]).expanduser()
            directories=[prefix/"lib/pkgconfig",prefix/"lib64/pkgconfig"]
            environment["PKG_CONFIG_PATH"]=os.pathsep.join([*(str(p) for p in directories),environment.get("PKG_CONFIG_PATH","")])
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout,env=environment)
        if result.returncode:
            raise RuntimeError(f"Command failed ({result.returncode}): {args}\n{result.stdout}\n{result.stderr}")
        return result.stdout.strip()

    @property
    def binary(self):
        return ROOT / "build" / "transport-lab"

    def build(self, netanim=False):
        self.execute(["cmake", "-S", self.path(ROOT / "simulation"), "-B", self.path(ROOT / "build"),
                      "-DTRANSPORT_ENABLE_NETANIM="+("ON" if netanim else "OFF")])
        self.execute(["cmake", "--build", self.path(ROOT / "build"), "--parallel", "2"])
        (self.binary.parent/"build.json").write_text(json.dumps(dict(
            source_sha256=hashlib.sha256((ROOT/"simulation/tcp_udp.cc").read_bytes()).hexdigest(),
            binary_sha256=hashlib.sha256(self.binary.read_bytes()).hexdigest(), ns3_version=self.version())))

    def version(self):
        available = self.execute(["pkg-config", "--list-all"])
        match = re.search(r"^(?:lib)?ns3[a-zA-Z0-9_.-]*-core\b", available, re.MULTILINE)
        if not match:
            raise RuntimeError("NS-3 development libraries not found. See docs/ns3-setup.md")
        return self.execute(["pkg-config", "--modversion", match.group()])

    def run(self, settings, prefix):
        if not self.binary.is_file():
            raise RuntimeError("Simulator is not built. Run: python scripts/build_ns3.py")
        metadata = self.binary.parent/"build.json"
        if not metadata.is_file():
            raise RuntimeError("Build metadata missing. Run: python scripts/build_ns3.py")
        built = json.loads(metadata.read_text())
        capabilities=self.binary.parent/"capabilities.json"
        if settings.get("netanim") and (not capabilities.exists() or not json.loads(capabilities.read_text()).get("netanim")):
            raise RuntimeError("NS-3 netanim module was not found at build time. Disable NetAnim XML to use built-in packet playback, or install that module and rebuild.")
        if built["source_sha256"] != hashlib.sha256((ROOT/"simulation/tcp_udp.cc").read_bytes()).hexdigest():
            raise RuntimeError("Simulator source changed. Rebuild with: python scripts/build_ns3.py")
        if built["binary_sha256"] != hashlib.sha256(self.binary.read_bytes()).hexdigest():
            raise RuntimeError("Simulator binary changed. Rebuild with: python scripts/build_ns3.py")
        topology = resolve(settings.get("topology"),settings)
        Path(str(prefix)+"-topology.json").write_text(json.dumps(topology,indent=2),encoding="utf-8")
        topology_file=Path(str(prefix)+"-topology.txt")
        topology_file.write_text(simulator_text(topology))
        args = [self.path(self.binary)]
        args += [f"--{key}={value}" for key, value in settings.items() if key not in ("topology","topology_id")]
        args.append("--topology="+self.path(topology_file))
        args.append("--output=" + self.path(prefix))
        return self.execute(args)

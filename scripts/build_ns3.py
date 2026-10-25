"""Build the simulator against distribution-provided NS-3 libraries."""
import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.ns3_backend import Ns3Backend

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netanim",action="store_true",help="Opt into linking the optional NS-3 NetAnim XML exporter")
    args=parser.parse_args()
    try:
        backend = Ns3Backend()
        backend.build(netanim=args.netanim)
        print(f"Built {backend.binary} against NS-3 {backend.version()}")
    except (RuntimeError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        print("See docs/mac-quickstart.md or docs/ns3-setup.md for prerequisites.", file=sys.stderr)
        sys.exit(1)

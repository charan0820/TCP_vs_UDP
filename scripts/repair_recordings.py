"""Regenerate missing legacy captures; identical configurations run only once."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import yaml
from dashboard.archive import batches,availability,prefix_for,rerun_configuration,regenerated_for
from experiments.ns3_backend import ROOT
from experiments.experiment_runner import run_suite


def plan(found):
    grouped={}
    for batch in found:
        if batch["manifest"].get("status")!="complete" or regenerated_for(found,batch):continue
        if not any(availability(prefix_for(batch,row))!="ready" for row in batch["rows"]):continue
        config=rerun_configuration(batch)
        config.pop("replay_of_batches",None)
        signature=json.dumps(config,sort_keys=True)
        group=grouped.setdefault(signature,dict(config=config,sources=[]))
        group["sources"].append(batch["folder"].name)
    return list(grouped.values())


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run",action="store_true",help="Run NS-3; otherwise only print the repair plan")
    args=parser.parse_args()
    groups=plan(batches(ROOT/"data/runs"))
    print(f"{len(groups)} unique configurations need new recordings.",flush=True)
    for group in groups:
        print("Saved batches: "+", ".join(group["sources"]),flush=True)
        if not args.run:continue
        group["config"]["replay_of_batches"]=group["sources"]
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"capture.yaml";path.write_text(yaml.safe_dump(group["config"]))
            destination=run_suite(path)
        print("Recorded: "+str(destination),flush=True)

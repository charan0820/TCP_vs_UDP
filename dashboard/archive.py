"""One source for archive discovery, recording availability and playback recovery."""
import csv
import json
from pathlib import Path
from experiments.topology import normalize, resolve
from visualization.packets import packet_spans, playback_html


def batches(root):
    found=[]
    for folder in sorted(Path(root).glob("*"),reverse=True):
        if not folder.is_dir() or not (folder/"manifest.json").exists(): continue
        try:
            manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
            rows=json.loads((folder/"results.json").read_text(encoding="utf-8")) if (folder/"results.json").exists() else []
            if not isinstance(rows,list) or not isinstance(manifest,dict): raise ValueError("Invalid archive format")
            found.append(dict(folder=folder,manifest=manifest,rows=rows,error=None))
        except (OSError,ValueError) as exc:
            found.append(dict(folder=folder,manifest={},rows=[],error=str(exc)))
    return found


def prefix_for(batch,row):
    # IDs retain the actual simulator run number even when a table is filtered.
    identifier=str(row.get("experiment_id",""))
    tail=identifier.rsplit("-",1)[-1]
    index=int(tail) if tail.isdigit() else batch["rows"].index(row)+1
    return batch["folder"]/f"run-{index:04d}"


def availability(prefix):
    path=Path(str(prefix)+"-packets.csv")
    if not path.exists(): return "missing"
    try:
        with path.open(newline="") as f:
            reader=csv.DictReader(f)
            if not {"event","uid","source","target","link","time_s"}.issubset(reader.fieldnames or []): return "invalid"
            return "ready" if next(reader,None) else "empty"
    except (OSError,csv.Error): return "invalid"


def topology_for(batch,row):
    path=Path(str(prefix_for(batch,row))+"-topology.json")
    if path.exists(): return json.loads(path.read_text(encoding="utf-8"))
    return resolve(batch["manifest"].get("configuration",{}).get("topology"),row)


def recording(batch,row,autoplay=False):
    """Render from raw events with today's player; cached old HTML is not required."""
    prefix=prefix_for(batch,row)
    status=availability(prefix)
    if status!="ready": return None,status
    try:
        spans,total=packet_spans(Path(str(prefix)+"-packets.csv"))
        if not spans: return None,"empty"
        return playback_html(topology_for(batch,row),spans,total,bool(row.get("packet_trace_truncated",False)),autoplay=autoplay),"ready"
    except (OSError,ValueError,KeyError,csv.Error): return None,"invalid"


def latest_matching(found,topology):
    for batch in found:
        for row in batch["rows"]:
            if availability(prefix_for(batch,row))!="ready": continue
            try:
                if normalize(topology_for(batch,row))==normalize(resolve(topology,row)):
                    return batch,row
            except (ValueError,KeyError,OSError): continue
    return None


def rerun_configuration(batch):
    """Regenerate a new provenance-preserving batch; never invent old device events."""
    config=json.loads(json.dumps(batch["manifest"]["configuration"]))
    config["packet_trace_limit"]=max(50000,config.get("packet_trace_limit",0))
    config["netanim"]=False
    config["replay_of_batches"]=[batch["folder"].name]
    return config


def regenerated_for(found,batch):
    return next((item for item in found if item["manifest"].get("status")=="complete" and
                 batch["folder"].name in item["manifest"].get("replay_of_batches",[])),None)

"""Offline, self-contained packet playback from measured NS-3 device events."""
import csv
import json
from collections import defaultdict, deque
from pathlib import Path


def packet_spans(path, limit=3000):
    """Pair transmissions with successful receives or receive drops per link/direction.

    Queue drops have no transmission. Missing outcomes stay unknown, never received.
    A packet UID is not a TCP sequence number and can repeat on different links.
    """
    spans=[]; pending=defaultdict(deque); total=0
    with Path(path).open(newline="") as f:
        for row in csv.DictReader(f):
            key=tuple(row[k] for k in ("link","source","target","uid"))
            if row["event"]=="tx":
                total+=1
                if len(spans)>=limit: continue
                span=dict(start=float(row["time_s"]),end=None,status="unobserved",source=int(row["source"]),
                    target=int(row["target"]),link=int(row["link"]),uid=row["uid"],bytes=int(row["bytes"]),
                    protocol=row["protocol"],detail=row["detail"],sequence=row["sequence"],ack=row["ack"])
                spans.append(span); pending[key].append(span)
            elif row["event"] in ("rx","rx_drop") and pending[key]:
                span=pending[key].popleft()
                span.update(end=float(row["time_s"]),status="received" if row["event"]=="rx" else "dropped")
            elif row["event"]=="queue_drop" and len(spans)<limit:
                spans.append(dict(start=float(row["time_s"]),end=float(row["time_s"]),status="queue_drop",
                    source=int(row["source"]),target=int(row["target"]),link=int(row["link"]),uid=row["uid"],
                    bytes=int(row["bytes"]),protocol=row["protocol"],detail=row["detail"],sequence=row["sequence"],ack=row["ack"]))
    return spans,total


def playback_html(topology, spans=None, total=0, truncated=False,autoplay=False):
    payload=json.dumps(dict(topology=topology,packets=spans or [],total=total,truncated=truncated,autoplay=autoplay),allow_nan=False)
    # User-authored labels are data, never executable HTML/script.
    payload=payload.replace("<","\\u003c").replace("\u2028","\\u2028").replace("\u2029","\\u2029")
    template=Path(__file__).with_name("packet_player.html").read_text(encoding="utf-8")
    return template.replace("/*PAYLOAD*/",payload)

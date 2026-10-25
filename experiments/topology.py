"""Validated topology contract shared by the editor, runner and NS-3 adapter."""
import hashlib
import json
import math


def preset(name="Direct link"):
    layouts = {
        "Direct link": ([(0,50),(100,50)], [(0,1)]),
        "Routed bottleneck": ([(0,50),(33,50),(66,50),(100,50)], [(0,1),(1,2),(2,3)]),
        "Star": ([(0,0),(50,50),(100,0),(100,100),(0,100)], [(0,1),(1,2),(1,3),(1,4)]),
        "Diamond": ([(0,50),(50,0),(50,100),(100,50)], [(0,1),(0,2),(1,3),(2,3)]),
    }
    positions, edges = layouts[name]
    receiver = 2 if name=="Star" else len(positions)-1
    return dict(nodes=[dict(id=i,label="Sender" if i==0 else "Receiver" if i==receiver else f"Router {i}",x=x,y=y)
                       for i,(x,y) in enumerate(positions)],
                links=[dict(source=a,target=b) for a,b in edges], sender=0, receiver=receiver)


def number(value, label, minimum=0, maximum=1_000_000):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{label} must be a finite number between {minimum} and {maximum}")
    return value


def normalize(raw):
    """Reject ambiguous/disconnected graphs; IDs are contiguous for NS-3 nodes."""
    if not isinstance(raw,dict): raise ValueError("Topology must be an object")
    nodes, links = raw.get("nodes"), raw.get("links")
    if not isinstance(nodes,list) or not 2 <= len(nodes) <= 32:
        raise ValueError("Topology needs 2–32 nodes")
    if not isinstance(links,list) or not 1 <= len(links) <= 64:
        raise ValueError("Topology needs 1–64 links")
    result_nodes=[]
    for node in nodes:
        if not isinstance(node,dict) or type(node.get("id")) is not int:
            raise ValueError("Each node needs an integer ID")
        label=node.get("label",f"Node {node['id']}")
        if not isinstance(label,str) or not 1<=len(label)<=48:
            raise ValueError("Node labels must have 1–48 characters")
        result_nodes.append(dict(id=node["id"],label=label,
            x=number(node.get("x",0),"Node x",-10000,10000), y=number(node.get("y",0),"Node y",-10000,10000)))
    ids={n["id"] for n in result_nodes}
    if len(ids)!=len(nodes) or ids!=set(range(len(nodes))):
        raise ValueError("Node IDs must be unique and consecutive: 0, 1, 2, …")
    sender, receiver=raw.get("sender",0),raw.get("receiver",len(nodes)-1)
    if type(sender) is not int or type(receiver) is not int or sender not in ids or receiver not in ids or sender==receiver:
        raise ValueError("Choose distinct existing sender and receiver IDs")
    seen=set(); neighbors={i:set() for i in ids}; result_links=[]
    for link in links:
        if not isinstance(link,dict): raise ValueError("Each link must be an object")
        a,b=link.get("source"),link.get("target")
        if type(a) is not int or type(b) is not int or a not in ids or b not in ids or a==b:
            raise ValueError("Links must connect two distinct existing integer node IDs")
        edge=tuple(sorted((a,b)))
        if edge in seen: raise ValueError("Duplicate links are not supported")
        seen.add(edge); neighbors[a].add(b); neighbors[b].add(a)
        cleaned=dict(source=a,target=b)
        for key,low,high in [("bandwidth_mbps",.001,10000),("delay_ms",0,10000),("loss_percent",0,99.999),("queue_packets",1,100000)]:
            if key in link:
                cleaned[key]=number(link[key],key,low,high)
                if key=="queue_packets" and type(link[key]) is not int:
                    raise ValueError("queue_packets must be an integer")
        result_links.append(cleaned)
    visited={sender}; pending=[sender]
    while pending:
        for neighbor in neighbors[pending.pop()]-visited:
            visited.add(neighbor); pending.append(neighbor)
    if visited!=ids: raise ValueError("All nodes must be connected; remove isolated nodes or add links")
    return dict(nodes=sorted(result_nodes,key=lambda n:n["id"]),links=result_links,sender=sender,receiver=receiver)


def resolve(raw, settings):
    topology=normalize(raw if raw is not None else preset())
    for index,link in enumerate(topology["links"]):
        link["id"]=index
        link.setdefault("bandwidth_mbps",settings["bandwidth"])
        link.setdefault("delay_ms",settings["delay"])
        link.setdefault("queue_packets",settings["queue"])
        base=link.get("loss_percent",0)
        # Independent base and condition error probabilities, not arithmetic sum.
        link["loss_percent"]=100*(1-(1-base/100)*(1-settings["loss"]/100))
    return topology


def fingerprint(topology):
    return hashlib.sha256(json.dumps(topology,sort_keys=True,separators=(",",":")).encode()).hexdigest()[:16]


def simulator_text(topology):
    lines=[f"{len(topology['nodes'])} {len(topology['links'])} {topology['sender']} {topology['receiver']}"]
    lines += [f"{n['x']} {n['y']}" for n in topology["nodes"]]
    lines += [f"{e['source']} {e['target']} {e['bandwidth_mbps']} {e['delay_ms']} {e['loss_percent']} {e['queue_packets']}" for e in topology["links"]]
    return "\n".join(lines)+"\n"

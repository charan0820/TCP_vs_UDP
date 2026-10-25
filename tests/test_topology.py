import copy
import csv
import json
from pathlib import Path
import pytest
from experiments.topology import preset,normalize,resolve,fingerprint,simulator_text
from visualization.packets import packet_spans,playback_html


@pytest.mark.parametrize("name",["Direct link","Routed bottleneck","Star","Diamond"])
def test_presets(name):
    topology=normalize(preset(name))
    assert topology["sender"]!=topology["receiver"]
    assert len(topology["nodes"])>=2


@pytest.mark.parametrize("change",["isolated","duplicate","self","missing","bad_id","bad_rate","fractional_queue","same_endpoint"])
def test_invalid_graphs(change):
    t=preset("Routed bottleneck")
    if change=="isolated":t["links"].pop()
    if change=="duplicate":t["links"].append(dict(t["links"][0]))
    if change=="self":t["links"][0]["target"]=0
    if change=="missing":t["links"][0]["target"]=12
    if change=="bad_id":t["nodes"][0]["id"]=8
    if change=="bad_rate":t["links"][0]["bandwidth_mbps"]=-1
    if change=="fractional_queue":t["links"][0]["queue_packets"]=1.5
    if change=="same_endpoint":t["receiver"]=t["sender"]
    with pytest.raises(ValueError):normalize(t)


def test_resolved_settings_and_topology_identity():
    t=preset();t["links"][0].update(loss_percent=10,bandwidth_mbps=2)
    resolved=resolve(t,dict(bandwidth=100,delay=5,queue=30,loss=20))
    assert resolved["links"][0]["loss_percent"]==pytest.approx(28)
    assert resolved["links"][0]["bandwidth_mbps"]==2
    assert resolved["links"][0]["delay_ms"]==5
    assert fingerprint(resolved)==fingerprint(copy.deepcopy(resolved))
    assert simulator_text(resolved).splitlines()[0]=="2 1 0 1"


def test_packet_pairing_never_invents_delivery(tmp_path):
    path=tmp_path/"packets.csv"
    path.write_text("time_s,event,link,source,target,uid,bytes,protocol,detail,sequence,ack\n"
        "1,tx,0,0,1,12,100,TCP,DATA,1,0\n"
        "1.1,rx,0,0,1,12,100,TCP,DATA,1,0\n"
        "1.1,tx,1,1,2,12,100,TCP,DATA,1,0\n"
        "1.2,rx_drop,1,1,2,12,100,TCP,DATA,1,0\n"
        "2,tx,0,0,1,13,100,TCP,DATA,1,0\n"
        "2.1,queue_drop,1,1,2,14,100,TCP,DATA,1,0\n")
    spans,total=packet_spans(path)
    assert total==3
    assert [p["status"] for p in spans]==["received","dropped","unobserved","queue_drop"]
    assert spans[2]["end"] is None
    assert packet_spans(path,limit=1)[0][0]["end"]==1.1


def test_player_escapes_labels():
    t=preset();t["nodes"][0]["label"]="</script><script>alert(1)</script>"
    html=playback_html(t)
    assert "</script><script>alert" not in html
    assert "\\u003c/script>" in html
    assert "/*PAYLOAD*/" not in html

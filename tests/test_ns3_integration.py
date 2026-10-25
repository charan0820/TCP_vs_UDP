"""Opt-in real simulator checks: set RUN_NS3_TESTS=1 after building."""
import json
import os
from pathlib import Path
import pytest
import csv
import xml.etree.ElementTree as ET
from experiments.ns3_backend import Ns3Backend
from metrics.collector import collect
from experiments.topology import preset
from visualization.packets import packet_spans

pytestmark=pytest.mark.skipif(os.environ.get("RUN_NS3_TESTS")!="1",reason="Opt-in real NS-3/WSL integration")


@pytest.mark.parametrize("protocol,size",[("TCP",64),("TCP",8192),("UDP",64),("UDP",8192)])
def test_clean_delivery(tmp_path, protocol, size):
    s=dict(protocol=protocol,size=size,count=20,duration=2,drain=2,rate=1,bandwidth=100,
           delay=1,loss=0,queue=100,seed=42,run=1,tcp="TcpNewReno",pcap=0)
    prefix=tmp_path/f"{protocol}-{size}"
    backend=Ns3Backend(); backend.run(s,prefix)
    result=collect(prefix,s)
    assert result["messages_sent"]==result["messages_received"]==20
    assert result["bytes_received"]==20*size
    assert result["packet_loss_percent"]==0
    assert result["avg_latency_ms"]>=1
    if protocol=="TCP": assert result["retransmissions"]==0


def test_loss_recovery_repeatability_and_pcap(tmp_path):
    s=dict(protocol="TCP",size=1024,count=400,duration=2,drain=5,rate=5,bandwidth=10,
           delay=10,loss=2,queue=100,seed=42,run=1,tcp="TcpNewReno",pcap=1)
    backend=Ns3Backend()
    first=tmp_path/"first"; second=tmp_path/"second"
    backend.run(s,first); backend.run(s,second)
    assert Path(str(first)+"-events.csv").read_bytes()==Path(str(second)+"-events.csv").read_bytes()
    result=collect(first,s)
    assert result["retransmissions"]>0
    assert result["messages_received"]==result["messages_sent"]
    assert list(tmp_path.glob("*.pcap"))


@pytest.mark.parametrize("name",["Routed bottleneck","Star","Diamond"])
def test_routed_delivery_and_actual_hops(tmp_path,name):
    t=preset(name)
    s=dict(protocol="TCP",size=128,count=10,duration=2,drain=2,rate=1,bandwidth=100,
           delay=2,loss=0,queue=100,seed=42,run=1,tcp="TcpNewReno",pcap=0,topology=t)
    prefix=tmp_path/"routed"
    Ns3Backend().run(s,prefix)
    result=collect(prefix,s)
    assert result["messages_received"]==10
    with Path(str(prefix)+"-packets.csv").open() as f:events=list(csv.DictReader(f))
    assert any(e["detail"]=="SYN" for e in events)
    assert any(e["detail"]=="ACK" for e in events)
    assert all(e["protocol"]=="TCP" for e in events)
    first_uid=next(e["uid"] for e in events if e["detail"]=="SYN")
    hops=[e for e in events if e["event"]=="tx" and e["uid"]==first_uid]
    assert len(hops)==(3 if name=="Routed bottleneck" else 2)
    assert hops[0]["source"]==str(t["sender"])
    assert hops[-1]["target"]==str(t["receiver"])


def test_netanim_and_measured_drops(tmp_path):
    backend=Ns3Backend()
    capabilities=json.loads((backend.binary.parent/"capabilities.json").read_text())
    s=dict(protocol="UDP",size=1024,count=300,duration=1,drain=2,rate=20,bandwidth=1,
           delay=5,loss=10,queue=2,seed=42,run=1,tcp="TcpNewReno",pcap=0,
           netanim=int(capabilities["netanim"]),topology=preset("Routed bottleneck"))
    prefix=tmp_path/"drops";backend.run(s,prefix)
    spans,total=packet_spans(Path(str(prefix)+"-packets.csv"))
    assert any(p["status"]=="queue_drop" for p in spans)
    assert any(p["status"]=="dropped" for p in spans)
    assert any(p["status"]=="received" for p in spans)
    if capabilities["netanim"]:
        root=ET.parse(Path(str(prefix)+"-animation.xml")).getroot()
        assert root.tag=="anim"
        assert len(root.findall("node"))==4


def test_capture_limit_marks_incomplete_recording(tmp_path):
    s=dict(protocol="TCP",size=64,count=20,duration=2,drain=2,rate=1,bandwidth=100,
           delay=1,loss=0,queue=100,seed=42,run=1,tcp="TcpNewReno",pcap=0,packetTraceLimit=1)
    prefix=tmp_path/"limited";Ns3Backend().run(s,prefix)
    summary=json.loads(Path(str(prefix)+"-summary.json").read_text())
    assert summary["packet_trace_truncated"] and summary["packet_trace_rows"]==1
    assert summary["messages_received"]==20
    spans,_=packet_spans(Path(str(prefix)+"-packets.csv"))
    assert spans[0]["status"]=="unobserved" and spans[0]["end"] is None


def test_manual_link_delay_changes_simulation(tmp_path):
    backend=Ns3Backend(); results=[]
    for delay in (1,21):
        topology=preset();topology["links"][0]["delay_ms"]=delay
        s=dict(protocol="UDP",size=128,count=10,duration=2,drain=2,rate=.1,bandwidth=100,
               delay=0,loss=0,queue=100,seed=42,run=1,tcp="TcpNewReno",pcap=0,topology=topology)
        prefix=tmp_path/f"delay-{delay}";backend.run(s,prefix)
        row=collect(prefix,s)
        assert row["messages_received"]==10
        results.append(row["avg_latency_ms"])
    assert results[1]-results[0]==pytest.approx(20,abs=.001)

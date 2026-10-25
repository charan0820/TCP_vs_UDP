"""Transport Lab: a simulation workspace and measured-signal archive."""
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yaml
from experiments.ns3_backend import ROOT
from experiments.experiment_runner import run_suite
from experiments.topology import resolve
from dashboard.topology_editor import editor
from dashboard.archive import batches,latest_matching,prefix_for,availability,rerun_configuration,regenerated_for
from dashboard.run_view import render,run_label
from dashboard.theme import apply,landing,navigate
from visualization.packets import playback_html

st.set_page_config(page_title="Transport Lab / Packet Core",page_icon=None,layout="wide",initial_sidebar_state="collapsed")
apply()
found=batches(ROOT/"data/runs")
st.markdown('<div class="masthead"><div class="wordmark"><span>TL</span> / TRANSPORT LAB</div><div class="masthead-status">NS-3 NETWORK EXPERIMENTS<br><b>LOCAL WORKSPACE</b></div></div>',unsafe_allow_html=True)
routes={"home":"Overview","lab":"Simulation lab","archive":"Archive","guide":"Guide"}
if "navigation" not in st.session_state: st.session_state.navigation=routes.get(st.query_params.get("view","home"),"Overview")
def route_changed():
    st.query_params["view"]={v:k for k,v in routes.items()}[st.session_state.navigation]
view=st.radio("Workspace navigation",list(routes.values()),horizontal=True,label_visibility="collapsed",key="navigation",on_change=route_changed)


def execute(config):
    progress=st.progress(0,text="Preparing NS-3 simulation")
    try:
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"experiment.yaml";path.write_text(yaml.safe_dump(config))
            result=run_suite(path,progress=lambda i,n,r:progress.progress(i/n,text=f"Recorded {i}/{n}: {r['protocol']} / {r['condition']}"))
        st.session_state.active_batch=str(result)
        st.session_state.autoplay=True
        st.success("Simulation complete. The packet replay and measurements below come from this run.")
        return batches(ROOT/"data/runs")
    except Exception as exc:
        st.error(f"Simulation did not complete: {exc}")
        st.info("Check that NS-3 is built with `python scripts/build_ns3.py`. Open Guide for Mac/WSL setup. Completed measurements are preserved in the archive.")
        return batches(ROOT/"data/runs")


def lab(found):
    st.title("Simulation lab")
    st.write("Shape the network, run NS-3, then follow the recorded packets through the same topology.")
    controls,stage=st.columns([.9,1.4],gap="large")
    saved=st.session_state.setdefault("traffic_draft",{})
    with controls:
        topology=editor(10.,10.)
        with st.expander("Traffic and measurement",expanded=False):
            protocols=st.multiselect("Protocols",["TCP","UDP"],default=saved.get("protocols",["TCP"]),key="protocols")
            a,b=st.columns(2)
            sizes=[64,128,256,512,1024,4096,8192]
            size=a.selectbox("Payload / bytes",sizes,index=sizes.index(saved.get("size",1024)),key="traffic-size")
            count=b.number_input("Message limit",1,100000,saved.get("count",400),key="traffic-count")
            rate=st.number_input("Offered rate / Mbps",.1,1000.,saved.get("rate",5.),key="traffic-rate")
            a,b=st.columns(2)
            duration=a.number_input("Generation / seconds",1,60,saved.get("duration",3),key="traffic-duration")
            drain=b.number_input("Drain / seconds",1,30,saved.get("drain",5),key="traffic-drain")
            reps=st.number_input("Repetitions per condition",1,20,saved.get("reps",1),key="traffic-reps")
            compare=st.checkbox("Compare baseline with added loss",value=saved.get("compare",True),key="traffic-compare")
            loss=st.number_input("Added loss on every link / %",0.,50.,saved.get("loss",2.),disabled=not compare,key="traffic-loss")
        with st.expander("Capture and TCP options"):
            algorithm=st.selectbox("Congestion control",["TcpNewReno","TcpCubic"],index=["TcpNewReno","TcpCubic"].index(saved.get("algorithm","TcpNewReno")),key="traffic-algorithm")
            capture=st.checkbox("Save Wireshark PCAP",value=saved.get("capture",False),key="traffic-pcap")
            packet_limit=st.number_input("Packet event limit",1000,1000000,saved.get("packet_limit",50000),step=1000,key="traffic-limit")
            capabilities=ROOT/"build/capabilities.json"
            supported=capabilities.exists() and json.loads(capabilities.read_text()).get("netanim",False)
            netanim=st.checkbox("Export NetAnim XML",disabled=not supported,help="Optional. Built-in replay does not need NetAnim.")
        saved.update(protocols=protocols,size=size,count=count,rate=rate,duration=duration,drain=drain,reps=reps,compare=compare,loss=loss,algorithm=algorithm,capture=capture,packet_limit=packet_limit)
        config=dict(experiments=dict(protocols=protocols,packet_sizes=[size],packet_counts=[count],duration_seconds=[duration],rates_mbps=[rate],repetitions=reps),
            conditions=[dict(name="baseline",delay_ms=10,loss_percent=0,bandwidth_mbps=10)],
            drain_seconds=drain,queue_packets=100,seed=42,tcp_algorithm=algorithm,pcap=capture,
            topology=topology,netanim=netanim,packet_trace_limit=packet_limit)
        if compare:config["conditions"].append(dict(name="added loss",delay_ms=10,loss_percent=loss,bandwidth_mbps=10))
        st.caption(f"{' + '.join(protocols) or 'No protocol'} · {count:,} messages · {size} B · {rate:g} Mbps · {reps} repetition(s)")
        if st.button("Run simulation",type="primary",use_container_width=True,disabled=topology is None or not protocols): found=execute(config)
        st.caption("This runs NS-3 and records new events. Play controls become available after a recording exists.")
        if topology:
            with st.expander("Export this experiment"):
                st.download_button("Save experiment YAML",yaml.safe_dump(config),"experiment.yaml","text/yaml")
                st.download_button("Save topology JSON",json.dumps(topology,indent=2),"topology.json","application/json")
    with stage:
        st.subheader("The signal path")
        match=latest_matching(found,topology) if topology else None
        if match:
            batch,_=match
            matching=[row for row in batch["rows"] if availability(prefix_for(batch,row))=="ready"]
            row=st.selectbox("Recorded run",matching,format_func=run_label,key="lab-run-"+batch["folder"].name)
            st.caption("Latest recording of this topology. Rerun to apply changed traffic settings.")
            render(batch,row,autoplay=st.session_state.pop("autoplay",False),key="lab")
        elif topology:
            st.markdown('<div class="archive-note">Topology ready. Click <strong>Run simulation</strong> to send packets and create a replay.</div>',unsafe_allow_html=True)
            components.html(playback_html(resolve(topology,dict(bandwidth=10,delay=10,loss=0,queue=100))),height=340,scrolling=True)
            st.caption("Layout preview only. No packets have been simulated for this draft.")
        else: st.info("Complete a valid topology to see its signal path.")


def archive(found):
    st.title("Measured archive")
    st.write("Replay captured signals, compare outcomes, or regenerate a legacy batch with packet recording enabled.")
    if not found:
        st.info("No local experiments yet. Enter the simulation lab to create your first recording.")
        st.button("Build a topology",on_click=navigate,args=("Simulation lab",));return
    def label(batch):
        m=batch["manifest"]
        ready=sum(availability(prefix_for(batch,r))=="ready" for r in batch["rows"])
        return f"{batch['folder'].name} · {m.get('status','unreadable')} · {len(batch['rows'])} runs / {ready} recordings"
    names=[str(batch["folder"]) for batch in found]
    lookup={str(batch["folder"]):batch for batch in found}
    if st.session_state.get("archive-batch") not in names:st.session_state["archive-batch"]=names[0]
    chosen=lookup[st.selectbox("Measured batch",names,format_func=lambda name:label(lookup[name]),key="archive-batch")]
    if chosen["error"]:
        st.error("This batch has unreadable metadata: "+chosen["error"]);return
    m=chosen["manifest"]
    st.caption(f"{m.get('timestamp','Unknown date')} · NS-3 {m.get('ns3_version','unknown')} · seed {m.get('configuration',{}).get('seed','unknown')}")
    if m.get("status")!="complete": st.warning(f"Batch status: {m.get('status','unknown')}. {m.get('error','Only completed runs are available.')}")
    if chosen["rows"]:
        row=st.selectbox("Recorded run",chosen["rows"],format_func=run_label,key="archive-run-"+chosen["folder"].name)
        status=render(chosen,row,key="archive")
        if status!="ready":
            st.caption("A rerun creates a new batch with the original configuration and capture enabled. It does not alter or invent the old recording.")
            successor=regenerated_for(found,chosen)
            if successor:
                st.info("A fresh recording already exists for these saved settings. It uses the current simulator code and keeps its own measurements.")
                def open_regenerated():st.session_state["archive-batch"]=str(successor["folder"])
                st.button("Open regenerated recording",type="primary",on_click=open_regenerated)
            elif st.button("Rerun batch with packet capture",type="primary"):
                refreshed=execute(rerun_configuration(chosen))
                fresh=next((b for b in refreshed if str(b["folder"])==st.session_state.get("active_batch")),None)
                if fresh and fresh["rows"]:render(fresh,fresh["rows"][0],autoplay=True,key="regenerated")
        with st.expander("Compare all runs in this batch"):
            frame=pd.DataFrame(chosen["rows"])
            metric=st.selectbox("Comparison metric",["throughput_mbps","avg_latency_ms","jitter_ms","packet_loss_percent","retransmissions"])
            keys=[k for k in ["protocol","condition","packet_size","packet_count","rate","delay","loss","bandwidth","duration","drain","queue","tcp","topology_id"] if k in frame]
            grouped=frame.groupby(keys,dropna=False)[metric].agg(mean="mean",median="median",std=lambda x:x.std(ddof=0),n="count").reset_index()
            grouped["Experiment"]=grouped.apply(lambda r:f"{r['protocol']} / {r['condition']} / {r['packet_size']} B / {r['rate']} Mbps",axis=1)
            if grouped["mean"].notna().any():st.bar_chart(grouped.set_index("Experiment")[["mean"]],color="#A78BFA")
            else:st.info("No measurements of this metric are available for these protocols.")
            st.dataframe(grouped.drop(columns="Experiment"),hide_index=True,width="stretch")
    else: st.info("No runs completed in this batch. Correct the failure above and run a new experiment in the lab.")
    with st.expander("Batch provenance and exports"):
        st.json(m)
        for name,mime in [("results.csv","text/csv"),("report.md","text/markdown")]:
            path=chosen["folder"]/name
            if path.exists():st.download_button("Download "+name,path.read_bytes(),name,mime)


if view=="Overview": landing(sum(b["manifest"].get("status")=="complete" for b in found))
elif view=="Simulation lab": lab(found)
elif view=="Archive": archive(found)
else:
    st.title("Inside the experiment")
    st.write("Python controls the run. C++ NS-3 models the network. The player replays device events recorded by that simulation.")
    setup,method=st.tabs(["Run on a Mac","How measurements work"])
    with setup:st.markdown((ROOT/"docs/mac-quickstart.md").read_text())
    with method:st.markdown((ROOT/"docs/methodology.md").read_text())
st.markdown('<footer class="footer"><span>TRANSPORT LAB / PACKET CORE</span><span>CONFIGURE · SIMULATE · RECORD · EXPLAIN</span></footer>',unsafe_allow_html=True)


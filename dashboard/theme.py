"""Reference-led visual shell. Fonts ship locally; no CDN requests at runtime."""
import base64
from functools import lru_cache
from pathlib import Path
import streamlit as st

ASSETS=Path(__file__).with_name("assets")


@lru_cache
def stylesheet():
    css=Path(__file__).with_name("theme.css").read_text(encoding="utf-8")
    for token,file in [("SORA_FONT","Sora.ttf"),("MONO_FONT","IBMPlexMono-Regular.ttf")]:
        css=css.replace(token,base64.b64encode((ASSETS/file).read_bytes()).decode())
    return css


def apply():
    st.markdown("<style>"+stylesheet()+"</style>",unsafe_allow_html=True)


def landing(completed):
    st.markdown('''<section class="hero" aria-labelledby="hero-title">
      <div class="signal-field" aria-hidden="true"><div class="signal-beam"></div></div>
      <div class="hero-meta"><span>NS-3 EXPERIMENT ENGINE<br><b>TCP / UDP</b></span><span>LOCAL WORKSPACE<br><b>RECORDED. REPRODUCIBLE.</b></span></div>
      <div class="hero-content"><div class="hero-state">READY TO TRANSMIT</div>
      <h1 id="hero-title">PACKET<br>CORE</h1>
      <p>Build a network. Follow the signal.<br>See what reliability costs.</p></div>
      <div class="hero-foot"><span>TRANSPORT LAB / NETWORK SYSTEMS</span><span>SCROLL TO EXPLORE</span></div>
    </section>''',unsafe_allow_html=True)
    a,b,c=st.columns([1,1,1])
    b.button("Enter simulation lab",type="primary",use_container_width=True,key="enter-lab",on_click=navigate,args=("Simulation lab",))
    st.markdown('''<div class="feature-layout">
      <article class="feature feature-network"><h2>Your network.<br>Your conditions.</h2><p>Connect nodes, set a bottleneck and introduce loss. Run the topology through real NS-3 transport models.</p><div class="path-line" aria-hidden="true"><i></i><hr><i></i><hr><i></i><hr><i></i></div><small>DIRECT · ROUTED · STAR · DIAMOND · CUSTOM</small></article>
      <article class="feature feature-recording"><h2>Every hop<br>has a story.</h2><p>Replay data, acknowledgements and drops from captured device events. Pause at the moment the network changes.</p><small>PLAY / PAUSE / INSPECT / EXPORT</small></article>
      <article class="feature feature-measure"><div><h2>Go beyond “TCP is reliable.”</h2><p>Compare goodput, application delay, jitter and recovery across repeated experiments.</p></div><span class="evidence-label">CSV + JSON<br>RAW TRACES<br>MEASURED REPORTS</span></article>
    </div>''',unsafe_allow_html=True)
    st.subheader("From a topology to an explanation")
    st.write("Configure a graph, run a controlled experiment, then replay the same measured run while inspecting its results. One workspace keeps the network and its evidence together.")
    a,b=st.columns(2)
    a.button("Browse measured recordings",use_container_width=True,on_click=navigate,args=("Archive",))
    b.button("Read the Mac setup guide",use_container_width=True,on_click=navigate,args=("Guide",))
    st.caption(f"{completed} completed local batches available. Simulations run on this computer; no cloud account is needed.")


def navigate(view):
    st.session_state["navigation"]=view
    st.query_params["view"]={"Overview":"home","Simulation lab":"lab","Archive":"archive","Guide":"guide"}[view]

